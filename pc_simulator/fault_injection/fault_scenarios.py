"""
Fault Scenario Loading and Management

This module provides functions to load and save fault scenarios from YAML files.
"""

import yaml
import numpy as np
from typing import Dict, Any, Optional, List
from pathlib import Path
from .fault_types import FaultType
from .fault_framework import FaultInjector, FaultMode
from .probabilistic_models import WeibullFaultModel, ExponentialFaultModel, PoissonFaultProcess


def load_scenario(yaml_file: str) -> Dict[str, Any]:
    """
    Load fault scenario from YAML file.
    
    Args:
        yaml_file: Path to YAML scenario file
        
    Returns:
        Scenario dictionary
    """
    with open(yaml_file, 'r') as f:
        scenario = yaml.safe_load(f)
    
    return scenario


def save_scenario(scenario: Dict[str, Any], yaml_file: str):
    """
    Save fault scenario to YAML file.
    
    Args:
        scenario: Scenario dictionary
        yaml_file: Path to output YAML file
    """
    with open(yaml_file, 'w') as f:
        yaml.dump(scenario, f, default_flow_style=False, sort_keys=False)


def create_fault_injector_from_scenario(scenario: Dict[str, Any],
                                       seed: Optional[int] = None) -> FaultInjector:
    """
    Create FaultInjector from scenario dictionary.
    
    Args:
        scenario: Scenario dictionary
        seed: Random seed
        
    Returns:
        Configured FaultInjector
    """
    # Determine mode
    mode_str = scenario.get('mode', 'deterministic').lower()
    mode = FaultMode.DETERMINISTIC if mode_str == 'deterministic' else FaultMode.PROBABILISTIC
    
    # Get seed from scenario or parameter
    scenario_seed = scenario.get('seed', seed)
    if scenario_seed is None and mode == FaultMode.DETERMINISTIC:
        scenario_seed = 42  # Default seed for deterministic
    
    # Create fault injector
    injector = FaultInjector(mode=mode, seed=scenario_seed)
    
    # Enable Monte Carlo if specified
    mc_config = scenario.get('monte_carlo')
    if mc_config:
        sampling_strategy = mc_config.get('sampling_strategy', 'lhs')
        injector.enable_monte_carlo(sampling_strategy, scenario_seed)
    
    # Enable Bayesian if specified
    bayesian_config = scenario.get('bayesian')
    if bayesian_config and bayesian_config.get('enabled', False):
        prior_prob = bayesian_config.get('prior_probability', 0.01)
        injector.enable_bayesian(prior_prob)
    
    # Load faults
    faults = scenario.get('faults', [])
    for fault_config in faults:
        fault_type_str = fault_config.get('type')
        fault_type = FaultType.from_string(fault_type_str)
        
        target = fault_config.get('target', 0)
        if isinstance(target, str) and target.startswith('cell_'):
            target = int(target.split('_')[1])
        
        parameters = fault_config.get('parameters', {})
        timing = fault_config.get('timing', {})
        
        # Handle probabilistic parameters
        if mode == FaultMode.PROBABILISTIC:
            # Convert distribution specifications to sampled values
            sampled_params = {}
            for param_name, param_value in parameters.items():
                if isinstance(param_value, dict) and 'distribution' in param_value:
                    # Sample from distribution
                    dist_type = param_value.get('distribution')
                    if dist_type == 'uniform':
                        min_val = param_value.get('min', 0.0)
                        max_val = param_value.get('max', 1.0)
                        sampled_params[param_name] = injector._rng.uniform(min_val, max_val)
                    elif dist_type == 'normal':
                        mean = param_value.get('mean', 0.0)
                        std = param_value.get('std', 1.0)
                        sampled_params[param_name] = injector._rng.normal(mean, std)
                    else:
                        sampled_params[param_name] = param_value
                else:
                    sampled_params[param_name] = param_value
            parameters = sampled_params
        
        # Handle timing models
        if timing and 'trigger_model' in timing:
            trigger_model = timing['trigger_model']
            if trigger_model == 'weibull':
                # Create Weibull model for timing
                shape = timing.get('shape', 1.5)
                scale = timing.get('scale', 3600.0)
                timing['trigger_params'] = {'shape': shape, 'scale': scale}
            elif trigger_model == 'poisson':
                rate = timing.get('rate', 0.0001)
                timing['trigger_params'] = {'rate': rate}
        
        # Inject fault
        injector.inject_fault(fault_type, target, parameters, timing)
    
    # Load correlations
    correlations = scenario.get('correlations', [])
    for corr_config in correlations:
        corr_type = corr_config.get('type')
        if corr_type == 'thermal_propagation':
            cells = corr_config.get('cells', [])
            correlation_matrix = corr_config.get('correlation_matrix')
            if correlation_matrix:
                from .copula_models import GaussianCopula
                copula = GaussianCopula(np.array(correlation_matrix))
                injector._copula_models['thermal_propagation'] = copula
    
    return injector


def validate_scenario(scenario: Dict[str, Any]) -> List[str]:
    """
    Validate scenario configuration.
    
    Args:
        scenario: Scenario dictionary
        
    Returns:
        List of validation errors (empty if valid)
    """
    errors = []
    
    # Check required fields
    if 'name' not in scenario:
        errors.append("Missing required field: 'name'")
    
    if 'faults' not in scenario:
        errors.append("Missing required field: 'faults'")
    
    # Validate faults
    faults = scenario.get('faults', [])
    for i, fault in enumerate(faults):
        if 'type' not in fault:
            errors.append(f"Fault {i}: Missing 'type' field")
        else:
            try:
                FaultType.from_string(fault['type'])
            except ValueError as e:
                errors.append(f"Fault {i}: Invalid fault type: {e}")
    
    # Validate mode
    mode = scenario.get('mode', 'deterministic')
    if mode not in ['deterministic', 'probabilistic']:
        errors.append(f"Invalid mode: {mode}. Must be 'deterministic' or 'probabilistic'")
    
    return errors

