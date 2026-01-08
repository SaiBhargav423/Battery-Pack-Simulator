# All Fault Injection Commands for main.py

This document provides commands to test every fault type with main.py (BMS connection).

## Base Command Structure

```bash
python pc_simulator/main.py --port COM3 --current 50.0 --duration 3600 --fault-scenario scenarios/fault_scenarios/<scenario_file>.yaml
```

---

## ELECTRICAL FAULTS

### 1. Internal Short Circuit - Hard (0.1Ω)
```bash
python pc_simulator/main.py --port COM3 --current 50.0 --duration 3600 --fault-scenario scenarios/fault_scenarios/internal_short_hard.yaml
```

### 2. Internal Short Circuit - Soft (500Ω)
```bash
python pc_simulator/main.py --port COM3 --current 50.0 --duration 3600 --fault-scenario scenarios/fault_scenarios/internal_short_soft.yaml
```

### 3. External Short Circuit
```bash
python pc_simulator/main.py --port COM3 --current 50.0 --duration 3600 --fault-scenario scenarios/fault_scenarios/external_short.yaml
```

### 4. Overcharge
```bash
python pc_simulator/main.py --port COM3 --current 50.0 --duration 3600 --fault-scenario scenarios/fault_scenarios/overcharge.yaml
```

### 5. Overdischarge
```bash
python pc_simulator/main.py --port COM3 --current -50.0 --duration 3600 --fault-scenario scenarios/fault_scenarios/overdischarge.yaml
```

### 6. Abnormal Self-Discharge (Leakage)
```bash
python pc_simulator/main.py --port COM3 --current 0.0 --duration 3600 --fault-scenario scenarios/fault_scenarios/self_discharge.yaml
```

### 7. Open Circuit
```bash
python pc_simulator/main.py --port COM3 --current 50.0 --duration 3600 --fault-scenario scenarios/fault_scenarios/open_circuit.yaml
```

---

## THERMAL FAULTS

### 8. Overheating
```bash
python pc_simulator/main.py --port COM3 --current 50.0 --duration 3600 --fault-scenario scenarios/fault_scenarios/overheating.yaml
```

### 9. Thermal Runaway
```bash
python pc_simulator/main.py --port COM3 --current 50.0 --duration 3600 --fault-scenario scenarios/fault_scenarios/thermal_runaway.yaml
```

### 10. Abnormal Temperature
```bash
python pc_simulator/main.py --port COM3 --current 50.0 --duration 3600 --fault-scenario scenarios/fault_scenarios/abnormal_temperature.yaml
```

---

## DEGRADATION/MECHANICAL FAULTS

### 11. Capacity Fade
```bash
python pc_simulator/main.py --port COM3 --current 50.0 --duration 3600 --fault-scenario scenarios/fault_scenarios/capacity_fade.yaml
```

### 12. Resistance Increase
```bash
python pc_simulator/main.py --port COM3 --current 50.0 --duration 3600 --fault-scenario scenarios/fault_scenarios/resistance_increase.yaml
```

### 13. Lithium Plating
```bash
python pc_simulator/main.py --port COM3 --current 50.0 --duration 3600 --fault-scenario scenarios/fault_scenarios/lithium_plating.yaml
```

### 14. Cell Imbalance
```bash
python pc_simulator/main.py --port COM3 --current 50.0 --duration 3600 --fault-scenario scenarios/fault_scenarios/cell_imbalance.yaml
```

### 15. Electrolyte Leakage
```bash
python pc_simulator/main.py --port COM3 --current 50.0 --duration 3600 --fault-scenario scenarios/fault_scenarios/electrolyte_leakage.yaml
```

---

## SENSOR/SYSTEM FAULTS

### 16. Sensor Offset
```bash
python pc_simulator/main.py --port COM3 --current 50.0 --duration 3600 --fault-scenario scenarios/fault_scenarios/sensor_offset.yaml
```

### 17. Sensor Drift
```bash
python pc_simulator/main.py --port COM3 --current 50.0 --duration 3600 --fault-scenario scenarios/fault_scenarios/sensor_drift.yaml
```

### 18. Insulation Fault
```bash
python pc_simulator/main.py --port COM3 --current 50.0 --duration 3600 --fault-scenario scenarios/fault_scenarios/insulation_fault.yaml
```

---

## PROPAGATION FAULTS

### 19. Thermal Propagation
```bash
python pc_simulator/main.py --port COM3 --current 50.0 --duration 3600 --fault-scenario scenarios/fault_scenarios/thermal_propagation.yaml
```

### 20. Cascading Failure
```bash
python pc_simulator/main.py --port COM3 --current 50.0 --duration 3600 --fault-scenario scenarios/fault_scenarios/cascading_failure.yaml
```

---

## ADVANCED OPTIONS

### With Bayesian Inference
```bash
python pc_simulator/main.py --port COM3 --current 50.0 --duration 3600 --fault-scenario scenarios/fault_scenarios/internal_short_hard.yaml --bayesian
```

### Continuous Mode (infinite)
```bash
python pc_simulator/main.py --port COM3 --current 50.0 --duration 0 --fault-scenario scenarios/fault_scenarios/internal_short_hard.yaml
```

### Different Protocol
```bash
python pc_simulator/main.py --port COM3 --current 50.0 --duration 3600 --protocol mcu --fault-scenario scenarios/fault_scenarios/internal_short_hard.yaml
```

---

## NOTES

- Replace `COM3` with your actual serial port
- Adjust `--current` value as needed (positive = charge, negative = discharge)
- Adjust `--duration` in seconds (0 = continuous/infinite)
- All scenarios use deterministic mode by default
- For probabilistic scenarios, use files ending with `_mc.yaml` or `_probabilistic.yaml`

