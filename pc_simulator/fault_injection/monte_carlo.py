"""
Monte Carlo Framework for Fault Injection

This module provides Monte Carlo simulation capabilities:
- Latin Hypercube Sampling (LHS) for better coverage
- Sobol sequences for quasi-Monte Carlo
- Random sampling
- Ensemble statistics and convergence monitoring
"""

import numpy as np
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Tuple, Callable
from scipy.stats import qmc
import warnings


class SamplingStrategy(ABC):
    """Base class for sampling strategies."""
    
    @abstractmethod
    def generate_samples(self, n_samples: int, n_params: int, 
                        bounds: Optional[List[Tuple[float, float]]] = None,
                        rng: Optional[np.random.Generator] = None) -> np.ndarray:
        """
        Generate parameter samples.
        
        Args:
            n_samples: Number of samples
            n_params: Number of parameters
            bounds: List of (min, max) bounds for each parameter (default: [0, 1])
            rng: Random number generator
            
        Returns:
            Array of shape (n_samples, n_params) with samples
        """
        pass


class LatinHypercubeSampler(SamplingStrategy):
    """
    Latin Hypercube Sampling (LHS) for better space-filling properties.
    
    LHS ensures better coverage of the parameter space with fewer samples
    compared to random sampling.
    """
    
    def generate_samples(self, n_samples: int, n_params: int,
                        bounds: Optional[List[Tuple[float, float]]] = None,
                        rng: Optional[np.random.Generator] = None) -> np.ndarray:
        """Generate LHS samples."""
        if bounds is None:
            bounds = [(0.0, 1.0)] * n_params
        
        if len(bounds) != n_params:
            raise ValueError(f"Number of bounds ({len(bounds)}) must match n_params ({n_params})")
        
        # Use scipy's Latin Hypercube Sampler
        sampler = qmc.LatinHypercube(d=n_params, seed=rng)
        samples = sampler.random(n=n_samples)
        
        # Transform from [0, 1] to desired bounds
        transformed_samples = np.zeros_like(samples)
        for i, (min_val, max_val) in enumerate(bounds):
            transformed_samples[:, i] = min_val + samples[:, i] * (max_val - min_val)
        
        return transformed_samples


class SobolSequenceSampler(SamplingStrategy):
    """
    Sobol sequence for quasi-Monte Carlo sampling.
    
    Sobol sequences provide low-discrepancy sampling for faster convergence.
    """
    
    def generate_samples(self, n_samples: int, n_params: int,
                        bounds: Optional[List[Tuple[float, float]]] = None,
                        rng: Optional[np.random.Generator] = None) -> np.ndarray:
        """Generate Sobol sequence samples."""
        if bounds is None:
            bounds = [(0.0, 1.0)] * n_params
        
        if len(bounds) != n_params:
            raise ValueError(f"Number of bounds ({len(bounds)}) must match n_params ({n_params})")
        
        # Use scipy's Sobol sequence
        try:
            sampler = qmc.Sobol(d=n_params, seed=rng)
            samples = sampler.random(n=n_samples)
        except ValueError as e:
            # Sobol sequence requires n_samples to be power of 2
            # Find next power of 2
            next_power_of_2 = 2 ** int(np.ceil(np.log2(n_samples)))
            warnings.warn(f"Sobol sequence requires n_samples to be power of 2. "
                        f"Using {next_power_of_2} samples instead of {n_samples}.")
            sampler = qmc.Sobol(d=n_params, seed=rng)
            samples = sampler.random(n=next_power_of_2)
            samples = samples[:n_samples]  # Take only requested number
        
        # Transform from [0, 1] to desired bounds
        transformed_samples = np.zeros_like(samples)
        for i, (min_val, max_val) in enumerate(bounds):
            transformed_samples[:, i] = min_val + samples[:, i] * (max_val - min_val)
        
        return transformed_samples


class RandomSampler(SamplingStrategy):
    """Standard random sampling."""
    
    def generate_samples(self, n_samples: int, n_params: int,
                        bounds: Optional[List[Tuple[float, float]]] = None,
                        rng: Optional[np.random.Generator] = None) -> np.ndarray:
        """Generate random samples."""
        if bounds is None:
            bounds = [(0.0, 1.0)] * n_params
        
        if len(bounds) != n_params:
            raise ValueError(f"Number of bounds ({len(bounds)}) must match n_params ({n_params})")
        
        if rng is None:
            rng = np.random.default_rng()
        
        # Generate random samples
        samples = np.zeros((n_samples, n_params))
        for i, (min_val, max_val) in enumerate(bounds):
            samples[:, i] = rng.uniform(min_val, max_val, n_samples)
        
        return samples


class EnsembleStatistics:
    """Statistical analysis of ensemble results."""
    
    @staticmethod
    def compute_statistics(results: List[Dict[str, Any]], 
                          metric_name: str = 'result') -> Dict[str, float]:
        """
        Compute ensemble statistics.
        
        Args:
            results: List of result dictionaries
            metric_name: Name of metric to analyze (key in result dict)
            
        Returns:
            Dictionary with statistics: mean, std, min, max, percentiles
        """
        # Extract metric values
        values = [r.get(metric_name, 0.0) for r in results]
        values = np.array(values)
        
        # Compute statistics
        stats_dict = {
            'mean': float(np.mean(values)),
            'std': float(np.std(values)),
            'min': float(np.min(values)),
            'max': float(np.max(values)),
            'median': float(np.median(values)),
            'p5': float(np.percentile(values, 5)),
            'p25': float(np.percentile(values, 25)),
            'p75': float(np.percentile(values, 75)),
            'p95': float(np.percentile(values, 95)),
            'n_samples': len(values)
        }
        
        return stats_dict
    
    @staticmethod
    def compute_confidence_interval(values: np.ndarray, confidence_level: float = 0.95) -> Tuple[float, float]:
        """
        Compute confidence interval using bootstrap method.
        
        Args:
            values: Array of values
            confidence_level: Confidence level (0.95 for 95% CI)
            
        Returns:
            Tuple of (lower_bound, upper_bound)
        """
        n = len(values)
        n_bootstrap = 1000
        
        # Bootstrap sampling
        bootstrap_means = []
        rng = np.random.default_rng()
        for _ in range(n_bootstrap):
            bootstrap_sample = rng.choice(values, size=n, replace=True)
            bootstrap_means.append(np.mean(bootstrap_sample))
        
        bootstrap_means = np.array(bootstrap_means)
        
        # Compute percentiles
        alpha = 1.0 - confidence_level
        lower = np.percentile(bootstrap_means, 100 * alpha / 2)
        upper = np.percentile(bootstrap_means, 100 * (1 - alpha / 2))
        
        return (float(lower), float(upper))


class ConvergenceMonitor:
    """Monitor convergence of ensemble statistics."""
    
    def __init__(self, tolerance: float = 0.01, window_size: int = 50):
        """
        Initialize convergence monitor.
        
        Args:
            tolerance: Relative change tolerance for convergence
            window_size: Number of recent samples to consider
        """
        self._tolerance = tolerance
        self._window_size = window_size
        self._statistic_history = []
    
    def update(self, statistic_value: float) -> bool:
        """
        Update with new statistic value and check convergence.
        
        Args:
            statistic_value: Current statistic value
            
        Returns:
            True if converged, False otherwise
        """
        self._statistic_history.append(statistic_value)
        
        if len(self._statistic_history) < self._window_size:
            return False
        
        # Check relative change in recent window
        recent_values = np.array(self._statistic_history[-self._window_size:])
        mean_recent = np.mean(recent_values)
        
        if mean_recent == 0:
            return False
        
        # Compute coefficient of variation
        cv = np.std(recent_values) / abs(mean_recent)
        
        return cv < self._tolerance
    
    def reset(self):
        """Reset convergence history."""
        self._statistic_history = []
    
    @property
    def history(self) -> List[float]:
        """Get statistic history."""
        return self._statistic_history.copy()


class MonteCarloFaultInjector:
    """
    Monte Carlo framework for ensemble fault injection.
    
    Runs multiple simulations with different parameter samples to quantify uncertainty.
    """
    
    def __init__(self, sampling_strategy: str = 'lhs', seed: Optional[int] = None):
        """
        Initialize Monte Carlo fault injector.
        
        Args:
            sampling_strategy: 'lhs', 'sobol', or 'random'
            seed: Random seed for reproducibility
        """
        self._seed = seed
        self._rng = np.random.default_rng(seed)
        
        # Initialize sampler
        if sampling_strategy.lower() == 'lhs':
            self._sampler = LatinHypercubeSampler()
        elif sampling_strategy.lower() == 'sobol':
            self._sampler = SobolSequenceSampler()
        elif sampling_strategy.lower() == 'random':
            self._sampler = RandomSampler()
        else:
            raise ValueError(f"Unknown sampling strategy: {sampling_strategy}")
        
        self._sampling_strategy = sampling_strategy
        self._convergence_monitor = ConvergenceMonitor()
    
    def generate_samples(self, n_samples: int, n_params: int,
                        bounds: Optional[List[Tuple[float, float]]] = None) -> np.ndarray:
        """
        Generate parameter samples.
        
        Args:
            n_samples: Number of samples
            n_params: Number of parameters
            bounds: List of (min, max) bounds for each parameter
            
        Returns:
            Array of shape (n_samples, n_params)
        """
        return self._sampler.generate_samples(n_samples, n_params, bounds, self._rng)
    
    def run_ensemble(self, simulation_func: Callable, n_runs: int,
                    parameter_bounds: List[Tuple[float, float]],
                    convergence_tolerance: Optional[float] = None) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Run ensemble of simulations.
        
        Args:
            simulation_func: Function that takes parameter array and returns result dict
            n_runs: Number of ensemble runs
            parameter_bounds: List of (min, max) bounds for each parameter
            convergence_tolerance: Optional convergence tolerance (stops early if converged)
            
        Returns:
            Tuple of (results_list, statistics_dict)
        """
        n_params = len(parameter_bounds)
        
        # Generate parameter samples
        samples = self.generate_samples(n_runs, n_params, parameter_bounds)
        
        # Run simulations
        results = []
        for i, params in enumerate(samples):
            result = simulation_func(params)
            result['run_id'] = i
            result['parameters'] = params.tolist()
            results.append(result)
            
            # Check convergence if tolerance specified
            if convergence_tolerance is not None and i >= 50:  # Start checking after 50 runs
                # Monitor mean of primary metric
                if 'result' in result:
                    converged = self._convergence_monitor.update(result['result'])
                    if converged:
                        print(f"Converged after {i+1} runs")
                        break
        
        # Compute statistics
        statistics = EnsembleStatistics.compute_statistics(results)
        
        return results, statistics
    
    def adaptive_sampling(self, critical_regions: List[Tuple[float, float]],
                        n_additional: int, original_bounds: List[Tuple[float, float]]) -> np.ndarray:
        """
        Generate additional samples focused on critical regions.
        
        Args:
            critical_regions: List of (min, max) regions to focus on
            n_additional: Number of additional samples
            original_bounds: Original parameter bounds
            
        Returns:
            Additional samples
        """
        # For simplicity, sample uniformly from critical regions
        # More sophisticated methods could use importance sampling
        samples = []
        for region_min, region_max in critical_regions:
            region_samples = self._rng.uniform(region_min, region_max, 
                                               size=(n_additional // len(critical_regions), 
                                                     len(original_bounds)))
            samples.append(region_samples)
        
        return np.vstack(samples) if samples else np.array([]).reshape(0, len(original_bounds))
    
    @property
    def sampling_strategy(self) -> str:
        """Get sampling strategy name."""
        return self._sampling_strategy

