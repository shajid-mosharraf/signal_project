"""DSP separation helpers for mixtures of two known voices.

This module is intentionally standalone and is not imported by the application.
The two clean voice recordings are used as spectral references for a soft
Wiener mask, so the functions can be called directly from a script or a
notebook without changing the frontend or API routes.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import numpy as np
from scipy import signal
import soundfile as sf


VoiceName = Literal["voice_one", "voice_two"]


def _as_mono(audio: np.ndarray) -> np.ndarray:
    """Return finite, mono, float32 audio without changing its level."""
    samples = np.asarray(audio, dtype=np.float32)
    if samples.ndim == 2:
        samples = samples.mean(axis=1) if samples.shape[1] <= 8 else samples.mean(axis=0)
    if samples.ndim != 1 or samples.size == 0:
        raise ValueError("Audio must be a non-empty one-dimensional or multichannel array.")
    if not np.isfinite(samples).all():
        raise ValueError("Audio contains NaN or infinite values.")
    return samples


def _resample(audio: np.ndarray, source_sr: int, target_sr: int) -> np.ndarray:
    if source_sr <= 0 or target_sr <= 0:
        raise ValueError("Sample rates must be positive integers.")
    if source_sr == target_sr:
        return audio
    divisor = np.gcd(source_sr, target_sr)
    return signal.resample_poly(audio, target_sr // divisor, source_sr // divisor).astype(np.float32)


def _reference_profile(audio: np.ndarray, sample_rate: int, n_fft: int, hop: int) -> np.ndarray:
    _, _, spectrum = signal.stft(
        audio,
        fs=sample_rate,
        window="hann",
        nperseg=n_fft,
        noverlap=n_fft - hop,
        nfft=n_fft,
        boundary="zeros",
    )
    power = np.abs(spectrum) ** 2
    power /= np.maximum(power.sum(axis=0, keepdims=True), 1e-12)
    profile = np.median(power, axis=1)
    profile /= max(float(profile.sum()), 1e-12)
    return profile


def _normalised_similarity(magnitude: np.ndarray, profile: np.ndarray) -> np.ndarray:
    frame_shape = np.maximum(magnitude.sum(axis=0), 1e-12)
    frame_profile = magnitude / frame_shape[None, :]
    profile_norm = profile / max(float(np.linalg.norm(profile)), 1e-12)
    frame_norm = np.maximum(np.linalg.norm(frame_profile, axis=0), 1e-12)
    return np.clip((profile_norm[:, None] * frame_profile).sum(axis=0) / frame_norm, 0.0, 1.0)


def separate_two_voices(
    mixture: np.ndarray,
    voice_one: np.ndarray,
    voice_two: np.ndarray,
    sample_rate: int = 16000,
    voice_one_sample_rate: int | None = None,
    voice_two_sample_rate: int | None = None,
    n_fft: int = 1024,
    hop_length: int = 256,
    mask_sharpness: float = 2.0,
) -> tuple[np.ndarray, np.ndarray]:
    """Separate a mixture using two clean voice recordings as references.

    Args:
        mixture: Mono or multichannel mixed recording to separate.
        voice_one: Clean recording containing the first speaker.
        voice_two: Clean recording containing the second speaker.
        sample_rate: Sample rate of ``mixture`` and the output arrays.
        voice_one_sample_rate: Rate of ``voice_one``; defaults to ``sample_rate``.
        voice_two_sample_rate: Rate of ``voice_two``; defaults to ``sample_rate``.
        n_fft: STFT window size. 1024 is suitable for speech at 16 kHz.
        hop_length: STFT advance in samples.
        mask_sharpness: Values above 1 make the soft masks more selective.

    Returns:
        ``(voice_one_estimate, voice_two_estimate)`` with the mixture length.

    This is a source-informed DSP estimate, not a neural speech separator. It
    works best when the reference recordings contain the same speakers and the
    mixture has limited background noise.
    """
    if n_fft < 32 or hop_length <= 0 or hop_length >= n_fft:
        raise ValueError("Require n_fft >= 32 and 0 < hop_length < n_fft.")
    if mask_sharpness <= 0:
        raise ValueError("mask_sharpness must be positive.")

    mixture_audio = _as_mono(mixture)
    first = _resample(_as_mono(voice_one), voice_one_sample_rate or sample_rate, sample_rate)
    second = _resample(_as_mono(voice_two), voice_two_sample_rate or sample_rate, sample_rate)

    frequencies, times, mixture_stft = signal.stft(
        mixture_audio,
        fs=sample_rate,
        window="hann",
        nperseg=n_fft,
        noverlap=n_fft - hop_length,
        nfft=n_fft,
        boundary="zeros",
    )
    del frequencies, times
    magnitude = np.abs(mixture_stft)
    first_profile = _reference_profile(first, sample_rate, n_fft, hop_length)
    second_profile = _reference_profile(second, sample_rate, n_fft, hop_length)

    first_similarity = _normalised_similarity(magnitude, first_profile)
    second_similarity = _normalised_similarity(magnitude, second_profile)
    first_activity = np.power(first_similarity + 1e-6, mask_sharpness)
    second_activity = np.power(second_similarity + 1e-6, mask_sharpness)

    first_power = first_profile[:, None] * first_activity[None, :]
    second_power = second_profile[:, None] * second_activity[None, :]
    denominator = first_power + second_power + 1e-12
    first_mask = first_power / denominator
    second_mask = second_power / denominator

    first_estimate = _istft_like(mixture_stft * first_mask, sample_rate, n_fft, hop_length, len(mixture_audio))
    second_estimate = _istft_like(mixture_stft * second_mask, sample_rate, n_fft, hop_length, len(mixture_audio))
    return first_estimate, second_estimate


def _istft_like(spectrum: np.ndarray, sample_rate: int, n_fft: int, hop_length: int, length: int) -> np.ndarray:
    _, audio = signal.istft(
        spectrum,
        fs=sample_rate,
        window="hann",
        nperseg=n_fft,
        noverlap=n_fft - hop_length,
        nfft=n_fft,
        input_onesided=True,
        boundary=True,
    )
    if len(audio) < length:
        audio = np.pad(audio, (0, length - len(audio)))
    return audio[:length].astype(np.float32)


def remove_mixer_voice(
    mixture: np.ndarray,
    voice_to_remove: np.ndarray,
    other_voice: np.ndarray,
    sample_rate: int = 16000,
    voice_to_remove_sample_rate: int | None = None,
    other_voice_sample_rate: int | None = None,
) -> np.ndarray:
    """Return the estimated mixture with one known voice removed."""
    removed, remaining = separate_two_voices(
        mixture,
        voice_to_remove,
        other_voice,
        sample_rate=sample_rate,
        voice_one_sample_rate=voice_to_remove_sample_rate,
        voice_two_sample_rate=other_voice_sample_rate,
    )
    del removed
    return remaining


def separate_two_voice_files(
    mixture_path: str | Path,
    voice_one_path: str | Path,
    voice_two_path: str | Path,
    output_one_path: str | Path,
    output_two_path: str | Path,
) -> None:
    """Separate WAV-compatible files and write the two estimates to disk."""
    mixture, sample_rate = sf.read(mixture_path, dtype="float32", always_2d=False)
    voice_one, first_rate = sf.read(voice_one_path, dtype="float32", always_2d=False)
    voice_two, second_rate = sf.read(voice_two_path, dtype="float32", always_2d=False)
    first, second = separate_two_voices(
        mixture,
        voice_one,
        voice_two,
        sample_rate=sample_rate,
        voice_one_sample_rate=first_rate,
        voice_two_sample_rate=second_rate,
    )
    sf.write(output_one_path, first, sample_rate)
    sf.write(output_two_path, second, sample_rate)


# ---------------------------------------------------------------------------
# Optional ML alternative (intentionally disabled; every line is commented).
# This uses scikit-learn NMF to learn two spectral components from the mixture,
# then uses the clean voice references to decide which component is each voice.
# To experiment with it, uncomment this whole block and add the function names
# to __all__ below. It is not imported or executed by the active project.
#
# from sklearn.decomposition import NMF
#
#
# def separate_two_voices_ml(
#     mixture: np.ndarray,
#     voice_one: np.ndarray,
#     voice_two: np.ndarray,
#     sample_rate: int = 16000,
#     voice_one_sample_rate: int | None = None,
#     voice_two_sample_rate: int | None = None,
# ) -> tuple[np.ndarray, np.ndarray]:
#     """Learn two mixture components with NMF and identify them by references."""
#     mixture_audio = _as_mono(mixture)
#     first = _resample(_as_mono(voice_one), voice_one_sample_rate or sample_rate, sample_rate)
#     second = _resample(_as_mono(voice_two), voice_two_sample_rate or sample_rate, sample_rate)
#     n_fft, hop_length = 1024, 256
#
#     _, _, mixture_stft = signal.stft(
#         mixture_audio,
#         fs=sample_rate,
#         window="hann",
#         nperseg=n_fft,
#         noverlap=n_fft - hop_length,
#         nfft=n_fft,
#         boundary="zeros",
#     )
#     mixture_power = np.abs(mixture_stft) ** 2 + 1e-8
#
#     # NMF expects observations by features: time frames by frequency bins.
#     model = NMF(n_components=2, init="nndsvda", random_state=0, max_iter=500)
#     activations = model.fit_transform(mixture_power.T)
#     bases = model.components_
#
#     first_profile = _reference_profile(first, sample_rate, n_fft, hop_length)
#     second_profile = _reference_profile(second, sample_rate, n_fft, hop_length)
#     basis_profiles = bases / np.maximum(bases.sum(axis=1, keepdims=True), 1e-12)
#     first_scores = basis_profiles @ first_profile
#     second_scores = basis_profiles @ second_profile
#     first_component = int(np.argmax(first_scores - second_scores))
#     second_component = 1 - first_component
#
#     first_power = bases[first_component][:, None] * activations[:, first_component][None, :]
#     second_power = bases[second_component][:, None] * activations[:, second_component][None, :]
#     denominator = first_power + second_power + 1e-12
#     first_mask = first_power / denominator
#     second_mask = second_power / denominator
#     first_estimate = _istft_like(
#         mixture_stft * first_mask, sample_rate, n_fft, hop_length, len(mixture_audio)
#     )
#     second_estimate = _istft_like(
#         mixture_stft * second_mask, sample_rate, n_fft, hop_length, len(mixture_audio)
#     )
#     return first_estimate, second_estimate
#
#
# def remove_mixer_voice_ml(
#     mixture: np.ndarray,
#     voice_to_remove: np.ndarray,
#     other_voice: np.ndarray,
#     sample_rate: int = 16000,
# ) -> np.ndarray:
#     """ML/NMF version of remove_mixer_voice; disabled until explicitly enabled."""
#     _, remaining = separate_two_voices_ml(
#         mixture, voice_to_remove, other_voice, sample_rate=sample_rate
#     )
#     return remaining


__all__ = ["remove_mixer_voice", "separate_two_voices", "separate_two_voice_files"]