from fpdf import FPDF

class PDF(FPDF):
    def header(self):
        self.set_font('helvetica', 'B', 15)
        self.cell(0, 10, 'Audio DSP & Communications Engineering Suite', border=False, ln=1, align='C')
        self.set_font('helvetica', 'I', 10)
        self.cell(0, 10, 'Comprehensive Workflow & Signal Principles', border=False, ln=1, align='C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    def chapter_title(self, num, title):
        self.set_font('helvetica', 'B', 12)
        self.set_fill_color(200, 220, 255)
        self.cell(0, 10, f'{num}. {title}', 0, 1, 'L', fill=True)
        self.cell(0, 10, f'{title}', 0, 1, 'L', fill=True)
        self.ln(4)

    def chapter_body(self, body):
        self.set_font('helvetica', '', 11)
        self.multi_cell(0, 6, body)
        self.ln()

pdf = PDF()
pdf.add_page()

content = [
    ('Introduction', 'This document serves as a comprehensive guide to the Digital Signal Processing (DSP) and Communications principles implemented in the Master Audio Lab.'),
    ('1. Core Time-Domain Operations', '''Trimming: Extracts a specific time window from the audio array by slicing the discrete samples: data[start_idx:end_idx].

Volume Scaling: A simple amplitude multiplication of the discrete signal by a scalar factor.

Time Reversal: Flips the discrete time sequence x[n] to x[-n]. In Python, this is achieved via array slicing data[::-1], which plays the audio backwards.

Echo: Modeled as a Finite Impulse Response (FIR) filter or convolution. The signal is delayed by a specific number of samples (delay_ms * sr) and added back to the original signal with an amplitude decay factor.'''),
    ('2. Frequency & Time Stretching', '''Resampling (Chipmunk Effect): Alters the sampling rate of the digital signal. When playback remains at the original sample rate, both the speed and pitch shift proportionally. We use Librosa for high-quality resampling.

Phase Vocoder: A sophisticated algorithm to stretch time without affecting pitch. It uses the Short-Time Fourier Transform (STFT) to analyze frequencies, scales the time axis, carefully unwraps and preserves the phase consistency between frames, and reconstructs the audio using the Inverse STFT.

Aliasing: Based on the Nyquist-Shannon Sampling Theorem. If a signal is downsampled without first applying a strict lowpass anti-aliasing filter, high frequencies wrap around (alias) into the lower frequency spectrum, causing irreversible metallic distortion.'''),
    ('3. Digital Filtering & Equalization', '''10-Band EQ: Implemented using Web Audio API Biquad Filters. These are Infinite Impulse Response (IIR) peaking filters that allow real-time boosting or cutting of specific frequency bands.

Digital Filters (Backend): Uses SciPys Butterworth filter design. Butterworth filters are chosen for their maximally flat frequency response in the passband, ensuring no ripple artifacts when applying Lowpass, Highpass, or Bandpass operations.'''),
    ('4. Communication Channel Simulation', '''Multipath / Inter-Symbol Interference (ISI): Simulates a physical environment where a signal reflects off buildings or mountains. This is implemented by convolving the audio with a channel impulse response (taps).

AWGN (Additive White Gaussian Noise): Simulates thermal noise in radio receivers. We calculate the signal power, generate Gaussian noise of corresponding power based on the desired Signal-to-Noise Ratio (SNR), and add it to the signal.

Single-Tone Jamming: Simulates an intentional or unintentional continuous wave (CW) interference. We generate a pure sine wave at a specific frequency (e.g., 1000 Hz) and add it to the audio at a specific SNR.'''),
    ('5. Receiver & Equalization', '''Zero-Forcing (ZF) Equalizer: The simplest equalizer. It takes the FFT of the signal and the channel taps, and divides the signal by the channel response (W = 1/H). While it perfectly removes multipath, it severely amplifies background noise in frequencies where the channel response is weak.

Minimum Mean Square Error (MMSE) Equalizer: A more robust approach that considers the noise floor. It balances inverting the channel and suppressing noise (W = H* / (|H|^2 + 1/SNR)), yielding much better audio recovery in noisy environments.'''),
    ('6. Voice Biometrics (Speaker Matcher)', '''Feature Extraction: Uses Mel-Frequency Cepstral Coefficients (MFCCs). This mimics the human ears non-linear perception of pitch (the Mel scale) and extracts the spectral envelope (timbre) of the voice, ignoring pitch variations.

Identification: Computes the mean MFCC vector across time to create a Voice Print. To identify a speaker, it calculates the Cosine Similarity between the uploaded voice print and all stored voice prints in the SQLite database, returning the closest match.''')
    ('Overview', 'This document serves as a comprehensive guide to the Digital Signal Processing (DSP) and Communications principles implemented in the Master Audio Lab.'),
    ('1. Core Time-Domain Operations', '''Trimming: Extracts a specific time window from the audio array by slicing the discrete samples: data[start_idx:end_idx].\n\nVolume Scaling: A simple amplitude multiplication of the discrete signal by a scalar factor.\n\nTime Reversal: Flips the discrete time sequence x[n] to x[-n]. In Python, this is achieved via array slicing data[::-1], which plays the audio backwards.\n\nEcho: Modeled as a Finite Impulse Response (FIR) filter or convolution. The signal is delayed by a specific number of samples (delay_ms * sr) and added back to the original signal with an amplitude decay factor.'''),
    ('2. Frequency & Time Stretching', '''Resampling (Chipmunk Effect): Alters the sampling rate of the digital signal. When playback remains at the original sample rate, both the speed and pitch shift proportionally. We use Librosa for high-quality resampling.\n\nPhase Vocoder: A sophisticated algorithm to stretch time without affecting pitch. It uses the Short-Time Fourier Transform (STFT) to analyze frequencies, scales the time axis, carefully unwraps and preserves the phase consistency between frames, and reconstructs the audio using the Inverse STFT.\n\nAliasing: Based on the Nyquist-Shannon Sampling Theorem. If a signal is downsampled without first applying a strict lowpass anti-aliasing filter, high frequencies wrap around (alias) into the lower frequency spectrum, causing irreversible metallic distortion.'''),
    ('3. Digital Filtering & Equalization', '''10-Band EQ: Implemented using Web Audio API Biquad Filters. These are Infinite Impulse Response (IIR) peaking filters that allow real-time boosting or cutting of specific frequency bands.\n\nDigital Filters (Backend): Uses SciPys Butterworth filter design. Butterworth filters are chosen for their maximally flat frequency response in the passband, ensuring no ripple artifacts when applying Lowpass, Highpass, or Bandpass operations.'''),
    ('4. Communication Channel Simulation', '''Multipath / Inter-Symbol Interference (ISI): Simulates a physical environment where a signal reflects off buildings or mountains. This is implemented by convolving the audio with a channel impulse response (taps).\n\nAWGN (Additive White Gaussian Noise): Simulates thermal noise in radio receivers. We calculate the signal power, generate Gaussian noise of corresponding power based on the desired Signal-to-Noise Ratio (SNR), and add it to the signal.\n\nSingle-Tone Jamming: Simulates an intentional or unintentional continuous wave (CW) interference. We generate a pure sine wave at a specific frequency (e.g., 1000 Hz) and add it to the audio at a specific SNR.'''),
    ('5. Receiver & Equalization', '''Zero-Forcing (ZF) Equalizer: The simplest equalizer. It takes the FFT of the signal and the channel taps, and divides the signal by the channel response (W = 1/H). While it perfectly removes multipath, it severely amplifies background noise in frequencies where the channel response is weak.\n\nMinimum Mean Square Error (MMSE) Equalizer: A more robust approach that considers the noise floor. It balances inverting the channel and suppressing noise (W = H* / (|H|^2 + 1/SNR)), yielding much better audio recovery in noisy environments.'''),
    ('6. Voice Biometrics (Speaker Matcher)', '''Feature Extraction: Uses Mel-Frequency Cepstral Coefficients (MFCCs). This mimics the human ears non-linear perception of pitch (the Mel scale) and extracts the spectral envelope (timbre) of the voice, ignoring pitch variations.\n\nIdentification: Computes the mean MFCC vector across time to create a Voice Print. To identify a speaker, it calculates the Cosine Similarity between the uploaded voice print and all stored voice prints in the SQLite database, returning the closest match.''')
    ('1. Core Time-Domain Operations', 'Trimming: Extracts a specific time window from the audio array by slicing the discrete samples: data[start_idx:end_idx].\n\nVolume Scaling: A simple amplitude multiplication of the discrete signal by a scalar factor.\n\nTime Reversal: Flips the discrete time sequence x[n] to x[-n]. In Python, this is achieved via array slicing data[::-1], which plays the audio backwards.\n\nEcho: Modeled as a Finite Impulse Response (FIR) filter or convolution. The signal is delayed by a specific number of samples (delay_ms * sr) and added back to the original signal with an amplitude decay factor.'),
    ('2. Frequency & Time Stretching', 'Resampling (Chipmunk Effect): Alters the sampling rate of the digital signal. When playback remains at the original sample rate, both the speed and pitch shift proportionally. We use Librosa for high-quality resampling.\n\nPhase Vocoder: A sophisticated algorithm to stretch time without affecting pitch. It uses the Short-Time Fourier Transform (STFT) to analyze frequencies, scales the time axis, carefully unwraps and preserves the phase consistency between frames, and reconstructs the audio using the Inverse STFT.\n\nAliasing: Based on the Nyquist-Shannon Sampling Theorem. If a signal is downsampled without first applying a strict lowpass anti-aliasing filter, high frequencies wrap around (alias) into the lower frequency spectrum, causing irreversible metallic distortion.'),
    ('3. Digital Filtering & Equalization', '10-Band EQ: Implemented using Web Audio API Biquad Filters. These are Infinite Impulse Response (IIR) peaking filters that allow real-time boosting or cutting of specific frequency bands.\n\nDigital Filters (Backend): Uses SciPys Butterworth filter design. Butterworth filters are chosen for their maximally flat frequency response in the passband, ensuring no ripple artifacts when applying Lowpass, Highpass, or Bandpass operations.'),
    ('4. Communication Channel Simulation', 'Multipath / Inter-Symbol Interference (ISI): Simulates a physical environment where a signal reflects off buildings or mountains. This is implemented by convolving the audio with a channel impulse response (taps).\n\nAWGN (Additive White Gaussian Noise): Simulates thermal noise in radio receivers. We calculate the signal power, generate Gaussian noise of corresponding power based on the desired Signal-to-Noise Ratio (SNR), and add it to the signal.\n\nSingle-Tone Jamming: Simulates an intentional or unintentional continuous wave (CW) interference. We generate a pure sine wave at a specific frequency (e.g., 1000 Hz) and add it to the audio at a specific SNR.'),
    ('5. Receiver & Equalization', 'Zero-Forcing (ZF) Equalizer: The simplest equalizer. It takes the FFT of the signal and the channel taps, and divides the signal by the channel response (W = 1/H). While it perfectly removes multipath, it severely amplifies background noise in frequencies where the channel response is weak.\n\nMinimum Mean Square Error (MMSE) Equalizer: A more robust approach that considers the noise floor. It balances inverting the channel and suppressing noise (W = H* / (|H|^2 + 1/SNR)), yielding much better audio recovery in noisy environments.'),
    ('6. Voice Biometrics (Speaker Matcher)', 'Feature Extraction: Uses Mel-Frequency Cepstral Coefficients (MFCCs). This mimics the human ears non-linear perception of pitch (the Mel scale) and extracts the spectral envelope (timbre) of the voice, ignoring pitch variations.\n\nIdentification: Computes the mean MFCC vector across time to create a Voice Print. To identify a speaker, it calculates the Cosine Similarity between the uploaded voice print and all stored voice prints in the SQLite database, returning the closest match.')
]

for num, (title, body) in enumerate(content, 1):
    if num == 1:
        pdf.chapter_title('Overview', title)
    else:
        pdf.chapter_title(num - 1, title)
    pdf.chapter_body(body.replace('\
', '\n'))
for title, body in content:
    pdf.chapter_title(0, title)
    pdf.chapter_body(body)

pdf.output('DSP_Workflow_Report.pdf')


