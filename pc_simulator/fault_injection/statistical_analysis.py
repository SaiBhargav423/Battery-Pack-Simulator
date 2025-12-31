"""
Statistical Analysis and Convergence Monitoring

This module provides comprehensive statistical analysis capabilities:
- Ensemble statistics (mean, std, percentiles)
- Confidence intervals (bootstrap)
- Convergence monitoring
- Sensitivity analysis (Sobol indices)
- Risk quantification (failure probability, VaR, CVaR)
"""

import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from scipy import stats
from scipy.stats import bootstrap
import warnings


class EnsembleAnalyzer:
    """Statistical analysis of ensemble results."""
    
    def __init__(self, confidence_level: float = 0.95):
        """
        Initialize ensemble analyzer.
        
        Args:
            confidence_level: Confidence level for intervals (default: 0.95)
        """
        self._confidence_level = confidence_level
    
    def compute_ensemble_stats(self, results: List[Dict[str, Any]], 
                               metric_name: str = 'result') -> Dict[str, Any]:
        """
        Compute comprehensive ensemble statistics.
        
        Args:
            results: List of result dictionaries
            metric_name: Name of metric to analyze
            
        Returns:
            Dictionary with statistics
        """
        # Extract metric values
        values = np.array([r.get(metric_name, 0.0) for r in results])
        
        if len(values) == 0:
            return {}
        
        # Basic statistics
        stats_dict = {
            'mean': float(np.mean(values)),
            'median': float(np.median(values)),
            'std': float(np.std(values)),
            'variance': float(np.var(values)),
            'min': float(np.min(values)),
            'max': float(np.max(values)),
            'range': float(np.max(values) - np.min(values)),
            'n_samples': len(values),
        }
        
        # Percentiles
        percentiles = [1, 5, 10, 25, 50, 75, 90, 95, 99]
        for p in percentiles:
            stats_dict[f'p{p}'] = float(np.percentile(values, p))
        
        # Skewness and kurtosis
        if len(values) > 2:
            stats_dict['skewness'] = float(stats.skew(values))
            stats_dict['kurtosis'] = float(stats.kurtosis(values))
        
        # Confidence intervals
        ci = self.compute_confidence_intervals(values)
        stats_dict['ci_lower'] = ci[0]
        stats_dict['ci_upper'] = ci[1]
        
        return stats_dict
    
    def compute_confidence_intervals(self, values: np.ndarray, 
                                    method: str = 'bootstrap') -> Tuple[float, float]:
        """
        Compute confidence intervals.
        
        Args:
            values: Array of values
            method: 'bootstrap' or 'normal' (assumes normal distribution)
            
        Returns:
            Tuple of (lower_bound, upper_bound)
        """
        if len(values) == 0:
            return (0.0, 0.0)
        
        alpha = 1.0 - self._confidence_level
        
        if method == 'bootstrap':
            # Bootstrap method (more robust)
            try:
                # Use scipy's bootstrap if available
                bootstrap_result = bootstrap((values,), np.mean, 
                                            confidence_level=self._confidence_level,
                                            method='percentile')
                return (float(bootstrap_result.confidence_interval.low),
                       float(bootstrap_result.confidence_interval.high))
            except:
                # Fallback to manual bootstrap
                n_bootstrap = min(1000, len(values) * 10)
                bootstrap_means = []
                rng = np.random.default_rng()
                for _ in range(n_bootstrap):
                    bootstrap_sample = rng.choice(values, size=len(values), replace=True)
                    bootstrap_means.append(np.mean(bootstrap_sample))
                
                bootstrap_means = np.array(bootstrap_means)
                lower = np.percentile(bootstrap_means, 100 * alpha / 2)
                upper = np.percentile(bootstrap_means, 100 * (1 - alpha / 2))
                return (float(lower), float(upper))
        
        elif method == 'normal':
            # Assume normal distribution
            mean = np.mean(values)
            std = np.std(values)
            n = len(values)
            se = std / np.sqrt(n)  # Standard error
            
            # t-distribution for small samples, normal for large
            if n < 30:
                t_critical = stats.t.ppf(1 - alpha / 2, df=n - 1)
                margin = t_critical * se
            else:
                z_critical = stats.norm.ppf(1 - alpha / 2)
                margin = z_critical * se
            
            return (float(mean - margin), float(mean + margin))
        
        else:
            raise ValueError(f"Unknown method: {method}")


class ConvergenceMonitor:
    """Monitor convergence of ensemble statistics."""
    
    def __init__(self, tolerance: float = 0.01, window_size: int = 50, 
                 min_samples: int = 100):
        """
        Initialize convergence monitor.
        
        Args:
            tolerance: Relative change tolerance for convergence
            window_size: Number of recent samples to consider
            min_samples: Minimum samples before checking convergence
        """
        self._tolerance = tolerance
        self._window_size = window_size
        self._min_samples = min_samples
        self._statistic_history = []
        self._converged = False
    
    def update(self, statistic_value: float) -> bool:
        """
        Update with new statistic value and check convergence.
        
        Args:
            statistic_value: Current statistic value
            
        Returns:
            True if converged, False otherwise
        """
        self._statistic_history.append(statistic_value)
        
        if len(self._statistic_history) < self._min_samples:
            return False
        
        if self._converged:
            return True
        
        # Check relative change in recent window
        if len(self._statistic_history) >= self._window_size:
            recent_values = np.array(self._statistic_history[-self._window_size:])
            mean_recent = np.mean(recent_values)
            
            if abs(mean_recent) > 1e-10:  # Avoid division by zero
                # Coefficient of variation
                cv = np.std(recent_values) / abs(mean_recent)
                
                if cv < self._tolerance:
                    self._converged = True
                    return True
        
        return False
    
    def reset(self):
        """Reset convergence history."""
        self._statistic_history = []
        self._converged = False
    
    @property
    def history(self) -> List[float]:
        """Get statistic history."""
        return self._statistic_history.copy()
    
    @property
    def converged(self) -> bool:
        """Check if converged."""
        return self._converged


class SensitivityAnalyzer:
    """Sensitivity analysis using Sobol indices."""
    
    def compute_sobol_indices(self, results: List[Dict[str, Any]], 
                             param_names: List[str],
                             metric_name: str = 'result') -> Dict[str, float]:
        """
        Compute Sobol indices for global sensitivity analysis.
        
        Note: This is a simplified implementation. Full Sobol analysis requires
        specific sampling strategies (A and B matrices).
        
        Args:
            results: List of result dictionaries with parameters and metric
            param_names: List of parameter names
            metric_name: Name of metric to analyze
            
        Returns:
            Dictionary mapping parameter names to Sobol indices
        """
        if len(results) < 10:
            warnings.warn("Insufficient samples for reliable Sobol indices")
            return {name: 0.0 for name in param_names}
        
        # Extract parameter values and metric
        param_values = []
        metric_values = []
        
        for result in results:
            params = result.get('parameters', [])
            if isinstance(params, list) and len(params) == len(param_names):
                param_values.append(params)
                metric_values.append(result.get(metric_name, 0.0))
        
        if len(param_values) == 0:
            return {name: 0.0 for name in param_names}
        
        param_array = np.array(param_values)
        metric_array = np.array(metric_values)
        
        # Compute correlation-based sensitivity (simplified)
        # Full Sobol indices require more sophisticated computation
        sensitivities = {}
        for i, param_name in enumerate(param_names):
            if param_array.shape[1] > i:
                # Pearson correlation coefficient as proxy for sensitivity
                correlation = np.corrcoef(param_array[:, i], metric_array)[0, 1]
                sensitivities[param_name] = float(abs(correlation)) if not np.isnan(correlation) else 0.0
            else:
                sensitivities[param_name] = 0.0
        
        # Normalize to sum to 1 (for relative importance)
        total = sum(sensitivities.values())
        if total > 0:
            sensitivities = {k: v / total for k, v in sensitivities.items()}
        
        return sensitivities


class RiskQuantifier:
    """Risk quantification and reliability metrics."""
    
    def __init__(self, confidence_level: float = 0.95):
        """
        Initialize risk quantifier.
        
        Args:
            confidence_level: Confidence level for risk metrics
        """
        self._confidence_level = confidence_level
    
    def estimate_failure_probability(self, results: List[Dict[str, Any]], 
                                    threshold: float,
                                    metric_name: str = 'result',
                                    failure_condition: str = 'above') -> Dict[str, float]:
        """
        Estimate failure probability.
        
        Args:
            results: List of result dictionaries
            threshold: Failure threshold
            metric_name: Name of metric to check
            failure_condition: 'above' or 'below' threshold
            
        Returns:
            Dictionary with failure probability and confidence interval
        """
        # Extract metric values
        values = np.array([r.get(metric_name, 0.0) for r in results])
        
        if len(values) == 0:
            return {'failure_probability': 0.0, 'ci_lower': 0.0, 'ci_upper': 0.0}
        
        # Count failures
        if failure_condition == 'above':
            failures = np.sum(values > threshold)
        else:  # below
            failures = np.sum(values < threshold)
        
        failure_prob = failures / len(values)
        
        # Confidence interval for proportion (binomial)
        # Using normal approximation
        n = len(values)
        p = failure_prob
        se = np.sqrt(p * (1 - p) / n)
        z = stats.norm.ppf(1 - (1 - self._confidence_level) / 2)
        
        ci_lower = max(0.0, p - z * se)
        ci_upper = min(1.0, p + z * se)
        
        return {
            'failure_probability': float(failure_prob),
            'ci_lower': float(ci_lower),
            'ci_upper': float(ci_upper),
            'n_failures': int(failures),
            'n_total': n
        }
    
    def compute_var_cvar(self, results: List[Dict[str, Any]], 
                        confidence_level: float,
                        metric_name: str = 'result') -> Dict[str, float]:
        """
        Compute Value at Risk (VaR) and Conditional VaR (CVaR).
        
        Args:
            results: List of result dictionaries
            confidence_level: Confidence level (e.g., 0.95 for 95% VaR)
            metric_name: Name of metric to analyze
            
        Returns:
            Dictionary with VaR and CVaR
        """
        # Extract metric values
        values = np.array([r.get(metric_name, 0.0) for r in results])
        
        if len(values) == 0:
            return {'var': 0.0, 'cvar': 0.0}
        
        # VaR: percentile at confidence level
        var = np.percentile(values, 100 * (1 - confidence_level))
        
        # CVaR: expected value of tail beyond VaR
        tail_values = values[values <= var]
        cvar = np.mean(tail_values) if len(tail_values) > 0 else var
        
        return {
            'var': float(var),
            'cvar': float(cvar),
            'confidence_level': confidence_level
        }
    
    def compute_reliability_metrics(self, results: List[Dict[str, Any]],
                                   time_values: Optional[np.ndarray] = None,
                                   metric_name: str = 'result',
                                   threshold: float = 0.0) -> Dict[str, float]:
        """
        Compute reliability metrics (MTBF, MTTF, reliability function).
        
        Args:
            results: List of result dictionaries
            time_values: Optional time values for each result
            metric_name: Name of metric to analyze
            threshold: Failure threshold
            
        Returns:
            Dictionary with reliability metrics
        """
        # Extract metric values
        values = np.array([r.get(metric_name, 0.0) for r in results])
        
        if len(values) == 0:
            return {}
        
        # Identify failures
        failures = values < threshold if threshold > 0 else values == 0
        
        n_failures = np.sum(failures)
        n_total = len(values)
        
        if n_failures == 0:
            return {
                'mtbf': np.inf,
                'mttf': np.inf,
                'reliability': 1.0,
                'failure_rate': 0.0
            }
        
        # Mean Time Between Failures (MTBF) or Mean Time To Failure (MTTF)
        if time_values is not None and len(time_values) == len(values):
            failure_times = time_values[failures]
            if len(failure_times) > 0:
                mttf = np.mean(failure_times)
            else:
                mttf = np.inf
        else:
            # Assume uniform time distribution
            mttf = n_total / (2.0 * n_failures) if n_failures > 0 else np.inf
        
        # Reliability (survival probability)
        reliability = 1.0 - (n_failures / n_total)
        
        # Failure rate (failures per unit time)
        failure_rate = n_failures / n_total
        
        return {
            'mtbf': float(mttf) if np.isfinite(mttf) else np.inf,
            'mttf': float(mttf) if np.isfinite(mttf) else np.inf,
            'reliability': float(reliability),
            'failure_rate': float(failure_rate),
            'n_failures': int(n_failures),
            'n_total': n_total
        }

