# Deterministic Fault Timing Guide

This document explains how deterministic faults are triggered and when they occur.

## Fault Trigger Mechanisms

Deterministic faults can be triggered in **3 ways**:

### 1. **Time-Based Trigger** (`trigger_time_sec`)
Fault triggers at a specific **simulation time** (in seconds).

**Examples:**
- `trigger_time_sec: 60.0` → Fault triggers at **60 seconds** (1 minute)
- `trigger_time_sec: 300.0` → Fault triggers at **300 seconds** (5 minutes)
- `trigger_time_sec: 0.0` → Fault triggers **immediately** at start

**How long it takes:**
- Depends on your simulation duration
- If you run `--duration 3600`, fault at `trigger_time_sec: 300.0` triggers at **5 minutes**
- If you run `--duration 60`, fault at `trigger_time_sec: 300.0` **never triggers** (simulation ends first)

### 2. **SOC-Based Trigger** (`trigger_soc`)
Fault triggers when pack SOC reaches a specific **percentage**.

**Examples:**
- `trigger_soc: 80.0` → Fault triggers when pack SOC drops to **80%**
- `trigger_soc: 90.0` → Fault triggers when pack SOC reaches **90%** (during charge)
- `trigger_soc: 20.0` → Fault triggers when pack SOC drops to **20%**

**How long it takes:**
- Depends on:
  - Current rate (C-rate)
  - Initial SOC
  - Cell capacity
  
**Example Calculation:**
- Initial SOC: 100%
- Target SOC: 80% (20% discharge)
- Current: 50A (0.5C for 100Ah cell)
- Time to discharge 20% = (20% × 100Ah) / 50A = **0.4 hours = 24 minutes**

### 3. **Immediate Trigger** (No timing specified or `trigger_time_sec: 0.0`)
Fault is active from the **start of simulation**.

**Examples:**
- `capacity_fade.yaml` → Active immediately
- `self_discharge.yaml` → Active immediately
- `cell_imbalance.yaml` → Active immediately

## Current Deterministic Scenarios - Timing Summary

| Scenario | Trigger Type | Trigger Value | Duration | When It Happens |
|----------|-------------|---------------|----------|-----------------|
| `internal_short_hard.yaml` | SOC-based | 80% SOC | 600s (10 min) | When pack reaches 80% SOC |
| `internal_short_soft.yaml` | SOC-based | 80% SOC | 600s | When pack reaches 80% SOC |
| `external_short.yaml` | Time-based | 60 seconds | 300s (5 min) | At 1 minute, lasts 5 minutes |
| `overcharge.yaml` | SOC-based | 90% SOC | Permanent | When pack reaches 90% SOC |
| `overdischarge.yaml` | SOC-based | 10% SOC | Permanent | When pack reaches 10% SOC |
| `self_discharge.yaml` | Immediate | 0.0s | Permanent | From start |
| `open_circuit.yaml` | Time-based | 120 seconds | Permanent | At 2 minutes |
| `overheating.yaml` | Time-based | 180 seconds | Permanent | At 3 minutes |
| `thermal_runaway.yaml` | Time-based | 300 seconds | Permanent | At 5 minutes |
| `abnormal_temperature.yaml` | Time-based | 60 seconds | Permanent | At 1 minute |
| `capacity_fade.yaml` | Immediate | 0.0s | Permanent | From start |
| `resistance_increase.yaml` | Time-based | 240 seconds | Permanent | At 4 minutes |
| `lithium_plating.yaml` | Immediate | 0.0s | Permanent | From start |
| `cell_imbalance.yaml` | Immediate | 0.0s | Permanent | From start |
| `electrolyte_leakage.yaml` | Time-based | 180 seconds | Permanent | At 3 minutes |
| `sensor_offset.yaml` | Immediate | 0.0s | Permanent | From start |
| `sensor_drift.yaml` | Immediate | 0.0s | Permanent | From start |
| `insulation_fault.yaml` | Time-based | 300 seconds | Permanent | At 5 minutes |
| `thermal_propagation.yaml` | Time-based | 180 seconds | Permanent | At 3 minutes |
| `cascading_failure.yaml` | Time-based | 300 seconds | Permanent | At 5 minutes |

## How to Calculate When Fault Triggers

### For Time-Based Faults:
```
Fault triggers at: trigger_time_sec seconds
Example: trigger_time_sec: 300.0 → Fault at 5 minutes
```

### For SOC-Based Faults:
```
Time to trigger = (Initial_SOC - Trigger_SOC) × Capacity / Current

Example:
- Initial SOC: 100%
- Trigger SOC: 80%
- Capacity: 100Ah
- Current: 50A (0.5C)
- Time = (100% - 80%) × 100Ah / 50A = 20Ah / 50A = 0.4 hours = 24 minutes
```

### For Immediate Faults:
```
Fault is active from: t = 0 seconds (immediately)
```

## Examples

### Example 1: Time-Based Fault
```yaml
timing:
  trigger_time_sec: 300.0  # 5 minutes
```
**When it triggers:** Exactly at 5 minutes (300 seconds) of simulation time

**Command:**
```bash
python pc_simulator/main.py --port COM3 --current 50.0 --duration 600 --fault-scenario scenarios/Deterministic/thermal_runaway.yaml
```
**Result:** Fault triggers at 5 minutes, simulation continues until 10 minutes total

### Example 2: SOC-Based Fault
```yaml
timing:
  trigger_soc: 80.0  # 80% SOC
```
**When it triggers:** When pack SOC reaches 80% (during discharge)

**Command:**
```bash
python pc_simulator/main.py --port COM3 --current 50.0 --duration 3600 --fault-scenario scenarios/Deterministic/internal_short_hard.yaml
```
**Result:** 
- If starting at 100% SOC with 50A discharge (0.5C)
- Time to 80% SOC ≈ 24 minutes
- Fault triggers at ~24 minutes
- Fault lasts 10 minutes (until ~34 minutes)
- Simulation continues to 60 minutes total

### Example 3: Immediate Fault
```yaml
timing:
  trigger_time_sec: 0.0
```
**When it triggers:** Immediately at simulation start (t=0)

**Command:**
```bash
python pc_simulator/main.py --port COM3 --current 50.0 --duration 3600 --fault-scenario scenarios/Deterministic/capacity_fade.yaml
```
**Result:** Fault is active from the very beginning of simulation

## Important Notes

1. **Simulation Duration Matters:**
   - If `trigger_time_sec: 300.0` but you run `--duration 60`, fault **never triggers**
   - Always ensure simulation duration is longer than trigger time

2. **SOC-Based Timing Depends on Current:**
   - Higher current → Faster SOC change → Faster fault trigger
   - Lower current → Slower SOC change → Slower fault trigger
   - Zero current → SOC doesn't change → Fault never triggers (unless already at trigger SOC)

3. **Fault Duration:**
   - `duration_sec: 600` → Fault clears after 600 seconds (10 minutes)
   - No `duration_sec` → Fault is **permanent** (stays active until simulation ends)

4. **Multiple Faults:**
   - Each fault has its own timing
   - Faults can trigger at different times independently

## Quick Reference

| Timing Type | Parameter | Example | When It Triggers |
|------------|-----------|---------|------------------|
| Time-based | `trigger_time_sec` | `300.0` | At 300 seconds |
| SOC-based | `trigger_soc` | `80.0` | When SOC = 80% |
| Immediate | `trigger_time_sec: 0.0` | `0.0` | At start (t=0) |
| Permanent | No `duration_sec` | - | Until simulation ends |
| Temporary | `duration_sec` | `600` | Clears after 600s |

