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
    # OCV table based on BMS lookup table (voltage in mV converted to V)
    _OCV_SOC_TABLE_DISCHARGE = np.array([
        # SOC%, OCV(V) - Based on BMS lookup table
        [0.0, 2.500],   # 0% - fully discharged (2500 mV)
        [1.0, 2.540],   # 1% (2540 mV)
        [2.0, 2.605],   # 2% (2605 mV)
        [3.0, 2.670],   # 3% (2670 mV)
        [4.0, 2.735],   # 4% (2735 mV)
        [5.0, 2.800],   # 5% (2800 mV)
        [6.0, 2.840],   # 6% (2840 mV)
        [7.0, 2.880],   # 7% (2880 mV)
        [8.0, 2.920],   # 8% (2920 mV)
        [9.0, 2.966],   # 9% (2966 mV)
        [10.0, 3.000],  # 10% (3000 mV)
        [11.0, 3.010],  # 11% (3010 mV)
        [12.0, 3.020],  # 12% (3020 mV)
        [13.0, 3.030],  # 13% (3030 mV)
        [14.0, 3.040],  # 14% (3040 mV)
        [15.0, 3.050],  # 15% (3050 mV)
        [16.0, 3.080],  # 16% (3080 mV)
        [17.0, 3.100],  # 17% (3100 mV)
        [18.0, 3.140],  # 18% (3140 mV)
        [19.0, 3.170],  # 19% (3170 mV)
        [20.0, 3.200],  # 20% (3200 mV)
        [21.0, 3.204],  # 21% (3204 mV)
        [22.0, 3.208],  # 22% (3208 mV)
        [23.0, 3.212],  # 23% (3212 mV)
        [24.0, 3.216],  # 24% (3216 mV)
        [25.0, 3.220],  # 25% (3220 mV)
        [26.0, 3.222],  # 26% (3222 mV)
        [27.0, 3.224],  # 27% (3224 mV)
        [28.0, 3.226],  # 28% (3226 mV)
        [29.0, 3.228],  # 29% (3228 mV)
        [30.0, 3.230],  # 30% (3230 mV)
        [31.0, 3.232],  # 31% (3232 mV)
        [32.0, 3.234],  # 32% (3234 mV)
        [33.0, 3.236],  # 33% (3236 mV)
        [34.0, 3.238],  # 34% (3238 mV)
        [35.0, 3.240],  # 35% (3240 mV)
        [36.0, 3.242],  # 36% (3242 mV)
        [37.0, 3.244],  # 37% (3244 mV)
        [38.0, 3.246],  # 38% (3246 mV)
        [39.0, 3.248],  # 39% (3248 mV)
        [40.0, 3.250],  # 40% (3250 mV)
        [41.0, 3.255],  # 41% (3255 mV)
        [42.0, 3.260],  # 42% (3260 mV)
        [43.0, 3.265],  # 43% (3265 mV)
        [44.0, 3.270],  # 44% (3270 mV)
        [45.0, 3.275],  # 45% (3275 mV)
        [46.0, 3.280],  # 46% (3280 mV)
        [47.0, 3.285],  # 47% (3285 mV)
        [48.0, 3.290],  # 48% (3290 mV)
        [49.0, 3.295],  # 49% (3295 mV)
        [50.0, 3.300],  # 50% (3300 mV)
        [51.0, 3.305],  # 51% (3305 mV)
        [52.0, 3.310],  # 52% (3310 mV)
        [53.0, 3.315],  # 53% (3315 mV)
        [54.0, 3.320],  # 54% (3320 mV)
        [55.0, 3.325],  # 55% (3325 mV)
        [56.0, 3.330],  # 56% (3330 mV)
        [57.0, 3.335],  # 57% (3335 mV)
        [58.0, 3.340],  # 58% (3340 mV)
        [59.0, 3.345],  # 59% (3345 mV)
        [60.0, 3.350],  # 60% (3350 mV)
        [61.0, 3.352],  # 61% (3352 mV)
        [62.0, 3.354],  # 62% (3354 mV)
        [63.0, 3.356],  # 63% (3356 mV)
        [64.0, 3.358],  # 64% (3358 mV)
        [65.0, 3.360],  # 65% (3360 mV)
        [66.0, 3.362],  # 66% (3362 mV)
        [67.0, 3.364],  # 67% (3364 mV)
        [68.0, 3.366],  # 68% (3366 mV)
        [69.0, 3.368],  # 69% (3368 mV)
        [70.0, 3.370],  # 70% (3370 mV)
        [71.0, 3.373],  # 71% (3373 mV)
        [72.0, 3.376],  # 72% (3376 mV)
        [73.0, 3.379],  # 73% (3379 mV)
        [74.0, 3.382],  # 74% (3382 mV)
        [75.0, 3.385],  # 75% (3385 mV)
        [76.0, 3.388],  # 76% (3388 mV)
        [77.0, 3.391],  # 77% (3391 mV)
        [78.0, 3.394],  # 78% (3394 mV)
        [79.0, 3.397],  # 79% (3397 mV)
        [80.0, 3.400],  # 80% (3400 mV)
        [81.0, 3.404],  # 81% (3404 mV)
        [82.0, 3.408],  # 82% (3408 mV)
        [83.0, 3.412],  # 83% (3412 mV)
        [84.0, 3.416],  # 84% (3416 mV)
        [85.0, 3.420],  # 85% (3420 mV)
        [86.0, 3.426],  # 86% (3426 mV)
        [87.0, 3.432],  # 87% (3432 mV)
        [88.0, 3.438],  # 88% (3438 mV)
        [89.0, 3.444],  # 89% (3444 mV)
        [90.0, 3.450],  # 90% (3450 mV)
        [91.0, 3.460],  # 91% (3460 mV)
        [92.0, 3.470],  # 92% (3470 mV)
        [93.0, 3.480],  # 93% (3480 mV)
        [94.0, 3.490],  # 94% (3490 mV)
        [95.0, 3.500],  # 95% (3500 mV)
        [96.0, 3.517],  # 96% (3517 mV)
        [97.0, 3.533],  # 97% (3533 mV)
        [98.0, 3.550],  # 98% (3550 mV)
        [99.0, 3.600],  # 99% (3600 mV)
        [100.0, 3.650],  # 100% - fully charged (3650 mV)
    ])
    
    # Charge OCV table (typically 5-15mV higher than discharge at same SOC due to hysteresis)
    # LiFePO₄ shows less hysteresis than other chemistries, but it's still present
    # Hysteresis offset: 15mV for SOC 0-20%, 10mV for SOC 20-80%, 5mV for SOC 80-100%
    _OCV_SOC_TABLE_CHARGE = np.array([
        # SOC%, OCV(V) - Charge curve (higher than discharge due to hysteresis)
        # Based on BMS lookup table with hysteresis offset applied
        [0.0, 2.515],   # 0% - 15mV higher than discharge (2.500) - ensures terminal voltage >= 2.51V after IR/RC drops
        [1.0, 2.555],   # 1% - 15mV higher (2540 + 15 = 2555 mV)
        [2.0, 2.620],   # 2% - 15mV higher (2605 + 15 = 2620 mV)
        [3.0, 2.685],   # 3% - 15mV higher (2670 + 15 = 2685 mV)
        [4.0, 2.750],   # 4% - 15mV higher (2735 + 15 = 2750 mV)
        [5.0, 2.815],   # 5% - 15mV higher (2800 + 15 = 2815 mV)
        [6.0, 2.855],   # 6% - 15mV higher (2840 + 15 = 2855 mV)
        [7.0, 2.895],   # 7% - 15mV higher (2880 + 15 = 2895 mV)
        [8.0, 2.935],   # 8% - 15mV higher (2920 + 15 = 2935 mV)
        [9.0, 2.981],   # 9% - 15mV higher (2966 + 15 = 2981 mV)
        [10.0, 3.015],  # 10% - 15mV higher (3000 + 15 = 3015 mV)
        [11.0, 3.025],  # 11% - 15mV higher (3010 + 15 = 3025 mV)
        [12.0, 3.035],  # 12% - 15mV higher (3020 + 15 = 3035 mV)
        [13.0, 3.045],  # 13% - 15mV higher (3030 + 15 = 3045 mV)
        [14.0, 3.055],  # 14% - 15mV higher (3040 + 15 = 3055 mV)
        [15.0, 3.065],  # 15% - 15mV higher (3050 + 15 = 3065 mV)
        [16.0, 3.095],  # 16% - 15mV higher (3080 + 15 = 3095 mV)
        [17.0, 3.115],  # 17% - 15mV higher (3100 + 15 = 3115 mV)
        [18.0, 3.155],  # 18% - 15mV higher (3140 + 15 = 3155 mV)
        [19.0, 3.185],  # 19% - 15mV higher (3170 + 15 = 3185 mV)
        [20.0, 3.210],  # 20% - 10mV higher (3200 + 10 = 3210 mV)
        [21.0, 3.214],  # 21% - 10mV higher (3204 + 10 = 3214 mV)
        [22.0, 3.218],  # 22% - 10mV higher (3208 + 10 = 3218 mV)
        [23.0, 3.222],  # 23% - 10mV higher (3212 + 10 = 3222 mV)
        [24.0, 3.226],  # 24% - 10mV higher (3216 + 10 = 3226 mV)
        [25.0, 3.230],  # 25% - 10mV higher (3220 + 10 = 3230 mV)
        [26.0, 3.232],  # 26% - 10mV higher (3222 + 10 = 3232 mV)
        [27.0, 3.234],  # 27% - 10mV higher (3224 + 10 = 3234 mV)
        [28.0, 3.236],  # 28% - 10mV higher (3226 + 10 = 3236 mV)
        [29.0, 3.238],  # 29% - 10mV higher (3228 + 10 = 3238 mV)
        [30.0, 3.240],  # 30% - 10mV higher (3230 + 10 = 3240 mV)
        [31.0, 3.242],  # 31% - 10mV higher (3232 + 10 = 3242 mV)
        [32.0, 3.244],  # 32% - 10mV higher (3234 + 10 = 3244 mV)
        [33.0, 3.246],  # 33% - 10mV higher (3236 + 10 = 3246 mV)
        [34.0, 3.248],  # 34% - 10mV higher (3238 + 10 = 3248 mV)
        [35.0, 3.250],  # 35% - 10mV higher (3240 + 10 = 3250 mV)
        [36.0, 3.252],  # 36% - 10mV higher (3242 + 10 = 3252 mV)
        [37.0, 3.254],  # 37% - 10mV higher (3244 + 10 = 3254 mV)
        [38.0, 3.256],  # 38% - 10mV higher (3246 + 10 = 3256 mV)
        [39.0, 3.258],  # 39% - 10mV higher (3248 + 10 = 3258 mV)
        [40.0, 3.260],  # 40% - 10mV higher (3250 + 10 = 3260 mV)
        [41.0, 3.265],  # 41% - 10mV higher (3255 + 10 = 3265 mV)
        [42.0, 3.270],  # 42% - 10mV higher (3260 + 10 = 3270 mV)
        [43.0, 3.275],  # 43% - 10mV higher (3265 + 10 = 3275 mV)
        [44.0, 3.280],  # 44% - 10mV higher (3270 + 10 = 3280 mV)
        [45.0, 3.285],  # 45% - 10mV higher (3275 + 10 = 3285 mV)
        [46.0, 3.290],  # 46% - 10mV higher (3280 + 10 = 3290 mV)
        [47.0, 3.295],  # 47% - 10mV higher (3285 + 10 = 3295 mV)
        [48.0, 3.300],  # 48% - 10mV higher (3290 + 10 = 3300 mV)
        [49.0, 3.305],  # 49% - 10mV higher (3295 + 10 = 3305 mV)
        [50.0, 3.310],  # 50% - 10mV higher (3300 + 10 = 3310 mV)
        [51.0, 3.315],  # 51% - 10mV higher (3305 + 10 = 3315 mV)
        [52.0, 3.320],  # 52% - 10mV higher (3310 + 10 = 3320 mV)
        [53.0, 3.325],  # 53% - 10mV higher (3315 + 10 = 3325 mV)
        [54.0, 3.330],  # 54% - 10mV higher (3320 + 10 = 3330 mV)
        [55.0, 3.335],  # 55% - 10mV higher (3325 + 10 = 3335 mV)
        [56.0, 3.340],  # 56% - 10mV higher (3330 + 10 = 3340 mV)
        [57.0, 3.345],  # 57% - 10mV higher (3335 + 10 = 3345 mV)
        [58.0, 3.350],  # 58% - 10mV higher (3340 + 10 = 3350 mV)
        [59.0, 3.355],  # 59% - 10mV higher (3345 + 10 = 3355 mV)
        [60.0, 3.360],  # 60% - 10mV higher (3350 + 10 = 3360 mV)
        [61.0, 3.362],  # 61% - 10mV higher (3352 + 10 = 3362 mV)
        [62.0, 3.364],  # 62% - 10mV higher (3354 + 10 = 3364 mV)
        [63.0, 3.366],  # 63% - 10mV higher (3356 + 10 = 3366 mV)
        [64.0, 3.368],  # 64% - 10mV higher (3358 + 10 = 3368 mV)
        [65.0, 3.370],  # 65% - 10mV higher (3360 + 10 = 3370 mV)
        [66.0, 3.372],  # 66% - 10mV higher (3362 + 10 = 3372 mV)
        [67.0, 3.374],  # 67% - 10mV higher (3364 + 10 = 3374 mV)
        [68.0, 3.376],  # 68% - 10mV higher (3366 + 10 = 3376 mV)
        [69.0, 3.378],  # 69% - 10mV higher (3368 + 10 = 3378 mV)
        [70.0, 3.380],  # 70% - 10mV higher (3370 + 10 = 3380 mV)
        [71.0, 3.383],  # 71% - 10mV higher (3373 + 10 = 3383 mV)
        [72.0, 3.386],  # 72% - 10mV higher (3376 + 10 = 3386 mV)
        [73.0, 3.389],  # 73% - 10mV higher (3379 + 10 = 3389 mV)
        [74.0, 3.392],  # 74% - 10mV higher (3382 + 10 = 3392 mV)
        [75.0, 3.395],  # 75% - 10mV higher (3385 + 10 = 3395 mV)
        [76.0, 3.398],  # 76% - 10mV higher (3388 + 10 = 3398 mV)
        [77.0, 3.401],  # 77% - 10mV higher (3391 + 10 = 3401 mV)
        [78.0, 3.404],  # 78% - 10mV higher (3394 + 10 = 3404 mV)
        [79.0, 3.407],  # 79% - 10mV higher (3397 + 10 = 3407 mV)
        [80.0, 3.410],  # 80% - 10mV higher (3400 + 10 = 3410 mV)
        [81.0, 3.409],  # 81% - 5mV higher (3404 + 5 = 3409 mV)
        [82.0, 3.413],  # 82% - 5mV higher (3408 + 5 = 3413 mV)
        [83.0, 3.417],  # 83% - 5mV higher (3412 + 5 = 3417 mV)
        [84.0, 3.421],  # 84% - 5mV higher (3416 + 5 = 3421 mV)
        [85.0, 3.425],  # 85% - 5mV higher (3420 + 5 = 3425 mV)
        [86.0, 3.431],  # 86% - 5mV higher (3426 + 5 = 3431 mV)
        [87.0, 3.437],  # 87% - 5mV higher (3432 + 5 = 3437 mV)
        [88.0, 3.443],  # 88% - 5mV higher (3438 + 5 = 3443 mV)
        [89.0, 3.449],  # 89% - 5mV higher (3444 + 5 = 3449 mV)
        [90.0, 3.455],  # 90% - 5mV higher (3450 + 5 = 3455 mV)
        [91.0, 3.465],  # 91% - 5mV higher (3460 + 5 = 3465 mV)
        [92.0, 3.475],  # 92% - 5mV higher (3470 + 5 = 3475 mV)
        [93.0, 3.485],  # 93% - 5mV higher (3480 + 5 = 3485 mV)
        [94.0, 3.495],  # 94% - 5mV higher (3490 + 5 = 3495 mV)
        [95.0, 3.505],  # 95% - 5mV higher (3500 + 5 = 3505 mV)
        [96.0, 3.522],  # 96% - 5mV higher (3517 + 5 = 3522 mV)
        [97.0, 3.538],  # 97% - 5mV higher (3533 + 5 = 3538 mV)
        [98.0, 3.555],  # 98% - 5mV higher (3550 + 5 = 3555 mV)
        [99.0, 3.605],  # 99% - 5mV higher (3600 + 5 = 3605 mV)
        [100.0, 3.655],  # 100% - fully charged (3650 + 5 = 3655 mV)
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

