# Probabilistic Fault Timing Guide

This document explains how probabilistic faults are triggered and when they occur.

## Key Difference: Deterministic vs Probabilistic

| Aspect | Deterministic | Probabilistic |
|--------|--------------|---------------|
| **Trigger Time** | Fixed (exact time/SOC) | Random (sampled from distribution) |
| **Parameters** | Fixed values | Sampled from distributions |
| **Reproducibility** | Same every run | Varies each run |
| **Use Case** | Regression testing | Risk analysis, uncertainty quantification |

## Probabilistic Timing Models

Probabilistic scenarios use **statistical models** to determine when faults trigger:

### 1. **Weibull Distribution** (Aging-Related Faults)

**Use Case:** Faults that become more likely over time (aging, wear-out)

**Parameters:**
- `shape` (β): Controls aging rate
  - β < 1: Decreasing hazard (infant mortality)
  - β = 1: Constant hazard (exponential)
  - β > 1: Increasing hazard (aging/wear-out) ← Most common
- `scale` (η): Characteristic lifetime (in seconds)

**Example:**
```yaml
timing:
  trigger_model: weibull
  shape: 2.0      # Increasing hazard (aging)
  scale: 3600.0   # 1 hour characteristic lifetime
```

**What this means:**
- Fault is **more likely** to occur as time passes
- Mean time to failure ≈ scale × Γ(1 + 1/shape)
- For shape=2.0, scale=3600s: Mean ≈ 3200 seconds (~53 minutes)
- But it's **random** - could trigger at 10 minutes or 2 hours

**Probability over time:**
- At 30 minutes (1800s): ~25% probability fault has occurred
- At 1 hour (3600s): ~63% probability fault has occurred
- At 2 hours (7200s): ~98% probability fault has occurred

### 2. **Poisson Process** (Random Fault Arrivals)

**Use Case:** Random fault arrivals with constant or time-varying rate

**Parameters:**
- `rate` (λ): Fault arrival rate (faults per second)

**Example:**
```yaml
timing:
  trigger_model: poisson
  rate: 0.0001  # 0.0001 faults per second = 1 fault per 2.78 hours on average
```

**What this means:**
- Faults arrive **randomly** with constant average rate
- Inter-arrival times follow exponential distribution
- Mean time between faults = 1/rate
- For rate=0.0001: Mean time = 10,000 seconds (~2.78 hours)

**Probability over time:**
- Probability of at least one fault by time t: P(t) = 1 - e^(-λt)
- At 1 hour (3600s): ~30% probability
- At 2 hours (7200s): ~51% probability
- At 5 hours (18000s): ~83% probability

### 3. **Exponential Distribution** (Constant Hazard Rate)

**Use Case:** Constant probability of fault over time

**Parameters:**
- `rate` (λ): Constant hazard rate

**Example:**
```yaml
timing:
  trigger_model: exponential
  rate: 0.00005  # per second
```

**What this means:**
- Constant probability of fault at any time
- Mean time to failure = 1/rate
- For rate=0.00005: Mean = 20,000 seconds (~5.56 hours)

## Probabilistic Parameter Distributions

Fault **parameters** (not just timing) are also probabilistic:

### Uniform Distribution
```yaml
parameters:
  resistance_ohm:
    distribution: uniform
    min: 0.01
    max: 0.1
```
**Meaning:** Resistance is randomly sampled between 0.01Ω and 0.1Ω

### Normal Distribution
```yaml
parameters:
  resistance_multiplier:
    distribution: normal
    mean: 1.5
    std: 0.2
```
**Meaning:** Resistance multiplier follows normal distribution (mean=1.5, std=0.2)

### Weibull Distribution (for parameters)
```yaml
parameters:
  fade_factor:
    distribution: weibull
    shape: 1.5
    scale: 0.85
```
**Meaning:** Fade factor follows Weibull distribution

## Current Probabilistic Scenarios - Timing Summary

| Scenario | Timing Model | Parameters | Mean Trigger Time | When It Happens |
|----------|-------------|------------|-------------------|-----------------|
| `internal_short_mc.yaml` | Weibull | shape=1.5, scale=7200s | ~6,400s (~1.8h) | Random, increasing probability |
| `thermal_runaway_probabilistic.yaml` | Weibull | shape=2.0, scale=3600s | ~3,200s (~53min) | Random, increasing probability |
| `capacity_fade_aging.yaml` | Weibull | shape=1.5, scale=7200s | ~6,400s (~1.8h) | Random, increasing probability |
| `resistance_increase_normal.yaml` | Poisson | rate=0.0001/s | ~10,000s (~2.8h) | Random arrivals |
| `internal_short_soft_probabilistic.yaml` | Exponential | rate=0.00005/s | ~20,000s (~5.6h) | Random, constant rate |
| `self_discharge_probabilistic.yaml` | Poisson | rate=0.0001/s | ~10,000s (~2.8h) | Random arrivals |
| `external_short_probabilistic.yaml` | Weibull | shape=2.0, scale=1800s | ~1,600s (~27min) | Random, increasing probability |

## How Long Until Fault Triggers?

### For Weibull Model:
**Cannot predict exactly** - it's random! But you can estimate:

**Example:** `thermal_runaway_probabilistic.yaml` (shape=2.0, scale=3600s)
- **50% chance** fault occurs by ~3,200 seconds (~53 minutes)
- **90% chance** fault occurs by ~5,400 seconds (~90 minutes)
- **99% chance** fault occurs by ~7,200 seconds (~2 hours)

**Formula for probability:**
```
P(fault by time t) = 1 - exp(-(t/scale)^shape)
```

### For Poisson Model:
**Cannot predict exactly** - random arrivals!

**Example:** `resistance_increase_normal.yaml` (rate=0.0001/s)
- **Mean time** = 1/0.0001 = 10,000 seconds (~2.78 hours)
- **50% chance** fault occurs by ~6,900 seconds (~1.9 hours)
- **90% chance** fault occurs by ~23,000 seconds (~6.4 hours)

**Formula for probability:**
```
P(fault by time t) = 1 - exp(-rate × t)
```

### For Exponential Model:
**Similar to Poisson** - constant hazard rate

**Example:** `internal_short_soft_probabilistic.yaml` (rate=0.00005/s)
- **Mean time** = 1/0.00005 = 20,000 seconds (~5.56 hours)
- **50% chance** fault occurs by ~13,900 seconds (~3.9 hours)
- **90% chance** fault occurs by ~46,000 seconds (~12.8 hours)

## Why Use Probabilistic Timing?

1. **Real-world uncertainty:** Real faults don't happen at exact times
2. **Risk analysis:** Quantify probability of failure
3. **Monte Carlo:** Run many simulations to understand distribution
4. **Aging modeling:** Weibull models aging-related failures accurately

## Example: Understanding Weibull Timing

**Scenario:** `thermal_runaway_probabilistic.yaml`
```yaml
timing:
  trigger_model: weibull
  shape: 2.0
  scale: 3600.0  # 1 hour
```

**What happens:**
1. At simulation start: 0% probability
2. As time passes: Probability **increases** (aging effect)
3. Each simulation run: Different trigger time (random)
4. Average trigger time: ~53 minutes, but varies widely

**In Monte Carlo run (1000 simulations):**
- Some faults trigger at 10 minutes
- Some at 1 hour
- Some at 2 hours
- Some may not trigger (if simulation ends early)
- Distribution shows the **uncertainty**

## Recommendations

### For Single Runs:
```bash
# Use --wait-for-fault to ensure you see the fault
python pc_simulator/main.py \
    --port COM3 --current 50.0 --duration 3600 \
    --fault-scenario scenarios/Probabilistic/thermal_runaway_probabilistic.yaml \
    --wait-for-fault --extend-after-fault 600 --max-duration 7200
```

### For Analysis:
```bash
# Run Monte Carlo to understand distribution
python pc_simulator/run_fault_local_no_bms.py \
    --scenario scenarios/Probabilistic/thermal_runaway_probabilistic.yaml \
    --monte-carlo --n-runs 1000 \
    --mode discharge --current 50.0 --duration 7200 \
    --statistical-analysis
```

**This will show:**
- Distribution of fault trigger times
- Mean, median, percentiles
- Probability of fault within duration

## Key Takeaways

1. **Probabilistic = Random:** Fault trigger time is **not fixed**
2. **Weibull:** Increasing probability over time (aging)
3. **Poisson/Exponential:** Constant or random arrival rate
4. **Use --wait-for-fault:** Ensures you observe fault effects
5. **Use Monte Carlo:** Understand the distribution of outcomes
6. **Longer duration:** Higher probability fault will trigger

## Probability Calculator

For Weibull (shape=β, scale=η):
```
P(fault by time t) = 1 - exp(-(t/η)^β)
```

For Poisson/Exponential (rate=λ):
```
P(fault by time t) = 1 - exp(-λ × t)
```

**Example:** Weibull(shape=2.0, scale=3600s) at t=1800s (30 min)
```
P = 1 - exp(-(1800/3600)^2) = 1 - exp(-0.25) = 1 - 0.779 = 0.221 = 22.1%
```

