"""
Fault Type Definitions

This module defines all fault types and categories for the fault injection framework.
"""

from enum import Enum
from typing import Dict, Any, Optional


class FaultCategory(Enum):
    """Fault categories for organization."""
    ELECTRICAL = "electrical"
    THERMAL = "thermal"
    DEGRADATION = "degradation"
    SENSOR = "sensor"
    SYSTEM = "system"
    PROPAGATION = "propagation"


class FaultType(Enum):
    """Fault types for injection."""
    
    # Electrical Faults
    INTERNAL_SHORT_CIRCUIT_HARD = "internal_short_circuit_hard"
    INTERNAL_SHORT_CIRCUIT_SOFT = "internal_short_circuit_soft"
    EXTERNAL_SHORT_CIRCUIT = "external_short_circuit"
    OVERCHARGE = "overcharge"
    OVERDISCHARGE = "overdischarge"
    ABNORMAL_SELF_DISCHARGE = "abnormal_self_discharge"
    OPEN_CIRCUIT = "open_circuit"
    
    # Thermal Faults
    OVERHEATING = "overheating"
    THERMAL_RUNAWAY = "thermal_runaway"
    ABNORMAL_TEMPERATURE = "abnormal_temperature"
    
    # Degradation/Mechanical Faults
    CAPACITY_FADE = "capacity_fade"
    RESISTANCE_INCREASE = "resistance_increase"
    LITHIUM_PLATING = "lithium_plating"
    CELL_IMBALANCE = "cell_imbalance"
    ELECTROLYTE_LEAKAGE = "electrolyte_leakage"
    
    # Sensor/System Faults
    SENSOR_OFFSET = "sensor_offset"
    SENSOR_DRIFT = "sensor_drift"
    INSULATION_FAULT = "insulation_fault"
    
    # Propagation Faults
    THERMAL_PROPAGATION = "thermal_propagation"
    CASCADING_FAILURE = "cascading_failure"
    
    @property
    def category(self) -> FaultCategory:
        """Get the category for this fault type."""
        category_map = {
            # Electrical
            FaultType.INTERNAL_SHORT_CIRCUIT_HARD: FaultCategory.ELECTRICAL,
            FaultType.INTERNAL_SHORT_CIRCUIT_SOFT: FaultCategory.ELECTRICAL,
            FaultType.EXTERNAL_SHORT_CIRCUIT: FaultCategory.ELECTRICAL,
            FaultType.OVERCHARGE: FaultCategory.ELECTRICAL,
            FaultType.OVERDISCHARGE: FaultCategory.ELECTRICAL,
            FaultType.ABNORMAL_SELF_DISCHARGE: FaultCategory.ELECTRICAL,
            FaultType.OPEN_CIRCUIT: FaultCategory.ELECTRICAL,
            # Thermal
            FaultType.OVERHEATING: FaultCategory.THERMAL,
            FaultType.THERMAL_RUNAWAY: FaultCategory.THERMAL,
            FaultType.ABNORMAL_TEMPERATURE: FaultCategory.THERMAL,
            # Degradation
            FaultType.CAPACITY_FADE: FaultCategory.DEGRADATION,
            FaultType.RESISTANCE_INCREASE: FaultCategory.DEGRADATION,
            FaultType.LITHIUM_PLATING: FaultCategory.DEGRADATION,
            FaultType.CELL_IMBALANCE: FaultCategory.DEGRADATION,
            FaultType.ELECTROLYTE_LEAKAGE: FaultCategory.DEGRADATION,
            # Sensor/System
            FaultType.SENSOR_OFFSET: FaultCategory.SENSOR,
            FaultType.SENSOR_DRIFT: FaultCategory.SENSOR,
            FaultType.INSULATION_FAULT: FaultCategory.SYSTEM,
            # Propagation
            FaultType.THERMAL_PROPAGATION: FaultCategory.PROPAGATION,
            FaultType.CASCADING_FAILURE: FaultCategory.PROPAGATION,
        }
        return category_map.get(self, FaultCategory.SYSTEM)
    
    @property
    def default_parameters(self) -> Dict[str, Any]:
        """Get default parameters for this fault type."""
        defaults = {
            FaultType.INTERNAL_SHORT_CIRCUIT_HARD: {
                'resistance_ohm': 0.1,
                'description': 'Hard internal short (0.01-1Ω)'
            },
            FaultType.INTERNAL_SHORT_CIRCUIT_SOFT: {
                'resistance_ohm': 500.0,
                'description': 'Soft internal short (100-1000Ω)'
            },
            FaultType.EXTERNAL_SHORT_CIRCUIT: {
                'resistance_ohm': 0.05,
                'description': 'External short across pack terminals'
            },
            FaultType.OVERCHARGE: {
                'voltage_limit_mv': 3700.0,
                'description': 'Force charging beyond V_max'
            },
            FaultType.OVERDISCHARGE: {
                'voltage_limit_mv': 2500.0,
                'description': 'Force discharging below V_min'
            },
            FaultType.ABNORMAL_SELF_DISCHARGE: {
                'leakage_current_ma': 10.0,
                'description': 'Constant leakage current'
            },
            FaultType.OPEN_CIRCUIT: {
                'resistance_ohm': 1e6,
                'description': 'High resistance open circuit'
            },
            FaultType.OVERHEATING: {
                'temperature_c': 60.0,
                'description': 'Elevated temperature'
            },
            FaultType.THERMAL_RUNAWAY: {
                'escalation_factor': 1.1,
                'description': 'Temperature escalation feedback'
            },
            FaultType.ABNORMAL_TEMPERATURE: {
                'temperature_offset_c': 10.0,
                'description': 'Temperature offset'
            },
            FaultType.CAPACITY_FADE: {
                'fade_factor': 0.9,
                'description': 'Capacity reduction factor'
            },
            FaultType.RESISTANCE_INCREASE: {
                'resistance_multiplier': 1.5,
                'description': 'Resistance increase multiplier'
            },
            FaultType.LITHIUM_PLATING: {
                'plating_resistance_ohm': 0.5,
                'capacity_reduction': 0.05,
                'description': 'Lithium plating effects'
            },
            FaultType.CELL_IMBALANCE: {
                'soc_variation_pct': 5.0,
                'capacity_variation_pct': 2.0,
                'description': 'Cell-to-cell variations'
            },
            FaultType.ELECTROLYTE_LEAKAGE: {
                'resistance_multiplier': 1.3,
                'leakage_current_ma': 5.0,
                'description': 'Electrolyte leakage effects'
            },
            FaultType.SENSOR_OFFSET: {
                'voltage_offset_mv': 10.0,
                'temperature_offset_c': 2.0,
                'description': 'Sensor measurement offset'
            },
            FaultType.SENSOR_DRIFT: {
                'drift_rate_mv_per_hour': 1.0,
                'description': 'Gradual sensor drift'
            },
            FaultType.INSULATION_FAULT: {
                'insulation_resistance_ohm': 1000.0,
                'description': 'Insulation resistance to ground'
            },
            FaultType.THERMAL_PROPAGATION: {
                'correlation_coefficient': 0.7,
                'description': 'Thermal coupling between cells'
            },
            FaultType.CASCADING_FAILURE: {
                'trigger_probability': 0.1,
                'description': 'Cascading failure probability'
            },
        }
        return defaults.get(self, {})
    
    def __str__(self) -> str:
        """String representation."""
        return self.value
    
    @classmethod
    def from_string(cls, value: str) -> 'FaultType':
        """Create FaultType from string."""
        try:
            return cls(value.lower())
        except ValueError:
            # Try to find by partial match
            for fault_type in cls:
                if fault_type.value.lower() == value.lower():
                    return fault_type
            raise ValueError(f"Unknown fault type: {value}")

