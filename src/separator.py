from sklearn.decomposition import FastICA
import numpy as np

def mix_sources_for_ica(sources, mixing_matrix=None):
    """
    Mixes N sources into M channels using a mixing matrix.
    Args:
        sources (list of ndarrays): List of source audio arrays.
        mixing_matrix (ndarray, optional): MxN mixing matrix.
    Returns:
        ndarray: Mixed signals of shape (n_samples, M)
    """
    # Ensure all sources are the same length
    max_len = max(len(s) for s in sources)
    S = np.zeros((max_len, len(sources)))
    for i, s in enumerate(sources):
        S[:len(s), i] = s
        
    if mixing_matrix is None:
        # Default: random full-rank mixing matrix
        np.random.seed(42) # For reproducibility
        mixing_matrix = np.random.rand(len(sources), len(sources))
        
    X = np.dot(S, mixing_matrix.T)
    return X, mixing_matrix

def separate_sources_ica(mixed_signals, n_components=2):
    """
    Separates independent sources from mixed channels using FastICA.
    
    Args:
        mixed_signals (ndarray): Shape (n_samples, n_channels).
        n_components (int): Number of independent sources to extract.
        
    Returns:
        ndarray: Separated sources of shape (n_components, n_samples).
    """
    ica = FastICA(n_components=n_components, random_state=42)
    S_ = ica.fit_transform(mixed_signals)  # Reconstruct signals
    # S_ shape is (n_samples, n_components)
    
    # Scale back to reasonable audio amplitude
    # FastICA outputs are zero mean and unit variance.
    # We can normalize them between -1 and 1
    separated = []
    for i in range(n_components):
        s = S_[:, i]
        if np.max(np.abs(s)) > 0:
            s = s / np.max(np.abs(s))
        separated.append(s)
        
    return separated

