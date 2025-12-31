"""
Time-Dependent Probabilistic Models for Fault Injection

This module provides probabilistic models for time-dependent fault occurrence:
- Weibull distribution for aging-related faults
- Exponential distribution for constant-hazard faults
- Poisson process for random fault arrivals
- Markov chains for fault state transitions
"""

import numpy as np
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple
from scipy import stats
from scipy.special import gamma


class TimeDependentFaultModel(ABC):
    """Base class for time-dependent fault probability models."""
    
    @abstractmethod
    def hazard_rate(self, time: float, params: Dict[str, Any]) -> float:
        """
        Compute hazard rate at time t.
        
        Args:
            time: Time in seconds
            params: Model parameters
            
        Returns:
            Hazard rate (failures per unit time)
        """
        pass
    
    @abstractmethod
    def cumulative_hazard(self, time: float, params: Dict[str, Any]) -> float:
        """
        Compute cumulative hazard up to time t.
        
        Args:
            time: Time in seconds
            params: Model parameters
            
        Returns:
            Cumulative hazard
        """
        pass
    
    @abstractmethod
    def sample_fault_time(self, params: Dict[str, Any], rng: Optional[np.random.Generator] = None) -> float:
        """
        Sample fault occurrence time.
        
        Args:
            params: Model parameters
            rng: Random number generator (optional)
            
        Returns:
            Sampled fault time in seconds
        """
        pass
    
    def probability(self, time: float, params: Dict[str, Any]) -> float:
        """
        Compute probability of fault occurring by time t.
        
        Args:
            time: Time in seconds
            params: Model parameters
            
        Returns:
            Probability (0.0 to 1.0)
        """
        H = self.cumulative_hazard(time, params)
        return 1.0 - np.exp(-H)


class WeibullFaultModel(TimeDependentFaultModel):
    """
    Weibull distribution for aging-related faults.
    
    Hazard rate: λ(t) = (β/η) * (t/η)^(β-1)
    - Shape parameter (β): controls aging rate
      - β < 1: decreasing hazard (infant mortality)
      - β = 1: constant hazard (exponential)
      - β > 1: increasing hazard (aging/wear-out)
    - Scale parameter (η): characteristic lifetime
    """
    
    def hazard_rate(self, time: float, params: Dict[str, Any]) -> float:
        """Compute Weibull hazard rate."""
        shape = params.get('shape', 2.0)  # β
        scale = params.get('scale', 3600.0)  # η (seconds)
        
        if time <= 0:
            return 0.0
        
        if shape <= 0 or scale <= 0:
            return 0.0
        
        # λ(t) = (β/η) * (t/η)^(β-1)
        hazard = (shape / scale) * np.power(time / scale, shape - 1.0)
        return max(0.0, hazard)
    
    def cumulative_hazard(self, time: float, params: Dict[str, Any]) -> float:
        """Compute cumulative Weibull hazard."""
        shape = params.get('shape', 2.0)
        scale = params.get('scale', 3600.0)
        
        if time <= 0:
            return 0.0
        
        if shape <= 0 or scale <= 0:
            return 0.0
        
        # H(t) = (t/η)^β
        return np.power(time / scale, shape)
    
    def sample_fault_time(self, params: Dict[str, Any], rng: Optional[np.random.Generator] = None) -> float:
        """Sample from Weibull distribution."""
        shape = params.get('shape', 2.0)
        scale = params.get('scale', 3600.0)
        
        if rng is None:
            rng = np.random.default_rng()
        
        # Sample from Weibull distribution
        return stats.weibull_min.rvs(shape, scale=scale, random_state=rng)


class ExponentialFaultModel(TimeDependentFaultModel):
    """
    Exponential distribution for constant-hazard faults.
    
    Hazard rate: λ(t) = λ (constant)
    - Rate parameter (λ): constant failure rate
    """
    
    def hazard_rate(self, time: float, params: Dict[str, Any]) -> float:
        """Compute exponential hazard rate (constant)."""
        rate = params.get('rate', 0.0001)  # per second
        return max(0.0, rate)
    
    def cumulative_hazard(self, time: float, params: Dict[str, Any]) -> float:
        """Compute cumulative exponential hazard."""
        rate = params.get('rate', 0.0001)
        return max(0.0, rate * time)
    
    def sample_fault_time(self, params: Dict[str, Any], rng: Optional[np.random.Generator] = None) -> float:
        """Sample from exponential distribution."""
        rate = params.get('rate', 0.0001)
        
        if rng is None:
            rng = np.random.default_rng()
        
        # Sample from exponential distribution
        return stats.expon.rvs(scale=1.0/rate if rate > 0 else np.inf, random_state=rng)


class PoissonFaultProcess:
    """
    Poisson process for random fault arrivals.
    
    Models random fault occurrences with constant or time-varying rate.
    """
    
    def __init__(self, rate: float = 0.0001, time_varying: bool = False):
        """
        Initialize Poisson fault process.
        
        Args:
            rate: Constant rate (faults per second) or initial rate if time_varying
            time_varying: If True, rate can vary over time
        """
        self._base_rate = rate
        self._time_varying = time_varying
    
    def sample_inter_arrival_time(self, current_time: float = 0.0, rng: Optional[np.random.Generator] = None) -> float:
        """
        Sample inter-arrival time (time until next fault).
        
        Args:
            current_time: Current simulation time
            rng: Random number generator
            
        Returns:
            Inter-arrival time in seconds
        """
        if rng is None:
            rng = np.random.default_rng()
        
        rate = self._get_rate(current_time)
        if rate <= 0:
            return np.inf
        
        # Inter-arrival times follow exponential distribution
        return stats.expon.rvs(scale=1.0/rate, random_state=rng)
    
    def sample_fault_times(self, duration: float, start_time: float = 0.0, 
                          rng: Optional[np.random.Generator] = None) -> np.ndarray:
        """
        Sample all fault arrival times within duration.
        
        Args:
            duration: Duration in seconds
            start_time: Start time
            rng: Random number generator
            
        Returns:
            Array of fault arrival times
        """
        if rng is None:
            rng = np.random.default_rng()
        
        fault_times = []
        current_time = start_time
        
        while current_time < start_time + duration:
            inter_arrival = self.sample_inter_arrival_time(current_time, rng)
            next_fault_time = current_time + inter_arrival
            
            if next_fault_time > start_time + duration:
                break
            
            fault_times.append(next_fault_time)
            current_time = next_fault_time
        
        return np.array(fault_times)
    
    def _get_rate(self, time: float) -> float:
        """Get rate at time t (can be overridden for time-varying rates)."""
        if self._time_varying:
            # Example: increasing rate over time
            # Can be customized
            return self._base_rate * (1.0 + time / 3600.0)  # Increase by 1x per hour
        return self._base_rate
    
    def set_rate_function(self, rate_func):
        """Set custom rate function for time-varying rates."""
        self._get_rate = rate_func


class MarkovFaultChain:
    """
    Markov chain for fault state transitions.
    
    Models fault progression through discrete states (e.g., normal -> degraded -> failed).
    """
    
    def __init__(self, transition_matrix: np.ndarray, states: list):
        """
        Initialize Markov fault chain.
        
        Args:
            transition_matrix: State transition probability matrix (n_states x n_states)
            states: List of state names
        """
        self._transition_matrix = np.array(transition_matrix)
        self._states = states
        self._n_states = len(states)
        
        # Validate transition matrix
        if self._transition_matrix.shape != (self._n_states, self._n_states):
            raise ValueError("Transition matrix must be square with size matching number of states")
        
        # Each row should sum to 1.0 (or close to it)
        row_sums = self._transition_matrix.sum(axis=1)
        if not np.allclose(row_sums, 1.0):
            raise ValueError("Each row of transition matrix must sum to 1.0")
    
    def get_next_state(self, current_state: int, rng: Optional[np.random.Generator] = None) -> int:
        """
        Sample next state given current state.
        
        Args:
            current_state: Current state index
            rng: Random number generator
            
        Returns:
            Next state index
        """
        if rng is None:
            rng = np.random.default_rng()
        
        if current_state < 0 or current_state >= self._n_states:
            raise ValueError(f"Invalid state index: {current_state}")
        
        # Sample from transition probabilities
        probs = self._transition_matrix[current_state, :]
        return rng.choice(self._n_states, p=probs)
    
    def get_state_probabilities(self, initial_state: int, n_steps: int) -> np.ndarray:
        """
        Compute state probabilities after n_steps.
        
        Args:
            initial_state: Initial state index
            n_steps: Number of steps
            
        Returns:
            Array of state probabilities
        """
        # Initial state vector (one-hot)
        state_vec = np.zeros(self._n_states)
        state_vec[initial_state] = 1.0
        
        # Multiply by transition matrix n_steps times
        for _ in range(n_steps):
            state_vec = state_vec @ self._transition_matrix
        
        return state_vec
    
    @property
    def states(self) -> list:
        """Get list of state names."""
        return self._states.copy()
    
    @property
    def transition_matrix(self) -> np.ndarray:
        """Get transition matrix."""
        return self._transition_matrix.copy()

