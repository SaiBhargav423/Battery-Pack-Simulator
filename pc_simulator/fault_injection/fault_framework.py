"""
Core Fault Injection Framework

This module provides the main FaultInjector class that integrates:
- Monte Carlo sampling
- Time-dependent probabilities
- Correlated fault modeling
- Bayesian inference (optional)
"""

import numpy as np
from typing import Dict, Any, Optional, List, Tuple, Callable, Union
from enum import Enum
import time

from .fault_types import FaultType, FaultCategory
from .fault_models import (
    apply_internal_short_circuit,
    apply_external_short_circuit,
    apply_capacity_fade,
    apply_resistance_increase,
    apply_thermal_runaway,
    apply_cell_imbalance,
    apply_open_circuit,
    apply_leakage_current,
    apply_overcharge,
    apply_overdischarge,
    clear_fault,
    clear_all_faults
)
from .monte_carlo import MonteCarloFaultInjector, SamplingStrategy
from .probabilistic_models import (
    TimeDependentFaultModel,
    WeibullFaultModel,
    ExponentialFaultModel,
    PoissonFaultProcess
)
from .copula_models import CopulaModel, GaussianCopula, ThermalPropagationCopula
from .statistical_analysis import EnsembleAnalyzer, ConvergenceMonitor
from .bayesian_inference import BayesianFaultDiagnosis, ParticleFilter


class FaultMode(Enum):
    """Fault injection mode."""
    DETERMINISTIC = "deterministic"
    PROBABILISTIC = "probabilistic"


class FaultState:
    """Tracks active fault state."""
    
    def __init__(self, fault_type: FaultType, target: Union[int, str],
                 parameters: Dict[str, Any], timing: Optional[Dict[str, Any]] = None):
        """
        Initialize fault state.
        
        Args:
            fault_type: Type of fault
            target: Target cell index or 'pack' for pack-level faults
            parameters: Fault parameters
            timing: Timing configuration (trigger time, duration, etc.)
        """
        self.fault_type = fault_type
        self.target = target
        self.parameters = parameters
        self.timing = timing or {}
        self.active = False
        self.triggered = False
        self.trigger_time = None
        self.clear_time = None


class FaultInjector:
    """
    Main fault injection framework.
    
    Integrates all probabilistic methods for comprehensive fault injection.
    """
    
    def __init__(self, mode: FaultMode = FaultMode.DETERMINISTIC, seed: Optional[int] = None):
        """
        Initialize fault injector.
        
        Args:
            mode: Deterministic or probabilistic mode
            seed: Random seed for reproducibility
        """
        self._mode = mode
        self._seed = seed
        self._rng = np.random.default_rng(seed)
        
        # Fault states
        self._fault_states: List[FaultState] = []
        self._active_faults: Dict[str, FaultState] = {}
        
        # Monte Carlo support
        self._monte_carlo: Optional[MonteCarloFaultInjector] = None
        
        # Time-dependent models
        self._time_models: Dict[str, TimeDependentFaultModel] = {}
        
        # Copula models for correlated faults
        self._copula_models: Dict[str, CopulaModel] = {}
        
        # Bayesian inference (optional)
        self._bayesian_enabled = False
        self._bayesian_diagnosis: Optional[BayesianFaultDiagnosis] = None
        self._particle_filters: Dict[str, ParticleFilter] = {}
        
        # Simulation state
        self._simulation_start_time = None
        self._current_time = 0.0
        
        # Statistics
        self._fault_injection_count = 0
        self._fault_clear_count = 0
    
    def set_mode(self, mode: FaultMode, seed: Optional[int] = None):
        """Set fault injection mode."""
        self._mode = mode
        if seed is not None:
            self._seed = seed
            self._rng = np.random.default_rng(seed)
    
    def enable_monte_carlo(self, sampling_strategy: str = 'lhs', seed: Optional[int] = None):
        """Enable Monte Carlo framework."""
        mc_seed = seed if seed is not None else self._seed
        self._monte_carlo = MonteCarloFaultInjector(sampling_strategy, mc_seed)
    
    def enable_bayesian(self, prior_probability: float = 0.01):
        """Enable Bayesian inference."""
        self._bayesian_enabled = True
        self._bayesian_diagnosis = BayesianFaultDiagnosis(prior_probability)
    
    def inject_fault(self, fault_type: FaultType, target: Union[int, str],
                    parameters: Dict[str, Any], timing: Optional[Dict[str, Any]] = None) -> str:
        """
        Inject fault with timing control.
        
        Args:
            fault_type: Type of fault
            target: Target cell index (0-15) or 'pack' for pack-level
            parameters: Fault parameters
            timing: Timing configuration:
                - trigger_time_sec: Time to trigger fault
                - trigger_soc: SOC to trigger fault
                - duration_sec: Duration of fault (None = permanent)
                - trigger_model: 'weibull', 'exponential', 'poisson'
                - trigger_params: Parameters for trigger model
        
        Returns:
            Fault ID string
        """
        fault_id = f"{fault_type.value}_{target}_{self._fault_injection_count}"
        
        fault_state = FaultState(fault_type, target, parameters, timing)
        self._fault_states.append(fault_state)
        self._fault_injection_count += 1
        
        return fault_id
    
    def inject_fault_probabilistic(self, fault_type: FaultType, target: Union[int, str],
                                  params_dist: Dict[str, Any],
                                  time_model: Optional[TimeDependentFaultModel] = None) -> str:
        """
        Inject fault with probabilistic parameters.
        
        Args:
            fault_type: Type of fault
            target: Target cell index or 'pack'
            params_dist: Parameter distributions (e.g., {'resistance_ohm': {'distribution': 'uniform', 'min': 0.01, 'max': 0.1}})
            time_model: Optional time-dependent model for fault timing
        
        Returns:
            Fault ID string
        """
        # Sample parameters from distributions
        sampled_params = {}
        for param_name, param_dist in params_dist.items():
            if isinstance(param_dist, dict):
                dist_type = param_dist.get('distribution', 'uniform')
                if dist_type == 'uniform':
                    min_val = param_dist.get('min', 0.0)
                    max_val = param_dist.get('max', 1.0)
                    sampled_params[param_name] = self._rng.uniform(min_val, max_val)
                elif dist_type == 'normal':
                    mean = param_dist.get('mean', 0.0)
                    std = param_dist.get('std', 1.0)
                    sampled_params[param_name] = self._rng.normal(mean, std)
                elif dist_type == 'weibull':
                    shape = param_dist.get('shape', 2.0)
                    scale = param_dist.get('scale', 1.0)
                    from scipy.stats import weibull_min
                    sampled_params[param_name] = weibull_min.rvs(shape, scale=scale, random_state=self._rng)
                else:
                    sampled_params[param_name] = param_dist
            else:
                sampled_params[param_name] = param_dist
        
        # Sample trigger time if time model provided
        timing = None
        if time_model is not None:
            trigger_time = time_model.sample_fault_time({}, self._rng)
            timing = {'trigger_time_sec': trigger_time}
        
        return self.inject_fault(fault_type, target, sampled_params, timing)
    
    def inject_correlated_faults(self, fault_group: List[Dict[str, Any]],
                               copula_model: CopulaModel) -> List[str]:
        """
        Inject correlated faults using copula model.
        
        Args:
            fault_group: List of fault configurations
            copula_model: Copula model for dependency
        
        Returns:
            List of fault IDs
        """
        # Sample correlated parameters
        n_faults = len(fault_group)
        uniform_samples = copula_model.sample(n_faults, self._rng)
        
        fault_ids = []
        for i, fault_config in enumerate(fault_group):
            fault_type = FaultType.from_string(fault_config['type'])
            target = fault_config.get('target', 0)
            
            # Transform uniform samples to parameter distributions
            # (Simplified - in practice would use proper marginal transformations)
            parameters = fault_config.get('parameters', {})
            for param_name, param_value in parameters.items():
                if isinstance(param_value, dict) and 'distribution' in param_value:
                    # Use copula sample to transform
                    # This is simplified - full implementation would use proper marginals
                    pass
            
            fault_id = self.inject_fault(fault_type, target, parameters)
            fault_ids.append(fault_id)
        
        return fault_ids
    
    def update(self, simulation_time_ms: float, pack_state: Optional[Dict[str, Any]] = None):
        """
        Update fault injector (check scheduled faults, update time-dependent faults).
        
        Args:
            simulation_time_ms: Current simulation time in milliseconds
            pack_state: Optional pack state dictionary (for SOC-based triggering)
        """
        self._current_time = simulation_time_ms / 1000.0  # Convert to seconds
        
        # Check and trigger scheduled faults
        for fault_state in self._fault_states:
            if fault_state.triggered:
                continue
            
            # Check trigger conditions
            should_trigger = False
            
            if fault_state.timing:
                # Time-based trigger
                trigger_time = fault_state.timing.get('trigger_time_sec')
                if trigger_time is not None and self._current_time >= trigger_time:
                    should_trigger = True
                
                # SOC-based trigger (for non-overcharge faults)
                trigger_soc = fault_state.timing.get('trigger_soc')
                if trigger_soc is not None and pack_state:
                    current_soc = pack_state.get('pack_soc_pct', 50.0)
                    # For overcharge, use voltage-based trigger instead (see below)
                    # For other faults (discharge), trigger when SOC <= threshold
                    if fault_state.fault_type != FaultType.OVERCHARGE:
                        if current_soc <= trigger_soc:
                            should_trigger = True
                
                # Overcharge trigger: can trigger on voltage >= 3.65V OR SOC >= 100%
                # Check trigger_condition in timing to determine which condition(s) to check
                if fault_state.fault_type == FaultType.OVERCHARGE and pack_state:
                    cell_voltages_mv = pack_state.get('cell_voltages_mv', [])
                    cell_socs_pct = pack_state.get('cell_socs_pct', [])
                    current_soc = pack_state.get('pack_soc_pct', 50.0)
                    
                    # Get trigger condition from timing config
                    # "soc" = only check SOC, "voltage" = only check voltage, "both" or None = check both
                    trigger_condition = fault_state.timing.get('trigger_condition', 'both')
                    
                    # Check voltage condition (if trigger_condition is "voltage" or "both")
                    if trigger_condition in ['voltage', 'both']:
                        voltage_limit_mv = 3650.0  # 3.65V overvoltage limit
                        if isinstance(fault_state.target, int) and 0 <= fault_state.target < len(cell_voltages_mv):
                            target_cell_voltage_mv = cell_voltages_mv[fault_state.target]
                            if target_cell_voltage_mv >= voltage_limit_mv:
                                should_trigger = True
                    
                    # Check SOC condition (if trigger_condition is "soc" or "both")
                    if trigger_condition in ['soc', 'both']:
                        # Check target cell SOC first (preferred), then pack SOC as fallback
                        if isinstance(fault_state.target, int) and 0 <= fault_state.target < len(cell_socs_pct):
                            target_cell_soc = cell_socs_pct[fault_state.target]
                            # Use 99.99 to account for floating point precision
                            if target_cell_soc >= 99.99:
                                should_trigger = True
                        # Fallback to pack SOC if cell SOC not available
                        elif current_soc >= 99.99:
                            should_trigger = True
                
                # Probabilistic trigger
                trigger_model = fault_state.timing.get('trigger_model')
                if trigger_model and not should_trigger:
                    if trigger_model == 'weibull':
                        model = WeibullFaultModel()
                        params = fault_state.timing.get('trigger_params', {})
                        prob = model.probability(self._current_time, params)
                        if self._rng.random() < prob:
                            should_trigger = True
                    elif trigger_model == 'poisson':
                        rate = fault_state.timing.get('rate', 0.0001)
                        process = PoissonFaultProcess(rate)
                        # Simplified: check if fault should occur
                        prob = 1.0 - np.exp(-rate * self._current_time)
                        if self._rng.random() < prob:
                            should_trigger = True
            
            if should_trigger:
                fault_state.active = True
                fault_state.triggered = True
                fault_state.trigger_time = self._current_time
                
                # Set clear time if duration specified
                duration = fault_state.timing.get('duration_sec')
                if duration is not None:
                    fault_state.clear_time = self._current_time + duration
                
                fault_key = f"{fault_state.fault_type.value}_{fault_state.target}"
                self._active_faults[fault_key] = fault_state
        
        # Check and clear expired faults
        to_clear = []
        for fault_key, fault_state in self._active_faults.items():
            if fault_state.clear_time is not None and self._current_time >= fault_state.clear_time:
                fault_state.active = False
                to_clear.append(fault_key)
                self._fault_clear_count += 1
        
        for key in to_clear:
            del self._active_faults[key]
    
    def apply_to_cell(self, cell, cell_index: int):
        """Apply active faults to cell."""
        for fault_key, fault_state in self._active_faults.items():
            if not fault_state.active:
                continue
            
            if fault_state.target != cell_index and fault_state.target != 'all':
                continue
            
            # Apply fault based on type
            fault_type = fault_state.fault_type
            params = fault_state.parameters
            
            # Calculate fault duration for time-dependent effects
            fault_duration_sec = 0.0
            if fault_state.trigger_time is not None:
                fault_duration_sec = self._current_time - fault_state.trigger_time
            
            if fault_type == FaultType.INTERNAL_SHORT_CIRCUIT_HARD:
                # Pass degradation parameters if available
                degradation_rate = params.get('degradation_rate', 0.0001)
                min_resistance = params.get('min_resistance_ohm', 0.001)
                apply_internal_short_circuit(
                    cell, 
                    params.get('resistance_ohm', 0.1),
                    current_time=self._current_time,
                    degradation_rate=degradation_rate,
                    min_resistance_ohm=min_resistance
                )
                # Update fault duration in cell's fault state
                if hasattr(cell, '_fault_state') and 'internal_short' in cell._fault_state:
                    cell._fault_state['internal_short']['fault_duration_sec'] = fault_duration_sec
                    if 'fault_start_time' not in cell._fault_state['internal_short']:
                        cell._fault_state['internal_short']['fault_start_time'] = fault_state.trigger_time or 0.0
            elif fault_type == FaultType.INTERNAL_SHORT_CIRCUIT_SOFT:
                degradation_rate = params.get('degradation_rate', 0.00005)  # Slower for soft shorts
                min_resistance = params.get('min_resistance_ohm', 10.0)  # Higher minimum for soft shorts
                apply_internal_short_circuit(
                    cell,
                    params.get('resistance_ohm', 500.0),
                    current_time=self._current_time,
                    degradation_rate=degradation_rate,
                    min_resistance_ohm=min_resistance
                )
                # Update fault duration
                if hasattr(cell, '_fault_state') and 'internal_short' in cell._fault_state:
                    cell._fault_state['internal_short']['fault_duration_sec'] = fault_duration_sec
                    if 'fault_start_time' not in cell._fault_state['internal_short']:
                        cell._fault_state['internal_short']['fault_start_time'] = fault_state.trigger_time or 0.0
            elif fault_type == FaultType.CAPACITY_FADE:
                apply_capacity_fade(cell, params.get('fade_factor', 0.9))
            elif fault_type == FaultType.RESISTANCE_INCREASE:
                apply_resistance_increase(cell, params.get('resistance_multiplier', 1.5))
            elif fault_type == FaultType.THERMAL_RUNAWAY:
                apply_thermal_runaway(cell, params.get('escalation_factor', 1.1))
            elif fault_type == FaultType.OPEN_CIRCUIT:
                apply_open_circuit(cell, params.get('resistance_ohm', 1e6))
            elif fault_type == FaultType.ABNORMAL_SELF_DISCHARGE:
                apply_leakage_current(cell, params.get('leakage_current_ma', 10.0))
            elif fault_type == FaultType.OVERCHARGE:
                apply_overcharge(cell, params.get('voltage_limit_mv', 3700.0))
            elif fault_type == FaultType.OVERDISCHARGE:
                apply_overdischarge(cell, params.get('voltage_limit_mv', 2500.0))
    
    def apply_to_pack(self, pack):
        """Apply active pack-level faults."""
        for fault_key, fault_state in self._active_faults.items():
            if not fault_state.active:
                continue
            
            if fault_state.target != 'pack':
                continue
            
            fault_type = fault_state.fault_type
            params = fault_state.parameters
            
            if fault_type == FaultType.EXTERNAL_SHORT_CIRCUIT:
                apply_external_short_circuit(pack, params.get('resistance_ohm', 0.05))
            elif fault_type == FaultType.CELL_IMBALANCE:
                cell_indices = params.get('cell_indices', list(range(16)))
                apply_cell_imbalance(pack, cell_indices,
                                   params.get('soc_variation_pct', 5.0),
                                   params.get('capacity_variation_pct', 2.0))
    
    def update_time_dependent_faults(self, simulation_time_ms: float, pack_state: Dict[str, Any]):
        """Update time-dependent fault parameters."""
        # This would update fault parameters based on time evolution
        # For now, handled in update() method
        pass
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get fault injection statistics."""
        return {
            'fault_injection_count': self._fault_injection_count,
            'fault_clear_count': self._fault_clear_count,
            'active_faults': len(self._active_faults),
            'total_faults': len(self._fault_states),
            'current_time_sec': self._current_time
        }
    
    def reset(self):
        """Reset fault injector."""
        self._fault_states = []
        self._active_faults = {}
        self._fault_injection_count = 0
        self._fault_clear_count = 0
        self._current_time = 0.0
        self._simulation_start_time = None

