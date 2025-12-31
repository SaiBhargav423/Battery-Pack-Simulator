"""
Correlated Fault Modeling using Copulas

This module provides copula-based dependency modeling for correlated faults:
- Gaussian copula for linear correlations
- Archimedean copulas (Clayton, Gumbel, Frank) for various dependency structures
- Specialized copula for thermal propagation
"""

import numpy as np
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple, List
from scipy import stats
from scipy.stats import multivariate_normal
from scipy.special import gamma


class CopulaModel(ABC):
    """Base class for copula-based dependency modeling."""
    
    @abstractmethod
    def sample(self, n_samples: int, rng: Optional[np.random.Generator] = None) -> np.ndarray:
        """
        Sample correlated uniform random variables [0, 1].
        
        Args:
            n_samples: Number of samples
            rng: Random number generator
            
        Returns:
            Array of shape (n_samples, n_dimensions) with values in [0, 1]
        """
        pass
    
    @abstractmethod
    def transform_to_marginals(self, uniform_samples: np.ndarray, 
                               marginals: List[stats.rv_continuous]) -> np.ndarray:
        """
        Transform uniform samples to desired marginal distributions.
        
        Args:
            uniform_samples: Uniform samples from copula [0, 1]
            marginals: List of scipy.stats distributions for each dimension
            
        Returns:
            Transformed samples with desired marginals
        """
        pass
    
    def sample_correlated_faults(self, n_faults: int, 
                                 fault_parameters: List[Dict[str, Any]],
                                 rng: Optional[np.random.Generator] = None) -> List[Dict[str, Any]]:
        """
        Sample correlated fault parameters.
        
        Args:
            n_faults: Number of faults to sample
            fault_parameters: List of parameter dictionaries (one per fault)
            rng: Random number generator
            
        Returns:
            List of sampled fault parameter dictionaries
        """
        # Sample uniform variables from copula
        uniform_samples = self.sample(n_faults, rng)
        
        # Transform to desired marginals for each fault
        results = []
        for i, fault_params in enumerate(fault_parameters):
            sampled_params = {}
            for param_name, param_dist in fault_params.items():
                if isinstance(param_dist, dict):
                    # Extract distribution parameters
                    dist_type = param_dist.get('distribution', 'uniform')
                    if dist_type == 'uniform':
                        min_val = param_dist.get('min', 0.0)
                        max_val = param_dist.get('max', 1.0)
                        # Transform uniform [0,1] to [min, max]
                        sampled_params[param_name] = min_val + uniform_samples[i, 0] * (max_val - min_val)
                    elif dist_type == 'normal':
                        mean = param_dist.get('mean', 0.0)
                        std = param_dist.get('std', 1.0)
                        # Use inverse CDF of normal
                        sampled_params[param_name] = stats.norm.ppf(uniform_samples[i, 0], loc=mean, scale=std)
                    else:
                        sampled_params[param_name] = uniform_samples[i, 0]
                else:
                    sampled_params[param_name] = param_dist
            results.append(sampled_params)
        
        return results


class GaussianCopula(CopulaModel):
    """
    Gaussian copula for linear correlations.
    
    Uses multivariate normal distribution to model dependencies.
    """
    
    def __init__(self, correlation_matrix: np.ndarray):
        """
        Initialize Gaussian copula.
        
        Args:
            correlation_matrix: Correlation matrix (must be symmetric, positive definite)
        """
        self._correlation_matrix = np.array(correlation_matrix)
        self._n_dim = self._correlation_matrix.shape[0]
        
        # Validate correlation matrix
        if self._correlation_matrix.shape != (self._n_dim, self._n_dim):
            raise ValueError("Correlation matrix must be square")
        if not np.allclose(self._correlation_matrix, self._correlation_matrix.T):
            raise ValueError("Correlation matrix must be symmetric")
        if not np.all(np.linalg.eigvals(self._correlation_matrix) > 0):
            raise ValueError("Correlation matrix must be positive definite")
    
    def sample(self, n_samples: int, rng: Optional[np.random.Generator] = None) -> np.ndarray:
        """Sample from Gaussian copula."""
        if rng is None:
            rng = np.random.default_rng()
        
        # Sample from multivariate normal with zero mean, unit variance, given correlation
        mean = np.zeros(self._n_dim)
        samples = multivariate_normal.rvs(mean=mean, cov=self._correlation_matrix, 
                                         size=n_samples, random_state=rng)
        
        # Transform to uniform [0, 1] using standard normal CDF
        uniform_samples = stats.norm.cdf(samples)
        
        return uniform_samples
    
    def transform_to_marginals(self, uniform_samples: np.ndarray, 
                               marginals: List[stats.rv_continuous]) -> np.ndarray:
        """Transform to desired marginals."""
        if len(marginals) != self._n_dim:
            raise ValueError(f"Number of marginals ({len(marginals)}) must match dimensions ({self._n_dim})")
        
        transformed = np.zeros_like(uniform_samples)
        for i, marginal in enumerate(marginals):
            transformed[:, i] = marginal.ppf(uniform_samples[:, i])
        
        return transformed
    
    @property
    def correlation_matrix(self) -> np.ndarray:
        """Get correlation matrix."""
        return self._correlation_matrix.copy()


class ArchimedeanCopula(CopulaModel):
    """
    Archimedean copula base class.
    
    Supports Clayton, Gumbel, and Frank copulas.
    """
    
    def __init__(self, theta: float, family: str = 'clayton'):
        """
        Initialize Archimedean copula.
        
        Args:
            theta: Copula parameter (must be > 0 for Clayton/Gumbel, != 0 for Frank)
            family: Copula family ('clayton', 'gumbel', 'frank')
        """
        self._theta = theta
        self._family = family.lower()
        
        if self._family == 'clayton' and theta <= 0:
            raise ValueError("Clayton copula requires theta > 0")
        if self._family == 'gumbel' and theta < 1:
            raise ValueError("Gumbel copula requires theta >= 1")
        if self._family == 'frank' and theta == 0:
            raise ValueError("Frank copula requires theta != 0")
    
    def sample(self, n_samples: int, rng: Optional[np.random.Generator] = None) -> np.ndarray:
        """Sample from Archimedean copula (2D only for simplicity)."""
        if rng is None:
            rng = np.random.default_rng()
        
        # For 2D Archimedean copulas, use conditional sampling
        u1 = rng.uniform(0, 1, n_samples)
        
        if self._family == 'clayton':
            # Clayton copula
            u2 = u1 * np.power(rng.uniform(0, 1, n_samples), -1.0 / (self._theta + 1.0))
            u2 = np.clip(u2, 0, 1)
        elif self._family == 'gumbel':
            # Gumbel copula (approximation)
            w = rng.uniform(0, 1, n_samples)
            u2 = np.power(-np.log(u1) / np.power(-np.log(w), 1.0/self._theta), 1.0/self._theta)
            u2 = np.clip(u2, 0, 1)
        elif self._family == 'frank':
            # Frank copula
            w = rng.uniform(0, 1, n_samples)
            u2 = -np.log(1.0 + w * (np.exp(-self._theta) - 1.0) / (1.0 + (np.exp(-self._theta * u1) - 1.0) * w)) / self._theta
            u2 = np.clip(u2, 0, 1)
        else:
            raise ValueError(f"Unknown Archimedean family: {self._family}")
        
        return np.column_stack([u1, u2])
    
    def transform_to_marginals(self, uniform_samples: np.ndarray, 
                               marginals: List[stats.rv_continuous]) -> np.ndarray:
        """Transform to desired marginals."""
        if len(marginals) != 2:
            raise ValueError("Archimedean copula currently supports 2D only")
        
        transformed = np.zeros_like(uniform_samples)
        for i, marginal in enumerate(marginals):
            transformed[:, i] = marginal.ppf(uniform_samples[:, i])
        
        return transformed


class ThermalPropagationCopula(CopulaModel):
    """
    Specialized copula for thermal propagation between cells.
    
    Models correlated temperature faults with distance-based correlation.
    """
    
    def __init__(self, cell_indices: List[int], correlation_coefficient: float = 0.7,
                 distance_decay: float = 0.5):
        """
        Initialize thermal propagation copula.
        
        Args:
            cell_indices: List of cell indices involved in propagation
            correlation_coefficient: Base correlation coefficient (0-1)
            distance_decay: Decay factor for distance-based correlation
        """
        self._cell_indices = cell_indices
        self._n_cells = len(cell_indices)
        self._base_correlation = correlation_coefficient
        self._distance_decay = distance_decay
        
        # Build correlation matrix based on cell distances
        self._correlation_matrix = self._build_correlation_matrix()
        
        # Use Gaussian copula internally
        self._gaussian_copula = GaussianCopula(self._correlation_matrix)
    
    def _build_correlation_matrix(self) -> np.ndarray:
        """Build correlation matrix based on cell distances."""
        corr_matrix = np.eye(self._n_cells)
        
        for i in range(self._n_cells):
            for j in range(i + 1, self._n_cells):
                # Distance between cells
                distance = abs(self._cell_indices[i] - self._cell_indices[j])
                
                # Correlation decays with distance
                correlation = self._base_correlation * np.exp(-self._distance_decay * distance)
                corr_matrix[i, j] = correlation
                corr_matrix[j, i] = correlation
        
        return corr_matrix
    
    def sample(self, n_samples: int, rng: Optional[np.random.Generator] = None) -> np.ndarray:
        """Sample from thermal propagation copula."""
        return self._gaussian_copula.sample(n_samples, rng)
    
    def transform_to_marginals(self, uniform_samples: np.ndarray, 
                               marginals: List[stats.rv_continuous]) -> np.ndarray:
        """Transform to desired marginals."""
        return self._gaussian_copula.transform_to_marginals(uniform_samples, marginals)
    
    def apply_thermal_propagation(self, cell_temperatures: np.ndarray, 
                                  base_temperature: float = 25.0) -> np.ndarray:
        """
        Apply thermal propagation effects to cell temperatures.
        
        Args:
            cell_temperatures: Current cell temperatures
            base_temperature: Base/ambient temperature
            
        Returns:
            Updated temperatures with propagation effects
        """
        # Sample correlated temperature increases
        n_samples = 1
        uniform_samples = self.sample(n_samples)
        
        # Transform to temperature increases (exponential distribution)
        temp_increases = []
        for i in range(self._n_cells):
            # Sample temperature increase (exponential with mean based on correlation)
            mean_increase = (cell_temperatures[i] - base_temperature) * self._base_correlation
            temp_increase = stats.expon.rvs(scale=mean_increase) if mean_increase > 0 else 0.0
            temp_increases.append(temp_increase)
        
        # Apply propagation
        propagated_temps = cell_temperatures.copy()
        for i, cell_idx in enumerate(self._cell_indices):
            if cell_idx < len(propagated_temps):
                propagated_temps[cell_idx] += temp_increases[i]
        
        return propagated_temps
    
    @property
    def correlation_matrix(self) -> np.ndarray:
        """Get correlation matrix."""
        return self._correlation_matrix.copy()

