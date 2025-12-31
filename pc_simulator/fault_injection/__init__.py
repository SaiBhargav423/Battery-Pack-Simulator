"""
Fault Injection Framework for BMS Simulation Testing

This package provides comprehensive fault injection capabilities with:
- Monte Carlo simulation (LHS, Sobol sequences)
- Time-dependent probabilistic models (Weibull, Poisson)
- Correlated fault modeling (copulas)
- Statistical analysis and convergence monitoring
- Optional Bayesian inference for online diagnosis
"""

from .fault_types import FaultType, FaultCategory
from .fault_framework import FaultInjector
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
    apply_overdischarge
)
from .monte_carlo import (
    MonteCarloFaultInjector,
    SamplingStrategy,
    LatinHypercubeSampler,
    SobolSequenceSampler,
    RandomSampler,
    EnsembleStatistics
)
from .probabilistic_models import (
    TimeDependentFaultModel,
    WeibullFaultModel,
    ExponentialFaultModel,
    PoissonFaultProcess,
    MarkovFaultChain
)
from .copula_models import (
    CopulaModel,
    GaussianCopula,
    ArchimedeanCopula,
    ThermalPropagationCopula
)
from .statistical_analysis import (
    EnsembleAnalyzer,
    ConvergenceMonitor,
    SensitivityAnalyzer,
    RiskQuantifier
)
from .bayesian_inference import (
    BayesianFaultDiagnosis,
    ParticleFilter,
    BayesianNetwork,
    AdaptiveTestPlanner
)
from .fault_scenarios import load_scenario, save_scenario

__all__ = [
    # Core types
    'FaultType',
    'FaultCategory',
    'FaultInjector',
    # Fault models
    'apply_internal_short_circuit',
    'apply_external_short_circuit',
    'apply_capacity_fade',
    'apply_resistance_increase',
    'apply_thermal_runaway',
    'apply_cell_imbalance',
    'apply_open_circuit',
    'apply_leakage_current',
    'apply_overcharge',
    'apply_overdischarge',
    # Monte Carlo
    'MonteCarloFaultInjector',
    'SamplingStrategy',
    'LatinHypercubeSampler',
    'SobolSequenceSampler',
    'RandomSampler',
    'EnsembleStatistics',
    # Probabilistic models
    'TimeDependentFaultModel',
    'WeibullFaultModel',
    'ExponentialFaultModel',
    'PoissonFaultProcess',
    'MarkovFaultChain',
    # Copula models
    'CopulaModel',
    'GaussianCopula',
    'ArchimedeanCopula',
    'ThermalPropagationCopula',
    # Statistical analysis
    'EnsembleAnalyzer',
    'ConvergenceMonitor',
    'SensitivityAnalyzer',
    'RiskQuantifier',
    # Bayesian inference
    'BayesianFaultDiagnosis',
    'ParticleFilter',
    'BayesianNetwork',
    'AdaptiveTestPlanner',
    # Scenarios
    'load_scenario',
    'save_scenario',
]

