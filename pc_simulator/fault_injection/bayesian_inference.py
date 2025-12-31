"""
Bayesian Inference for Fault Diagnosis

This module provides Bayesian methods for:
- Online fault detection (Bayesian updates)
- Fault state tracking (particle filters)
- Parameter estimation
- Adaptive test planning
"""

import numpy as np
from typing import Dict, Any, List, Optional, Tuple, Callable
from scipy import stats
from scipy.stats import norm
import warnings


class BayesianFaultDiagnosis:
    """
    Bayesian inference for fault diagnosis.
    
    Updates fault probability given observations using Bayes' theorem.
    """
    
    def __init__(self, prior_probability: float = 0.01):
        """
        Initialize Bayesian fault diagnosis.
        
        Args:
            prior_probability: Prior probability of fault (default: 1%)
        """
        self._prior_prob = prior_probability
        self._current_prob = prior_probability
        self._observation_history = []
    
    def update_fault_probability(self, observation: Dict[str, Any],
                                 likelihood_func: Callable) -> float:
        """
        Update fault probability given observation using Bayes' theorem.
        
        P(fault | observation) = P(observation | fault) * P(fault) / P(observation)
        
        Args:
            observation: Observation dictionary (e.g., voltage, temperature)
            likelihood_func: Function that computes P(observation | fault)
            
        Returns:
            Updated fault probability
        """
        # Compute likelihood: P(observation | fault)
        likelihood_fault = likelihood_func(observation, fault=True)
        
        # Compute likelihood: P(observation | no fault)
        likelihood_no_fault = likelihood_func(observation, fault=False)
        
        # Prior probabilities
        p_fault = self._current_prob
        p_no_fault = 1.0 - p_fault
        
        # Evidence (normalization constant)
        evidence = likelihood_fault * p_fault + likelihood_no_fault * p_no_fault
        
        if evidence == 0:
            return self._current_prob
        
        # Posterior probability
        posterior = (likelihood_fault * p_fault) / evidence
        
        # Update current probability
        self._current_prob = posterior
        self._observation_history.append({
            'observation': observation,
            'posterior_prob': posterior
        })
        
        return posterior
    
    def reset(self, prior_probability: Optional[float] = None):
        """Reset to prior probability."""
        if prior_probability is not None:
            self._prior_prob = prior_probability
        self._current_prob = self._prior_prob
        self._observation_history = []
    
    @property
    def current_probability(self) -> float:
        """Get current fault probability."""
        return self._current_prob
    
    @property
    def observation_history(self) -> List[Dict[str, Any]]:
        """Get observation history."""
        return self._observation_history.copy()


class ParticleFilter:
    """
    Particle filter for fault state tracking.
    
    Tracks hidden fault states (e.g., internal short resistance) using
    sequential Monte Carlo methods.
    """
    
    def __init__(self, n_particles: int = 100, state_dim: int = 1,
                 initial_state_dist: Optional[stats.rv_continuous] = None):
        """
        Initialize particle filter.
        
        Args:
            n_particles: Number of particles
            state_dim: Dimension of state vector
            initial_state_dist: Initial state distribution
        """
        self._n_particles = n_particles
        self._state_dim = state_dim
        
        # Initialize particles
        if initial_state_dist is None:
            initial_state_dist = stats.norm(loc=0.0, scale=1.0)
        
        self._particles = initial_state_dist.rvs(size=(n_particles, state_dim))
        self._weights = np.ones(n_particles) / n_particles
        self._rng = np.random.default_rng()
    
    def predict(self, transition_func: Callable, process_noise: float = 0.1):
        """
        Prediction step: propagate particles through state transition.
        
        Args:
            transition_func: Function that predicts next state given current state
            process_noise: Process noise standard deviation
        """
        # Propagate each particle
        for i in range(self._n_particles):
            predicted_state = transition_func(self._particles[i])
            # Add process noise
            noise = self._rng.normal(0, process_noise, size=self._state_dim)
            self._particles[i] = predicted_state + noise
    
    def update(self, observation: Dict[str, Any], 
              likelihood_func: Callable):
        """
        Update step: reweight particles based on observation.
        
        Args:
            observation: Current observation
            likelihood_func: Function that computes likelihood P(observation | state)
        """
        # Compute likelihood for each particle
        likelihoods = np.zeros(self._n_particles)
        for i in range(self._n_particles):
            likelihoods[i] = likelihood_func(observation, self._particles[i])
        
        # Update weights: w_i = w_i * P(observation | state_i)
        self._weights *= likelihoods
        
        # Normalize weights
        weight_sum = np.sum(self._weights)
        if weight_sum > 0:
            self._weights /= weight_sum
        else:
            # Reset to uniform if all weights are zero
            self._weights = np.ones(self._n_particles) / self._n_particles
    
    def resample(self):
        """Resample particles based on weights (systematic resampling)."""
        # Systematic resampling
        n = self._n_particles
        cumulative_weights = np.cumsum(self._weights)
        u = (np.arange(n) + self._rng.random()) / n
        
        new_particles = np.zeros_like(self._particles)
        j = 0
        for i in range(n):
            while u[i] > cumulative_weights[j]:
                j += 1
            new_particles[i] = self._particles[j]
        
        self._particles = new_particles
        self._weights = np.ones(n) / n
    
    def get_state_estimate(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Get state estimate (mean and covariance).
        
        Returns:
            Tuple of (mean, covariance)
        """
        # Weighted mean
        mean = np.average(self._particles, axis=0, weights=self._weights)
        
        # Weighted covariance
        centered = self._particles - mean
        covariance = np.average(centered[:, :, np.newaxis] * centered[:, np.newaxis, :],
                               axis=0, weights=self._weights)
        
        return mean, covariance
    
    @property
    def particles(self) -> np.ndarray:
        """Get current particles."""
        return self._particles.copy()
    
    @property
    def weights(self) -> np.ndarray:
        """Get current weights."""
        return self._weights.copy()


class BayesianNetwork:
    """
    Simple Bayesian network for fault propagation.
    
    Models dependencies between faults using conditional probabilities.
    """
    
    def __init__(self, nodes: List[str], edges: List[Tuple[str, str]],
                 conditional_probs: Dict[Tuple[str, str], float]):
        """
        Initialize Bayesian network.
        
        Args:
            nodes: List of node names (faults)
            edges: List of (parent, child) edges
            conditional_probs: Dictionary mapping (parent, child) to P(child | parent)
        """
        self._nodes = nodes
        self._edges = edges
        self._conditional_probs = conditional_probs
        self._node_states = {node: False for node in nodes}
    
    def update_node_probability(self, node: str, observation: Dict[str, Any]) -> float:
        """
        Update probability of a node given observations.
        
        Args:
            node: Node name
            observation: Observation dictionary
            
        Returns:
            Updated probability
        """
        # Find parent nodes
        parents = [parent for parent, child in self._edges if child == node]
        
        # Compute probability based on parents
        if len(parents) == 0:
            # Root node: use prior
            prob = 0.01  # Default prior
        else:
            # Compute based on parent states
            prob = 0.0
            for parent in parents:
                if self._node_states.get(parent, False):
                    cond_prob = self._conditional_probs.get((parent, node), 0.1)
                    prob = max(prob, cond_prob)
        
        return prob
    
    def set_node_state(self, node: str, state: bool):
        """Set node state (fault present/absent)."""
        if node in self._node_states:
            self._node_states[node] = state
    
    def get_node_state(self, node: str) -> bool:
        """Get node state."""
        return self._node_states.get(node, False)
    
    def propagate(self, trigger_node: str):
        """
        Propagate fault from trigger node through network.
        
        Args:
            trigger_node: Node that triggers propagation
        """
        self.set_node_state(trigger_node, True)
        
        # Propagate to children
        children = [child for parent, child in self._edges if parent == trigger_node]
        for child in children:
            # Sample whether child is triggered
            cond_prob = self._conditional_probs.get((trigger_node, child), 0.1)
            if np.random.random() < cond_prob:
                self.set_node_state(child, True)
                # Recursively propagate
                self.propagate(child)


class AdaptiveTestPlanner:
    """
    Adaptive test planning based on prior results.
    
    Optimizes test strategy to maximize information gain.
    """
    
    def __init__(self, test_parameters: List[Dict[str, Any]]):
        """
        Initialize adaptive test planner.
        
        Args:
            test_parameters: List of available test parameter configurations
        """
        self._test_parameters = test_parameters
        self._test_history = []
        self._results_history = []
    
    def plan_next_test(self, objective: str = 'maximize_information') -> Dict[str, Any]:
        """
        Plan next test based on prior results.
        
        Args:
            objective: Planning objective ('maximize_information', 'target_failure', etc.)
            
        Returns:
            Recommended test configuration
        """
        if len(self._test_history) == 0:
            # First test: use default
            return self._test_parameters[0]
        
        if objective == 'maximize_information':
            # Select test that maximizes expected information gain
            # Simplified: select test with highest variance in unexplored region
            return self._select_high_variance_test()
        elif objective == 'target_failure':
            # Select test most likely to trigger failure
            return self._select_failure_targeting_test()
        else:
            # Default: random selection
            return np.random.choice(self._test_parameters)
    
    def _select_high_variance_test(self) -> Dict[str, Any]:
        """Select test with high variance (unexplored region)."""
        # Simplified: return first unused test
        used_tests = [test for test in self._test_history]
        for test in self._test_parameters:
            if test not in used_tests:
                return test
        # All tests used: return random
        return np.random.choice(self._test_parameters)
    
    def _select_failure_targeting_test(self) -> Dict[str, Any]:
        """Select test targeting failure conditions."""
        # Simplified: return test with extreme parameters
        # In practice, would use optimization to find parameters
        # that maximize failure probability
        return self._test_parameters[-1]  # Assume last is most extreme
    
    def record_result(self, test_config: Dict[str, Any], result: Dict[str, Any]):
        """Record test result."""
        self._test_history.append(test_config)
        self._results_history.append(result)
    
    @property
    def test_history(self) -> List[Dict[str, Any]]:
        """Get test history."""
        return self._test_history.copy()

