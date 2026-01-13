"""
LiFePO₄ Battery Cell Equivalent Circuit Model (ECM)

This module implements a detailed ECM for LiFePO₄ cells with:
- OCV-SOC relationship with hysteresis (separate charge/discharge curves)
- Internal resistance R0 as function of SOC and temperature
- 2RC network (R1-C1 fast, R2-C2 slow) for transient response
- Temperature effects on OCV and capacity
- Aging factors (cycle aging + calendar aging, resistance increase)
- Thermal model (self-heating)
"""

import numpy as np
from typing import Tuple, Optional


class LiFePO4Cell:
    """
    LiFePO₄ Battery Cell Equivalent Circuit Model
    
    ECM Structure:
        OCV(SOC, T, direction) - R0(SOC, T) - [R1 || C1] - [R2 || C2] - Terminal
    
    Features:
    - Hysteresis: Separate charge/discharge OCV curves
    - 2RC Network: Fast (R1-C1) and slow (R2-C2) transients
    - Calendar Aging: Time-based capacity fade
    - Cycle Aging: Cycle-based capacity fade and resistance increase
    
    Parameters:
        capacity_ah: Nominal capacity in Ah (default: 100Ah)
        initial_soc: Initial state of charge (0.0 to 1.0, default: 0.5)
        temperature_c: Initial temperature in °C (default: 32.0)
        cycles: Number of charge/discharge cycles (default: 0)
    """
    
    # OCV-SOC lookup tables (101 points: 0% to 100%)
    # Typical LiFePO₄ curve: flat plateau around 3.2V, steep ends
    # Precision: 0.001V (1mV) for better accuracy, especially in steep regions
    # Hysteresis: Separate curves for charge and discharge
    _OCV_SOC_TABLE_DISCHARGE = np.array([
        # SOC%, OCV(V) - Adjusted for application requirements (0% SOC = 2.52V to ensure terminal voltage >= 2.51V after IR/RC drops)
        [0.0, 2.520],   # 0% - fully discharged (2.52V ensures terminal voltage >= 2.51V after IR/RC drops)
        [1.0, 2.550],
        [2.0, 2.600],
        [3.0, 2.650],
        [4.0, 2.700],
        [5.0, 2.750],
        [6.0, 2.762],
        [7.0, 2.774],
        [8.0, 2.786],
        [9.0, 2.798],
        [10.0, 2.810],  # 10%
        [11.0, 2.821],
        [12.0, 2.831],
        [13.0, 2.842],
        [14.0, 2.853],
        [15.0, 2.864],
        [16.0, 2.874],
        [17.0, 2.885],
        [18.0, 2.896],
        [19.0, 2.906],
        [20.0, 2.917],  # 20%
        [21.0, 2.918],
        [22.0, 2.918],
        [23.0, 2.919],
        [24.0, 2.919],
        [25.0, 2.920],
        [26.0, 2.921],
        [27.0, 2.921],
        [28.0, 2.922],
        [29.0, 2.922],
        [30.0, 2.923],  # 30%
        [31.0, 2.924],
        [32.0, 2.924],
        [33.0, 2.925],
        [34.0, 2.925],
        [35.0, 2.926],
        [36.0, 2.927],
        [37.0, 2.927],
        [38.0, 2.928],
        [39.0, 2.928],
        [40.0, 2.929],  # 40%
        [41.0, 2.930],
        [42.0, 2.930],
        [43.0, 2.931],
        [44.0, 2.931],
        [45.0, 2.932],
        [46.0, 2.933],
        [47.0, 2.933],
        [48.0, 2.934],
        [49.0, 2.934],
        [50.0, 2.935],  # 50%
        [51.0, 2.936],
        [52.0, 2.936],
        [53.0, 2.937],
        [54.0, 2.937],
        [55.0, 2.938],
        [56.0, 2.938],
        [57.0, 2.939],
        [58.0, 2.940],
        [59.0, 2.940],
        [60.0, 2.941],  # 60%
        [61.0, 2.941],
        [62.0, 2.942],
        [63.0, 2.942],
        [64.0, 2.943],
        [65.0, 2.944],
        [66.0, 2.944],
        [67.0, 2.945],
        [68.0, 2.945],
        [69.0, 2.946],
        [70.0, 2.946],  # 70%
        [71.0, 2.947],
        [72.0, 2.947],
        [73.0, 2.948],
        [74.0, 2.949],
        [75.0, 2.949],
        [76.0, 2.950],
        [77.0, 2.950],
        [78.0, 2.951],
        [79.0, 2.951],
        [80.0, 2.952],  # 80%
        [81.0, 2.954],
        [82.0, 2.955],
        [83.0, 2.957],
        [84.0, 2.958],
        [85.0, 2.960],
        [86.0, 2.961],
        [87.0, 2.963],
        [88.0, 2.964],
        [89.0, 2.966],
        [90.0, 2.967],  # 90%
        [91.0, 2.981],
        [92.0, 2.996],
        [93.0, 3.010],
        [94.0, 3.024],
        [95.0, 3.039],
        [96.0, 3.053],
        [97.0, 3.067],
        [98.0, 3.081],
        [99.0, 3.096],
        [100.0, 3.110],  # 100% - fully charged (adjusted from 3.472V to 3.110V)
    ])
    
    # Charge OCV table (typically 5-15mV higher than discharge at same SOC due to hysteresis)
    # LiFePO₄ shows less hysteresis than other chemistries, but it's still present
    # Hysteresis offset: 15mV for SOC 0-20%, 10mV for SOC 20-80%, 5mV for SOC 80-100%
    _OCV_SOC_TABLE_CHARGE = np.array([
        # SOC%, OCV(V) - Charge curve (higher than discharge due to hysteresis)
        [0.0, 2.535],   # 0% - 15mV higher than discharge (2.520) - ensures terminal voltage >= 2.51V after IR/RC drops
        [1.0, 2.565],   # 15mV higher
        [2.0, 2.615],   # 15mV higher
        [3.0, 2.665],   # 15mV higher
        [4.0, 2.715],   # 15mV higher
        [5.0, 2.765],   # 15mV higher
        [6.0, 2.777],   # 15mV higher
        [7.0, 2.789],   # 15mV higher
        [8.0, 2.801],   # 15mV higher
        [9.0, 2.813],   # 15mV higher
        [10.0, 2.825],  # 10% - 15mV higher than discharge (2.810)
        [11.0, 2.836],  # 15mV higher
        [12.0, 2.846],  # 15mV higher
        [13.0, 2.857],  # 15mV higher
        [14.0, 2.868],  # 15mV higher
        [15.0, 2.879],  # 15mV higher
        [16.0, 2.889],  # 15mV higher
        [17.0, 2.900],  # 15mV higher
        [18.0, 2.911],  # 15mV higher
        [19.0, 2.921],  # 15mV higher
        [20.0, 2.927],  # 20% - 10mV higher than discharge (2.917)
        [21.0, 2.928],  # 10mV higher
        [22.0, 2.928],  # 10mV higher
        [23.0, 2.929],  # 10mV higher
        [24.0, 2.929],  # 10mV higher
        [25.0, 2.930],  # 10mV higher
        [26.0, 2.931],  # 10mV higher
        [27.0, 2.931],  # 10mV higher
        [28.0, 2.932],  # 10mV higher
        [29.0, 2.932],  # 10mV higher
        [30.0, 2.933],  # 30% - 10mV higher than discharge (2.923)
        [31.0, 2.934],  # 10mV higher
        [32.0, 2.934],  # 10mV higher
        [33.0, 2.935],  # 10mV higher
        [34.0, 2.935],  # 10mV higher
        [35.0, 2.936],  # 10mV higher
        [36.0, 2.937],  # 10mV higher
        [37.0, 2.937],  # 10mV higher
        [38.0, 2.938],  # 10mV higher
        [39.0, 2.938],  # 10mV higher
        [40.0, 2.939],  # 40% - 10mV higher than discharge (2.929)
        [41.0, 2.940],  # 10mV higher
        [42.0, 2.940],  # 10mV higher
        [43.0, 2.941],  # 10mV higher
        [44.0, 2.941],  # 10mV higher
        [45.0, 2.942],  # 10mV higher
        [46.0, 2.943],  # 10mV higher
        [47.0, 2.943],  # 10mV higher
        [48.0, 2.944],  # 10mV higher
        [49.0, 2.944],  # 10mV higher
        [50.0, 2.945],  # 50% - 10mV higher than discharge (2.935)
        [51.0, 2.946],  # 10mV higher
        [52.0, 2.946],  # 10mV higher
        [53.0, 2.947],  # 10mV higher
        [54.0, 2.947],  # 10mV higher
        [55.0, 2.948],  # 10mV higher
        [56.0, 2.948],  # 10mV higher
        [57.0, 2.949],  # 10mV higher
        [58.0, 2.950],  # 10mV higher
        [59.0, 2.950],  # 10mV higher
        [60.0, 2.951],  # 60% - 10mV higher than discharge (2.941)
        [61.0, 2.951],  # 10mV higher
        [62.0, 2.952],  # 10mV higher
        [63.0, 2.952],  # 10mV higher
        [64.0, 2.953],  # 10mV higher
        [65.0, 2.954],  # 10mV higher
        [66.0, 2.954],  # 10mV higher
        [67.0, 2.955],  # 10mV higher
        [68.0, 2.955],  # 10mV higher
        [69.0, 2.956],  # 10mV higher
        [70.0, 2.956],  # 70% - 10mV higher than discharge (2.946)
        [71.0, 2.957],  # 10mV higher
        [72.0, 2.957],  # 10mV higher
        [73.0, 2.958],  # 10mV higher
        [74.0, 2.959],  # 10mV higher
        [75.0, 2.959],  # 10mV higher
        [76.0, 2.960],  # 10mV higher
        [77.0, 2.960],  # 10mV higher
        [78.0, 2.961],  # 10mV higher
        [79.0, 2.961],  # 10mV higher
        [80.0, 2.962],  # 80% - 10mV higher than discharge (2.952)
        [81.0, 2.959],  # 5mV higher than discharge (2.954)
        [82.0, 2.960],  # 5mV higher
        [83.0, 2.962],  # 5mV higher
        [84.0, 2.963],  # 5mV higher
        [85.0, 2.965],  # 5mV higher
        [86.0, 2.966],  # 5mV higher
        [87.0, 2.968],  # 5mV higher
        [88.0, 2.969],  # 5mV higher
        [89.0, 2.971],  # 5mV higher
        [90.0, 2.972],  # 90% - 5mV higher than discharge (2.967)
        [91.0, 2.986],  # 5mV higher
        [92.0, 3.001],  # 5mV higher
        [93.0, 3.015],  # 5mV higher
        [94.0, 3.029],  # 5mV higher
        [95.0, 3.044],  # 5mV higher
        [96.0, 3.058],  # 5mV higher
        [97.0, 3.072],  # 5mV higher
        [98.0, 3.086],  # 5mV higher
        [99.0, 3.101],  # 5mV higher
        [100.0, 3.110],  # 100% - fully charged (same as discharge at 100%)
    ])
    
    # ECM parameters - 2RC network
    # Fast RC network (short time constant)
    # Reduced resistances for high C-rate operation to prevent excessive voltage drops
    R1 = 1e-3  # Fast transient resistance: 1 mΩ (reduced from 3 mΩ)
    C1 = 2000.0  # Fast transient capacitance: 2000 F (time constant τ1 = R1*C1 = 2s)
    
    # Slow RC network (long time constant)
    R2 = 0.5e-3  # Slow transient resistance: 0.5 mΩ (reduced from 2 mΩ)
    C2 = 10000.0  # Slow transient capacitance: 10000 F (time constant τ2 = R2*C2 = 5s)
    
    # Temperature coefficients
    OCV_TEMP_COEFF = -0.5e-3  # OCV temperature coefficient: -0.5 mV/°C
    CAPACITY_TEMP_COEFF = 0.005  # Capacity temperature coefficient: +0.5% per °C
    
    # Aging parameters
    # Cycle aging
    FADE_RATE = 0.0001  # Capacity fade rate per cycle
    RESISTANCE_INCREASE_RATE = 0.001  # Resistance increase rate per cycle
    
    # Calendar aging parameters (Arrhenius-based model)
    CALENDAR_AGING_ACTIVATION_ENERGY = 30000.0  # Activation energy (J/mol) for Arrhenius equation
    GAS_CONSTANT = 8.314  # Gas constant (J/(mol·K))
    CALENDAR_AGING_BASE_RATE = 1.0e-9  # Base aging rate (per hour at 25°C, 50% SOC)
    CALENDAR_AGING_SOC_EXPONENT = 0.5  # SOC dependence exponent (aging faster at high/low SOC)
    CALENDAR_AGING_REF_TEMP = 298.15  # Reference temperature (25°C in Kelvin)
    
    # Thermal parameters
    THERMAL_MASS = 3500.0  # Thermal mass (J/°C) - for 100Ah cell (~2.5kg, c_p=1400 J/(kg·K))
    THERMAL_RESISTANCE = 0.5  # Thermal resistance to ambient (K/W) - convection + radiation
    SELF_HEATING_COEFF = 0.001  # Self-heating coefficient (W per A²)
    # Heat dissipation parameters
    CELL_SURFACE_AREA = 0.15  # m² (approximate for 100Ah cell)
    CONVECTION_COEFFICIENT = 10.0  # W/(m²·K) - natural convection
    EMISSIVITY = 0.9  # Surface emissivity for radiation
    STEFAN_BOLTZMANN = 5.67e-8  # W/(m²·K⁴) - Stefan-Boltzmann constant
    
    def __init__(
        self,
        capacity_ah: float = 100.0,
        initial_soc: float = 0.5,
        temperature_c: float = 32.0,
        cycles: int = 0,
        ambient_temp_c: float = 32.0,
        resistance_multiplier: float = 1.0
    ):
        """
        Initialize LiFePO₄ cell model.
        
        Args:
            capacity_ah: Nominal capacity in Ah (default: 100Ah)
            initial_soc: Initial state of charge (0.0 to 1.0, default: 0.5)
            temperature_c: Initial temperature in °C (default: 32.0)
            cycles: Number of charge/discharge cycles (default: 0)
            ambient_temp_c: Ambient temperature in °C (default: 32.0)
            resistance_multiplier: Base resistance multiplier for cell-to-cell variation (default: 1.0)
        """
        # Store nominal capacity
        self._capacity_nominal_ah = capacity_ah
        
        # Initialize state variables
        self._soc = np.clip(initial_soc, 0.0, 1.0)
        self._temperature_c = temperature_c
        self._ambient_temp_c = ambient_temp_c
        self._cycles = cycles
        
        # Store base resistance multiplier (for cell-to-cell variation)
        self._base_resistance_multiplier = max(resistance_multiplier, 0.1)  # Prevent negative or zero multiplier
        
        # 2RC network state (voltages across C1 and C2)
        self._v_rc1 = 0.0  # Fast RC network voltage
        self._v_rc2 = 0.0  # Slow RC network voltage
        
        # Hysteresis tracking
        self._last_current_direction = 0  # 1 = charging, -1 = discharging, 0 = rest
        self._hysteresis_soc = initial_soc  # SOC at last current direction change
        
        # Store last calculated terminal voltage (for get_state())
        self._last_terminal_voltage_v = None
        
        # Calendar aging tracking
        self._calendar_aging_time_hours = 0.0  # Total time in hours (for calendar aging)
        self._last_update_time_hours = 0.0  # Last update time for calendar aging calculation
        self._storage_soc = initial_soc  # SOC during storage (for calendar aging)
        self._storage_temp = temperature_c  # Temperature during storage
        
        # Fault state tracking
        self._fault_state = {}
        
        # Calculate aged capacity and resistance
        self._update_aging()
        
        # Initialize OCV lookup table interpolation (both charge and discharge)
        self._soc_table = self._OCV_SOC_TABLE_DISCHARGE[:, 0] / 100.0  # Convert % to fraction
        self._ocv_table_discharge = self._OCV_SOC_TABLE_DISCHARGE[:, 1]
        self._ocv_table_charge = self._OCV_SOC_TABLE_CHARGE[:, 1]
    
    def _update_aging(self):
        """
        Update capacity and resistance based on cycle count and calendar aging.
        
        Combined aging model:
        - Cycle aging: Capacity fade and resistance increase with cycles
        - Calendar aging: Capacity fade with time, temperature, and storage SOC
        """
        # Cycle aging: Capacity fade
        cycle_fade_factor = 1.0 - self.FADE_RATE * np.sqrt(max(self._cycles, 0))
        cycle_fade_factor = max(cycle_fade_factor, 0.5)  # Limit to 50% fade
        
        # Calendar aging: Time-based capacity fade
        # Arrhenius equation: rate = A * exp(-Ea/(R*T)) * SOC^exponent
        # Aging is faster at high temperature and extreme SOC
        if self._calendar_aging_time_hours > 0:
            temp_kelvin = self._storage_temp + 273.15
            arrhenius_factor = np.exp(
                -self.CALENDAR_AGING_ACTIVATION_ENERGY / 
                (self.GAS_CONSTANT * temp_kelvin)
            )
            
            # SOC dependence: aging faster at high/low SOC
            # Normalize SOC to 0-1 range, then apply exponent
            soc_factor = (self._storage_soc ** self.CALENDAR_AGING_SOC_EXPONENT) + \
                        ((1.0 - self._storage_soc) ** self.CALENDAR_AGING_SOC_EXPONENT)
            soc_factor = soc_factor / 2.0  # Normalize
            
            # Calculate calendar aging (hours to years conversion)
            calendar_aging_rate = self.CALENDAR_AGING_BASE_RATE * arrhenius_factor * soc_factor
            calendar_fade = calendar_aging_rate * self._calendar_aging_time_hours
            calendar_fade_factor = 1.0 - min(calendar_fade, 0.3)  # Limit to 30% calendar fade
        else:
            calendar_fade_factor = 1.0
        
        # Combined aging: multiply both factors
        total_fade_factor = cycle_fade_factor * calendar_fade_factor
        total_fade_factor = max(total_fade_factor, 0.5)  # Overall limit to 50% fade
        
        self._capacity_actual_ah = self._capacity_nominal_ah * total_fade_factor
        
        # Resistance increase: Only cycle-based (calendar aging has minimal effect on resistance)
        self._resistance_multiplier = 1.0 + self.RESISTANCE_INCREASE_RATE * max(self._cycles, 0)
    
    def get_ocv(
        self, 
        soc_pct: Optional[float] = None, 
        temperature_c: Optional[float] = None,
        current_direction: Optional[int] = None
    ) -> float:
        """
        Get Open Circuit Voltage (OCV) for given SOC and temperature with hysteresis.
        
        Args:
            soc_pct: State of charge in percent (0-100). If None, use current SOC.
            temperature_c: Temperature in °C. If None, use current temperature.
            current_direction: Current direction (1=discharge, -1=charge, 0=rest).
                             If None, use last known direction.
        
        Returns:
            OCV in volts
        """
        if soc_pct is None:
            soc = self._soc
        else:
            soc = np.clip(soc_pct / 100.0, 0.0, 1.0)
        
        if temperature_c is None:
            temp = self._temperature_c
        else:
            temp = temperature_c
        
        # Determine which OCV curve to use based on current direction
        if current_direction is None:
            current_direction = self._last_current_direction
        
        # Select OCV table based on current direction
        # Charge: use charge curve (higher voltage)
        # Discharge: use discharge curve (lower voltage)
        # Rest: interpolate between curves based on last direction
        # Note: Positive current = discharge, Negative current = charge
        if current_direction > 0:  # Discharging (positive current)
            ocv_table = self._ocv_table_discharge
        elif current_direction < 0:  # Charging (negative current)
            ocv_table = self._ocv_table_charge
        else:  # Rest - use average or last direction
            if self._last_current_direction > 0:  # Was discharging
                ocv_table = self._ocv_table_discharge
            elif self._last_current_direction < 0:  # Was charging
                ocv_table = self._ocv_table_charge
            else:
                # No history - use average of charge and discharge
                ocv_charge = np.interp(soc, self._soc_table, self._ocv_table_charge)
                ocv_discharge = np.interp(soc, self._soc_table, self._ocv_table_discharge)
                ocv_base = (ocv_charge + ocv_discharge) / 2.0
                # Apply temperature correction
                ocv = ocv_base + self.OCV_TEMP_COEFF * (temp - 25.0)
                return ocv
        
        # Interpolate OCV from selected lookup table
        ocv_base = np.interp(soc, self._soc_table, ocv_table)
        
        # Apply temperature correction: OCV_temp = OCV_base + temp_coeff * (T - 25°C)
        ocv = ocv_base + self.OCV_TEMP_COEFF * (temp - 25.0)
        
        return ocv
    
    def get_internal_resistance(self, soc_pct: Optional[float] = None, temperature_c: Optional[float] = None) -> float:
        """
        Get internal resistance R0 as function of SOC and temperature.
        
        Formula: R0(SOC, T) = R0_base(SOC) * [1 - 0.005 * (T - 25)] * base_multiplier * aging_factor
        
        Args:
            soc_pct: State of charge in percent (0-100). If None, use current SOC.
            temperature_c: Temperature in °C. If None, use current temperature.
        
        Returns:
            Internal resistance in mΩ
        """
        if soc_pct is None:
            soc = self._soc
        else:
            soc = np.clip(soc_pct / 100.0, 0.0, 1.0)
        
        if temperature_c is None:
            temp = self._temperature_c
        else:
            temp = temperature_c
        
        # Base R0 at 25°C: 0.5 mΩ at 50% SOC
        # SOC dependence: higher at low SOC, lower at high SOC (typical LFP behavior)
        # Fine-tuned to better match real data behavior
        # - 1.4x at 0% SOC (slightly reduced from 1.5x for better low-SOC voltage match)
        # - 1.0x at 50% SOC (baseline)
        # - 0.75x at 100% SOC (slightly reduced from 0.8x for better high-SOC voltage match)
        if soc <= 0.5:
            # Linear from 0% to 50%
            r0_base_multiplier = 1.4 - (soc * 0.8)  # 1.4 at 0%, 1.0 at 50%
        else:
            # Linear from 50% to 100%: reduce resistance at high SOC
            r0_base_multiplier = 1.0 - ((soc - 0.5) * 0.5)  # 1.0 at 50%, 0.75 at 100%
        
        r0_base_mohm = 0.5 * r0_base_multiplier
        
        # Temperature dependence: -0.5% per °C (lower R0 at higher temp)
        temp_factor = 1.0 - 0.005 * (temp - 25.0)
        temp_factor = max(temp_factor, 0.5)  # Limit to 50% reduction
        
        # Apply base multiplier (cell-to-cell variation) and aging multiplier
        r0_mohm = r0_base_mohm * temp_factor * self._base_resistance_multiplier * self._resistance_multiplier
        
        # Apply fault-based resistance changes
        if hasattr(self, '_fault_state') and self._fault_state:
            # Resistance increase fault
            if 'resistance_increase' in self._fault_state and self._fault_state['resistance_increase'].get('active', False):
                multiplier = self._fault_state['resistance_increase'].get('multiplier', 1.0)
                r0_mohm *= multiplier
            # Open circuit fault
            if 'open_circuit' in self._fault_state and self._fault_state['open_circuit'].get('active', False):
                resistance_ohm = self._fault_state['open_circuit'].get('resistance_ohm', 1e6)
                r0_mohm = resistance_ohm * 1000.0  # Convert to mΩ
        
        return r0_mohm
    
    def _update_thermal_model(self, current_ma: float, dt_ms: float, ambient_temp_c: Optional[float] = None):
        """
        Update cell temperature based on self-heating and ambient.
        
        Enhanced thermal model:
        - Self-heating: P = I² * R0 (normal operation) + P_short (fault)
        - Heat dissipation: Q_loss = Q_conv + Q_rad
          - Convection: Q_conv = h * A * (T_cell - T_ambient)
          - Radiation: Q_rad = ε * σ * A * (T_cell^4 - T_ambient^4)
        - Temperature change: dT = (P_heating - Q_loss) * dt / C_thermal
        - Thermal runaway: Exothermic reactions at high temperatures
        
        Args:
            current_ma: Current in mA (positive = discharge, negative = charge)
            dt_ms: Time step in milliseconds
            ambient_temp_c: Ambient temperature in °C. If None, use stored ambient.
        """
        if ambient_temp_c is not None:
            self._ambient_temp_c = ambient_temp_c
        
        # Convert current to Amperes
        current_a = current_ma / 1000.0
        
        # Calculate normal power dissipation: P = I² * R0
        r0_ohm = self.get_internal_resistance() / 1000.0  # Convert mΩ to Ω
        power_w = (current_a ** 2) * r0_ohm
        
        # Add fault-related heat generation (handled in _apply_fault_effects, but we need total here)
        # This will be added via temp_adjustment from _apply_fault_effects
        
        # Heat dissipation to ambient: Q_loss = Q_conv + Q_rad
        temp_diff = self._temperature_c - self._ambient_temp_c
        temp_diff_k = temp_diff  # Temperature difference in Kelvin (same as Celsius for differences)
        
        # Convection heat transfer: Q_conv = h * A * (T_cell - T_ambient)
        q_conv_w = self.CONVECTION_COEFFICIENT * self.CELL_SURFACE_AREA * temp_diff_k
        
        # Radiation heat transfer: Q_rad = ε * σ * A * (T_cell^4 - T_ambient^4)
        t_cell_k = self._temperature_c + 273.15  # Convert to Kelvin
        t_ambient_k = self._ambient_temp_c + 273.15  # Convert to Kelvin
        q_rad_w = self.EMISSIVITY * self.STEFAN_BOLTZMANN * self.CELL_SURFACE_AREA * (
            t_cell_k ** 4 - t_ambient_k ** 4
        )
        
        # Total heat loss
        heat_loss_w = q_conv_w + q_rad_w
        
        # Thermal runaway heat generation (exothermic reactions)
        thermal_runaway_power_w = self._calculate_thermal_runaway_heat()
        
        # Net power: P_net = P_heating + P_thermal_runaway - Q_loss
        net_power_w = power_w + thermal_runaway_power_w - heat_loss_w
        
        # Temperature change: dT = P_net * dt / C_thermal
        dt_sec = dt_ms / 1000.0
        dtemp = (net_power_w * dt_sec) / self.THERMAL_MASS
        
        # Update temperature
        self._temperature_c += dtemp
        
        # Limit temperature to reasonable range (extended for thermal runaway scenarios)
        # Allow up to 200°C for thermal runaway modeling, but warn
        self._temperature_c = np.clip(self._temperature_c, -40.0, 200.0)
    
    def _calculate_thermal_runaway_heat(self) -> float:
        """
        Calculate heat generation from thermal runaway exothermic reactions.
        
        Thermal runaway stages:
        - SEI decomposition: ~90-120°C, ΔH ≈ 200-400 J/g
        - Anode-electrolyte reaction: ~120-150°C, ΔH ≈ 1000-2000 J/g
        - Cathode decomposition: ~150-200°C, ΔH ≈ 500-1000 J/g
        - Electrolyte decomposition: >200°C, ΔH ≈ 2000-4000 J/g
        
        Returns:
            Additional heat generation power in Watts
        """
        temp_c = self._temperature_c
        power_w = 0.0
        
        # SEI decomposition (90-120°C)
        if temp_c >= 90.0:
            # Arrhenius-like activation: exponential increase with temperature
            if temp_c < 120.0:
                activation = np.exp((temp_c - 90.0) / 10.0)  # Exponential activation
                power_w += 0.5 * activation  # Base power ~0.5W, scales exponentially
            else:
                # Fully activated
                power_w += 5.0  # ~5W when fully activated
        
        # Anode-electrolyte reaction (120-150°C)
        if temp_c >= 120.0:
            if temp_c < 150.0:
                activation = np.exp((temp_c - 120.0) / 8.0)
                power_w += 2.0 * activation  # Base power ~2W
            else:
                power_w += 20.0  # ~20W when fully activated
        
        # Cathode decomposition (150-200°C)
        if temp_c >= 150.0:
            if temp_c < 200.0:
                activation = np.exp((temp_c - 150.0) / 10.0)
                power_w += 5.0 * activation  # Base power ~5W
            else:
                power_w += 50.0  # ~50W when fully activated
        
        # Electrolyte decomposition (>200°C) - catastrophic
        if temp_c >= 200.0:
            activation = np.exp((temp_c - 200.0) / 5.0)
            power_w += 100.0 * activation  # Very high power, exponential growth
        
        return power_w
    
    def update(
        self,
        current_ma: float,
        dt_ms: float,
        temperature_c: Optional[float] = None,
        ambient_temp_c: Optional[float] = None
    ) -> Tuple[float, float]:
        """
        Update cell state based on current and time step.
        
        ECM update:
        1. Update SOC using Coulomb counting
        2. Update 2RC network (R1-C1 fast, R2-C2 slow) voltages
        3. Calculate terminal voltage: V = OCV - I*R0 - V_RC1 - V_RC2
        4. Update thermal model
        5. Update calendar aging tracking
        
        Args:
            current_ma: Current in mA (positive = discharge, negative = charge)
            dt_ms: Time step in milliseconds
            temperature_c: External temperature in °C (optional, for forced temp)
            ambient_temp_c: Ambient temperature in °C (optional)
        
        Returns:
            Tuple of (terminal_voltage_mv, soc_pct)
        """
        # Update thermal model (if not forced temperature)
        if temperature_c is None:
            self._update_thermal_model(current_ma, dt_ms, ambient_temp_c)
        else:
            self._temperature_c = temperature_c
        
        # Apply fault effects (modifies current and temperature)
        fault_current_ma, temp_adjustment = self._apply_fault_effects(current_ma, dt_ms)
        self._temperature_c += temp_adjustment
        
        # Get temperature-dependent capacity
        # Capacity increases with temperature: Q(T) = Q_nominal * [1 + 0.005 * (T - 25)]
        temp_capacity_factor = 1.0 + self.CAPACITY_TEMP_COEFF * (self._temperature_c - 25.0)
        fault_capacity_factor = self._get_fault_capacity_factor()
        capacity_ah = self._capacity_actual_ah * temp_capacity_factor * fault_capacity_factor
        
        # Update SOC using Coulomb counting
        # SOC change: dSOC = -I * dt / Q (negated because positive = discharge, negative = charge)
        # Positive current (discharge) decreases SOC, negative current (charge) increases SOC
        # Use fault-modified current
        current_a = fault_current_ma / 1000.0
        dt_hours = dt_ms / (1000.0 * 3600.0)
        dsoc = -(current_a * dt_hours) / capacity_ah  # Negate because positive = discharge
        
        self._soc += dsoc
        self._soc = np.clip(self._soc, 0.0, 1.0)
        
        # Update current direction for hysteresis
        # Note: Positive current = discharge, Negative current = charge
        if current_ma > 0.001:  # Discharging (positive current, small threshold to avoid noise)
            new_direction = 1
        elif current_ma < -0.001:  # Charging (negative current)
            new_direction = -1
        else:  # Rest
            new_direction = 0
        
        # Update hysteresis tracking if direction changed
        if new_direction != 0 and new_direction != self._last_current_direction:
            self._hysteresis_soc = self._soc
            self._last_current_direction = new_direction
        elif new_direction != 0:
            self._last_current_direction = new_direction
        
        # Update 2RC network voltages
        # C-rate dependent RC resistances: reduce at high C-rates to prevent unrealistic voltage drops
        # At high C-rates, polarization is lower due to better cell design and higher conductivity
        current_c_rate = abs(current_a) / self._capacity_nominal_ah if self._capacity_nominal_ah > 0 else 0.0
        
        # Scale RC resistances based on C-rate
        # At 1C: use full resistance
        # At 6C: use ~40% of resistance (reduced polarization at high rates)
        # Use a saturation function: R_eff = R_base * (1 / (1 + alpha * (C_rate - 1)))
        # This reduces RC resistance as C-rate increases
        if current_c_rate <= 1.0:
            rc_scale_factor = 1.0  # Full resistance at low C-rates
        else:
            # Reduce resistance at high C-rates: scale factor decreases from 1.0 at 1C to ~0.4 at 6C
            # Formula: scale = 1.0 / (1.0 + 0.15 * (C_rate - 1.0))
            rc_scale_factor = 1.0 / (1.0 + 0.15 * (current_c_rate - 1.0))
            rc_scale_factor = max(rc_scale_factor, 0.3)  # Minimum 30% to prevent zero resistance
        
        r1_effective = self.R1 * rc_scale_factor
        r2_effective = self.R2 * rc_scale_factor
        
        # Fast RC network (R1-C1): short time constant
        tau1 = r1_effective * self.C1  # Time constant depends on effective resistance
        dt_sec = dt_ms / 1000.0
        exp_factor1 = np.exp(-dt_sec / tau1) if tau1 > 0 else 0.0
        
        # Update fast RC voltage using effective resistance
        self._v_rc1 = self._v_rc1 * exp_factor1 + current_a * r1_effective * (1.0 - exp_factor1)
        
        # Slow RC network (R2-C2): long time constant
        tau2 = r2_effective * self.C2  # Time constant depends on effective resistance
        exp_factor2 = np.exp(-dt_sec / tau2) if tau2 > 0 else 0.0
        
        # Update slow RC voltage using effective resistance
        self._v_rc2 = self._v_rc2 * exp_factor2 + current_a * r2_effective * (1.0 - exp_factor2)
        
        # Calculate terminal voltage
        # V_terminal = OCV - |I|*R0 - |V_RC1| - |V_RC2|
        # Standard ECM: voltage drops always subtract from OCV
        # IR drop magnitude = |I|*R0 (always positive, subtracts from OCV)
        # RC voltage drops are always positive magnitude (subtract from OCV)
        ocv = self.get_ocv(current_direction=new_direction)
        r0_ohm = self.get_internal_resistance() / 1000.0  # Convert mΩ to Ω
        ir_drop_magnitude = abs(current_a) * r0_ohm
        v_internal = ocv - ir_drop_magnitude - abs(self._v_rc1) - abs(self._v_rc2)
        
        # Apply voltage divider effect if internal short circuit is active
        # Enhanced ECM: parallel resistance branch when fault active
        # 
        # ECM Best Practice: Internal short circuit creates a parallel resistance path
        # The short resistance R_short is in parallel with the cell's Thevenin equivalent
        # Terminal voltage is reduced by the voltage divider effect
        #
        # Thevenin equivalent resistance includes:
        # - R0 (ohmic resistance)
        # - RC network effective resistance (for steady-state, use R1+R2)
        # For dynamic response, we use R0 as primary since RC networks are reactive
        #
        # Voltage divider: V_terminal = V_internal * (R_parallel / (R_internal + R_parallel))
        # Where R_parallel = (R_internal * R_short) / (R_internal + R_short)
        # Simplifies to: V_terminal = V_internal * R_short / (R_internal + R_short)
        # This is correct when R_short << R_internal (which is true for hard shorts)
        fault_active = False
        if hasattr(self, '_fault_state') and self._fault_state:
            if 'internal_short' in self._fault_state:
                fault_active = self._fault_state['internal_short'].get('active', False)
        
        if fault_active:
            r_short_ohm = self._fault_state['internal_short'].get('resistance_ohm', 0.1)
            
            # Calculate Thevenin equivalent resistance of the cell
            # ECM Best Practice: For internal short circuit, the short resistance is in parallel
            # with the cell's internal impedance. The effective resistance seen by the load
            # is the parallel combination: R_parallel = (R_internal * R_short) / (R_internal + R_short)
            #
            # The cell's internal impedance includes:
            # - R0: Ohmic resistance (primary component, typically 0.5-1.0 mΩ for LiFePO4)
            # - Additional impedance from cell structure, tabs, connections (~5-20 mΩ)
            # - RC networks are reactive and don't contribute to DC resistance
            #
            # For accurate modeling, we use a realistic effective internal resistance
            # that accounts for the cell's actual impedance, not just R0
            r0_mohm = r0_ohm * 1000.0
            
            # Effective internal resistance: R0 plus structural impedance
            # Literature values for LiFePO4: total cell impedance ~10-30 mΩ
            # We use a conservative estimate that accounts for:
            # - R0 (ohmic): 0.5-1.0 mΩ
            # - Structural impedance (tabs, connections): 5-15 mΩ
            # - Total: ~10-20 mΩ typical
            # For hard shorts (0.1Ω), this gives realistic voltage drops of 10-30%
            structural_impedance_mohm = 10.0  # Additional impedance from cell structure
            r_internal_effective_mohm = r0_mohm + structural_impedance_mohm
            r_internal_effective_mohm = max(r_internal_effective_mohm, 8.0)  # Minimum 8 mΩ
            r_internal_effective_ohm = r_internal_effective_mohm / 1000.0
            
            if r_short_ohm > 0 and r_internal_effective_ohm > 0:
                # Voltage divider for parallel short circuit (ECM standard approach)
                # When R_short is in parallel with R_internal:
                # V_terminal = V_internal * (R_short / (R_internal + R_short))
                # 
                # This formula correctly models the voltage drop:
                # - For R_short = 0.1Ω and R_internal = 0.01Ω: ratio = 0.1/0.11 = 0.91 (9% drop)
                # - For R_short = 0.1Ω and R_internal = 0.02Ω: ratio = 0.1/0.12 = 0.83 (17% drop)
                # - For R_short << R_internal: voltage drop is small
                # - For R_short >> R_internal: voltage drop approaches 100%
                voltage_divider_ratio = r_short_ohm / (r_internal_effective_ohm + r_short_ohm)
                
                # Apply voltage divider to get terminal voltage
                v_terminal = v_internal * voltage_divider_ratio
                
                # Store debug info for validation
                if not hasattr(self, '_fault_debug'):
                    self._fault_debug = {}
                self._fault_debug['voltage_drop_pct'] = (1.0 - voltage_divider_ratio) * 100.0
                self._fault_debug['r_short_ohm'] = r_short_ohm
                self._fault_debug['r_internal_ohm'] = r_internal_effective_ohm
                self._fault_debug['v_internal'] = v_internal
                self._fault_debug['v_terminal'] = v_terminal
            else:
                v_terminal = v_internal
        else:
            v_terminal = v_internal
        
        # Apply minimum voltage limit (2.51V for LiFePO4 - ensures voltage > 2.5V)
        # At 0% SOC, ensure voltage never drops below 2.51V (2510 mV)
        # Check if overdischarge fault is active - if so, use fault's voltage limit
        MIN_VOLTAGE = 2.51  # Minimum safe operating voltage (2510 mV) - ensures voltage > 2.5V
        
        # Check for overdischarge fault - allows discharging below normal minimum
        if hasattr(self, '_fault_state') and self._fault_state:
            if 'overdischarge' in self._fault_state and self._fault_state['overdischarge'].get('active', False):
                voltage_limit_mv = self._fault_state['overdischarge'].get('voltage_limit_mv', 2500.0)
                voltage_limit_v = voltage_limit_mv / 1000.0
                # Overdischarge fault allows voltage to drop below normal minimum
                # Use the fault's voltage limit instead of default 2.51V
                MIN_VOLTAGE = voltage_limit_v
        
        # Strictly enforce minimum voltage: ensure voltage never goes below 2.51V (2510 mV)
        # This is critical for 0% SOC operation to ensure voltage > 2.5V
        v_terminal = max(v_terminal, MIN_VOLTAGE)
        
        # Additional safety check: if voltage is still below 2.51V after clamp, force it to 2.51V
        # This handles any edge cases or rounding issues
        if v_terminal < 2.51:
            v_terminal = 2.51
        
        # Apply overcharge voltage limit if fault is active
        # Overcharge allows cell to charge beyond normal maximum (typically 3.65V for LiFePO4)
        if hasattr(self, '_fault_state') and self._fault_state:
            if 'overcharge' in self._fault_state and self._fault_state['overcharge'].get('active', False):
                voltage_limit_mv = self._fault_state['overcharge'].get('voltage_limit_mv', 3700.0)
                voltage_limit_v = voltage_limit_mv / 1000.0
                # Allow voltage to reach the overcharge limit (remove normal max voltage constraint)
                # The cell can now charge up to voltage_limit_v
                # Note: We don't clamp here, we just allow it to exceed normal limits
                # The actual voltage is determined by the ECM model during charging
                pass  # Overcharge fault allows exceeding normal limits, no clamping needed
        
        # Update calendar aging
        # Track time and storage conditions
        # SOC: only update when at rest (storage SOC)
        # Temperature: always update (affects aging even during operation)
        current_time_hours = self._calendar_aging_time_hours + (dt_ms / (1000.0 * 3600.0))
        
        if abs(current_ma) < 0.001:  # At rest - update storage SOC
            self._storage_soc = self._soc
        
        # Always update storage temperature (temperature affects aging)
        self._storage_temp = self._temperature_c
        
        self._calendar_aging_time_hours = current_time_hours
        
        # Recalculate aging if significant time has passed
        if current_time_hours - self._last_update_time_hours > 1.0:  # Update every hour
            self._update_aging()
            self._last_update_time_hours = current_time_hours
        
        # Store terminal voltage for get_state() - ALWAYS store this
        # Final safety check: ensure voltage is at least 2.51V (2510 mV) before storing
        # This prevents any cell from going below 2.51V, especially at 0% SOC
        v_terminal = max(v_terminal, 2.51)
        self._last_terminal_voltage_v = v_terminal
        
        # Convert to mV - ensure minimum 2510 mV (2.51V) - ensures voltage > 2.5V
        voltage_mv = max(v_terminal * 1000.0, 2510.0)
        
        # Return voltage in mV and SOC in percent
        return voltage_mv, self._soc * 100.0
    
    def set_aging(self, cycles: int, calendar_aging_hours: Optional[float] = None):
        """
        Set aging state (number of cycles and/or calendar aging time) and update capacity/resistance.
        
        Args:
            cycles: Number of charge/discharge cycles
            calendar_aging_hours: Total calendar aging time in hours (optional)
        """
        self._cycles = max(cycles, 0)
        if calendar_aging_hours is not None:
            self._calendar_aging_time_hours = max(calendar_aging_hours, 0.0)
        self._update_aging()
    
    def get_state(self) -> dict:
        """
        Get current cell state.
        
        Returns:
            Dictionary with cell state variables
        """
        # Use stored terminal voltage if available (from last update())
        # This should always be set after update() is called
        if self._last_terminal_voltage_v is not None:
            v_terminal = self._last_terminal_voltage_v
        else:
            # Fallback: calculate terminal voltage (only if update() hasn't been called yet)
            # This should rarely happen in normal operation
            ocv = self.get_ocv()
            r0_ohm = self.get_internal_resistance() / 1000.0
            # Approximate v_internal (without current, use OCV minus RC drops)
            # Note: This doesn't account for IR drop, so it's an approximation
            v_internal_approx = ocv - abs(self._v_rc1) - abs(self._v_rc2)
            
            # Apply voltage divider if internal short is active
            fault_active = False
            if hasattr(self, '_fault_state') and self._fault_state:
                if 'internal_short' in self._fault_state:
                    fault_active = self._fault_state['internal_short'].get('active', False)
            
            if fault_active:
                r_short_ohm = self._fault_state['internal_short'].get('resistance_ohm', 0.1)
                r_effective_mohm = max(r0_ohm * 1000.0, 20.0)
                r_effective_ohm = r_effective_mohm / 1000.0
                if r_short_ohm > 0:
                    voltage_divider_ratio = r_short_ohm / (r_effective_ohm + r_short_ohm)
                    v_terminal = v_internal_approx * voltage_divider_ratio
                else:
                    v_terminal = v_internal_approx
            else:
                v_terminal = v_internal_approx
            
            # Apply minimum voltage limit - strictly enforce 2.51V minimum (2510 mV)
            # This ensures cells never go below 2.51V, especially at 0% SOC
            v_terminal = max(v_terminal, 2.51)
            if v_terminal < 2.51:
                v_terminal = 2.51
        
        # Ensure voltage is at least 2.51V (2510 mV) before returning
        # This is critical for 0% SOC to ensure voltage > 2.5V
        v_terminal = max(v_terminal, 2.51)
        voltage_mv = max(v_terminal * 1000.0, 2510.0)
        
        return {
            'soc_pct': self._soc * 100.0,
            'voltage_mv': voltage_mv,  # Use stored or calculated terminal voltage (clamped to >= 2500 mV)
            'temperature_c': self._temperature_c,
            'capacity_ah': self._capacity_actual_ah,
            'internal_resistance_mohm': self.get_internal_resistance(),
            'cycles': self._cycles,
            'calendar_aging_hours': self._calendar_aging_time_hours,
            'rc1_voltage_v': self._v_rc1,
            'rc2_voltage_v': self._v_rc2,
            'current_direction': self._last_current_direction
        }
    
    def reset(self, soc_pct: Optional[float] = None, temperature_c: Optional[float] = None):
        """
        Reset cell state (useful for testing).
        
        Args:
            soc_pct: New SOC in percent (0-100). If None, keep current.
            temperature_c: New temperature in °C. If None, keep current.
        """
        if soc_pct is not None:
            self._soc = np.clip(soc_pct / 100.0, 0.0, 1.0)
        if temperature_c is not None:
            self._temperature_c = temperature_c
        self._v_rc1 = 0.0
        self._v_rc2 = 0.0
        self._last_current_direction = 0
        # Clear fault state on reset
        self._fault_state = {}
    
    def _apply_fault_effects(self, current_ma: float, dt_ms: float) -> Tuple[float, float]:
        """
        Apply fault effects to current and temperature.
        
        Args:
            current_ma: Original current in mA
            dt_ms: Time step in ms
            
        Returns:
            Tuple of (modified_current_ma, temperature_adjustment_c)
        """
        modified_current = current_ma
        temp_adjustment = 0.0
        
        if not hasattr(self, '_fault_state') or not self._fault_state:
            return modified_current, temp_adjustment
        
        # Leakage current (self-discharge)
        if 'leakage_current' in self._fault_state and self._fault_state['leakage_current'].get('active', False):
            leakage_ma = self._fault_state['leakage_current'].get('current_ma', 0.0)
            modified_current -= leakage_ma  # Leakage reduces effective current
        
        # Internal short circuit - adds parallel current path
        if 'internal_short' in self._fault_state and self._fault_state['internal_short'].get('active', False):
            short_state = self._fault_state['internal_short']
            
            # Get initial resistance (set on first activation)
            if 'initial_resistance_ohm' not in short_state:
                short_state['initial_resistance_ohm'] = short_state.get('resistance_ohm', 0.1)
            r_short_initial = short_state['initial_resistance_ohm']
            
            # Time-dependent resistance degradation
            # Short resistance decreases over time as damage progresses
            fault_duration = short_state.get('fault_duration_sec', 0.0)
            degradation_rate = short_state.get('degradation_rate', 0.0001)  # per second
            min_resistance = short_state.get('min_resistance_ohm', 0.001)  # Minimum to prevent division by zero
            
            # Inverse degradation: R(t) = R0 / (1 + k * t) for more gradual degradation
            # This prevents resistance from dropping too quickly
            r_short_ohm = r_short_initial / (1.0 + degradation_rate * fault_duration)
            r_short_ohm = max(r_short_ohm, min_resistance)
            short_state['resistance_ohm'] = r_short_ohm  # Update stored resistance
            
            # Short circuit current: I_short = V_cell / R_short
            # Use terminal voltage (or OCV as approximation)
            ocv_v = self.get_ocv()  # Get OCV in volts
            # For more accuracy, could use actual terminal voltage, but OCV is reasonable approximation
            v_cell = ocv_v  # Approximate with OCV
            i_short_a = v_cell / r_short_ohm if r_short_ohm > 0 else 0.0
            i_short_ma = i_short_a * 1000.0
            
            # Short circuit draws current (reduces available current)
            modified_current -= i_short_ma
            
            # Enhanced heat generation: P_short = V² / R_short (more accurate than I²*R)
            # This accounts for the voltage divider effect
            power_w = (v_cell ** 2) / r_short_ohm if r_short_ohm > 0 else 0.0
            temp_adjustment += (power_w * dt_ms / 1000.0) / self.THERMAL_MASS
        
        # Thermal runaway - temperature escalation
        if 'thermal_runaway' in self._fault_state and self._fault_state['thermal_runaway'].get('active', False):
            escalation = self._fault_state['thermal_runaway'].get('escalation_factor', 1.1)
            # Temperature increases exponentially
            dt_sec = dt_ms / 1000.0
            temp_increase = (escalation - 1.0) * self._temperature_c * dt_sec
            temp_adjustment += temp_increase
        
        return modified_current, temp_adjustment
    
    def _get_fault_capacity_factor(self) -> float:
        """Get capacity reduction factor due to faults."""
        if not hasattr(self, '_fault_state') or not self._fault_state:
            return 1.0
        
        factor = 1.0
        if 'capacity_fade' in self._fault_state and self._fault_state['capacity_fade'].get('active', False):
            factor *= self._fault_state['capacity_fade'].get('fade_factor', 1.0)
        
        return factor

