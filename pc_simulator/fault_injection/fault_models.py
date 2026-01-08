"""
Fault Model Application Functions

This module provides functions to apply various fault types to cell and pack models.
All functions support probabilistic parameters and time-dependent evolution.
"""

import numpy as np
from typing import Dict, Any, Optional, List, Union, Callable

# Import at runtime - these should be available
try:
    from plant.cell_model import LiFePO4Cell
    from plant.pack_model import BatteryPack16S
except ImportError:
    # For type hints only if import fails
    LiFePO4Cell = None
    BatteryPack16S = None

from .fault_types import FaultType


def apply_internal_short_circuit(cell, resistance_ohm: float,
                                 time_evolution: Optional[Callable] = None,
                                 current_time: float = 0.0,
                                 degradation_rate: float = 0.0001,
                                 min_resistance_ohm: float = 0.001) -> None:
    """
    Apply internal short circuit fault to cell.
    
    Adds parallel resistance R_short across cell terminals with time-dependent degradation.
    
    Args:
        cell: Cell model to modify
        resistance_ohm: Initial short circuit resistance (0.01-1Ω for hard, 100-1000Ω for soft)
        time_evolution: Optional function(time) -> resistance_ohm for time-dependent evolution
        current_time: Current simulation time
        degradation_rate: Resistance degradation rate per second (default: 0.0001)
        min_resistance_ohm: Minimum resistance to prevent division by zero (default: 0.001Ω)
    """
    if time_evolution is not None:
        resistance_ohm = time_evolution(current_time)
    
    # Store fault state in cell (will need to modify cell model to support this)
    if not hasattr(cell, '_fault_state'):
        cell._fault_state = {}
    
    # Initialize or update fault state
    if 'internal_short' not in cell._fault_state:
        cell._fault_state['internal_short'] = {
            'resistance_ohm': max(min_resistance_ohm, resistance_ohm),
            'active': True,
            'fault_start_time': current_time,
            'fault_duration_sec': 0.0,
            'degradation_rate': degradation_rate,
            'min_resistance_ohm': min_resistance_ohm,
            'initial_resistance_ohm': resistance_ohm
        }
    else:
        # Update existing fault state
        cell._fault_state['internal_short']['active'] = True
        if 'initial_resistance_ohm' not in cell._fault_state['internal_short']:
            cell._fault_state['internal_short']['initial_resistance_ohm'] = resistance_ohm
        if 'degradation_rate' not in cell._fault_state['internal_short']:
            cell._fault_state['internal_short']['degradation_rate'] = degradation_rate
        if 'min_resistance_ohm' not in cell._fault_state['internal_short']:
            cell._fault_state['internal_short']['min_resistance_ohm'] = min_resistance_ohm


def apply_external_short_circuit(pack, resistance_ohm: float,
                                 time_evolution: Optional[Callable] = None,
                                 current_time: float = 0.0) -> None:
    """
    Apply external short circuit fault across pack terminals.
    
    Args:
        pack: Pack model to modify
        resistance_ohm: External short circuit resistance
        time_evolution: Optional function(time) -> resistance_ohm
        current_time: Current simulation time
    """
    if time_evolution is not None:
        resistance_ohm = time_evolution(current_time)
    
    if not hasattr(pack, '_fault_state'):
        pack._fault_state = {}
    
    pack._fault_state['external_short'] = {
        'resistance_ohm': max(0.001, resistance_ohm),
        'active': True
    }


def apply_capacity_fade(cell, fade_factor: float,
                       time_evolution: Optional[Callable] = None,
                       current_time: float = 0.0) -> None:
    """
    Apply capacity fade fault.
    
    Reduces cell capacity by fade_factor.
    
    Args:
        cell: Cell model to modify
        fade_factor: Capacity reduction factor (0.0 to 1.0, where 1.0 = no fade)
        time_evolution: Optional function(time) -> fade_factor
        current_time: Current simulation time
    """
    if time_evolution is not None:
        fade_factor = time_evolution(current_time)
    
    fade_factor = np.clip(fade_factor, 0.1, 1.0)  # Minimum 10% capacity
    
    if not hasattr(cell, '_fault_state'):
        cell._fault_state = {}
    
    cell._fault_state['capacity_fade'] = {
        'fade_factor': fade_factor,
        'active': True
    }
    
    # Apply to capacity (will need cell model modification)
    if hasattr(cell, '_capacity_nominal_ah'):
        # Store original capacity if not already stored
        if 'original_capacity' not in cell._fault_state.get('capacity_fade', {}):
            cell._fault_state['capacity_fade']['original_capacity'] = cell._capacity_nominal_ah


def apply_resistance_increase(cell, resistance_multiplier: float,
                             time_evolution: Optional[Callable] = None,
                             current_time: float = 0.0) -> None:
    """
    Apply resistance increase fault.
    
    Multiplies internal resistance by resistance_multiplier.
    
    Args:
        cell: Cell model to modify
        resistance_multiplier: Resistance multiplier (1.0 = no change, >1.0 = increase)
        time_evolution: Optional function(time) -> multiplier
        current_time: Current simulation time
    """
    if time_evolution is not None:
        resistance_multiplier = time_evolution(current_time)
    
    resistance_multiplier = max(1.0, resistance_multiplier)  # Minimum 1.0
    
    if not hasattr(cell, '_fault_state'):
        cell._fault_state = {}
    
    cell._fault_state['resistance_increase'] = {
        'multiplier': resistance_multiplier,
        'active': True
    }


def apply_thermal_runaway(cell, escalation_factor: float = 1.1,
                         initial_temp_c: Optional[float] = None,
                         time_evolution: Optional[Callable] = None,
                         current_time: float = 0.0) -> None:
    """
    Apply thermal runaway fault.
    
    Creates temperature escalation feedback loop.
    
    Args:
        cell: Cell model to modify
        escalation_factor: Temperature escalation factor per time step
        initial_temp_c: Initial temperature for runaway (if None, use current)
        time_evolution: Optional function(time) -> escalation_factor
        current_time: Current simulation time
    """
    if time_evolution is not None:
        escalation_factor = time_evolution(current_time)
    
    if not hasattr(cell, '_fault_state'):
        cell._fault_state = {}
    
    if initial_temp_c is None:
        initial_temp_c = cell._temperature_c
    
    cell._fault_state['thermal_runaway'] = {
        'escalation_factor': escalation_factor,
        'initial_temp_c': initial_temp_c,
        'active': True
    }


def apply_cell_imbalance(pack, cell_indices: List[int],
                         soc_variation_pct: float = 5.0,
                         capacity_variation_pct: float = 2.0) -> None:
    """
    Apply cell imbalance fault.
    
    Creates variations in SOC and capacity across cells.
    
    Args:
        pack: Pack model to modify
        cell_indices: List of cell indices to affect
        soc_variation_pct: SOC variation in percent
        capacity_variation_pct: Capacity variation in percent
    """
    if not hasattr(pack, '_fault_state'):
        pack._fault_state = {}
    
    pack._fault_state['cell_imbalance'] = {
        'cell_indices': cell_indices,
        'soc_variation_pct': soc_variation_pct,
        'capacity_variation_pct': capacity_variation_pct,
        'active': True
    }


def apply_open_circuit(cell, resistance_ohm: float = 1e6) -> None:
    """
    Apply open circuit fault.
    
    Sets very high resistance (effectively open circuit).
    
    Args:
        cell: Cell model to modify
        resistance_ohm: Open circuit resistance (default: 1MΩ)
    """
    if not hasattr(cell, '_fault_state'):
        cell._fault_state = {}
    
    cell._fault_state['open_circuit'] = {
        'resistance_ohm': resistance_ohm,
        'active': True
    }


def apply_leakage_current(cell, leakage_current_ma: float,
                         time_evolution: Optional[Callable] = None,
                         current_time: float = 0.0) -> None:
    """
    Apply abnormal self-discharge (leakage current) fault.
    
    Adds constant leakage current.
    
    Args:
        cell: Cell model to modify
        leakage_current_ma: Leakage current in mA
        time_evolution: Optional function(time) -> leakage_current_ma
        current_time: Current simulation time
    """
    if time_evolution is not None:
        leakage_current_ma = time_evolution(current_time)
    
    if not hasattr(cell, '_fault_state'):
        cell._fault_state = {}
    
    cell._fault_state['leakage_current'] = {
        'current_ma': leakage_current_ma,
        'active': True
    }


def apply_overcharge(cell, voltage_limit_mv: float = 3700.0) -> None:
    """
    Apply overcharge fault.
    
    Forces charging beyond normal voltage limit.
    
    Args:
        cell: Cell model to modify
        voltage_limit_mv: Overcharge voltage limit in mV
    """
    if not hasattr(cell, '_fault_state'):
        cell._fault_state = {}
    
    cell._fault_state['overcharge'] = {
        'voltage_limit_mv': voltage_limit_mv,
        'active': True
    }


def apply_overdischarge(cell, voltage_limit_mv: float = 2500.0) -> None:
    """
    Apply overdischarge fault.
    
    Forces discharging below normal voltage limit.
    
    Args:
        cell: Cell model to modify
        voltage_limit_mv: Overdischarge voltage limit in mV
    """
    if not hasattr(cell, '_fault_state'):
        cell._fault_state = {}
    
    cell._fault_state['overdischarge'] = {
        'voltage_limit_mv': voltage_limit_mv,
        'active': True
    }


def clear_fault(cell_or_pack, 
                fault_type: str) -> None:
    """
    Clear a specific fault.
    
    Args:
        cell_or_pack: Cell or pack model
        fault_type: Fault type to clear
    """
    if hasattr(cell_or_pack, '_fault_state'):
        if fault_type in cell_or_pack._fault_state:
            cell_or_pack._fault_state[fault_type]['active'] = False


def clear_all_faults(cell_or_pack) -> None:
    """
    Clear all faults.
    
    Args:
        cell_or_pack: Cell or pack model
    """
    if hasattr(cell_or_pack, '_fault_state'):
        for fault_type in cell_or_pack._fault_state:
            cell_or_pack._fault_state[fault_type]['active'] = False



