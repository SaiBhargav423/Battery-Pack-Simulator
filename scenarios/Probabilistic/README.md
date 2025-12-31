# Probabilistic Fault Scenarios

This folder contains probabilistic fault scenarios that demonstrate the Monte Carlo framework and probabilistic modeling capabilities.

## Available Scenarios

### 1. **internal_short_mc.yaml** - Basic Monte Carlo
- **Feature**: Uniform distribution for resistance
- **Timing**: Weibull model
- **Use Case**: Basic probabilistic internal short circuit
- **Command**: 
  ```bash
  python pc_simulator/run_fault_local_no_bms.py --scenario scenarios/Probabilistic/internal_short_mc.yaml --monte-carlo --n-runs 1000 --mode discharge --current 50.0 --duration 3600 --statistical-analysis
  ```

### 2. **internal_short_soft_probabilistic.yaml** - Soft Short with Exponential Timing
- **Feature**: Uniform resistance (100-1000Ω), Exponential timing
- **Timing**: Exponential distribution (constant hazard rate)
- **Use Case**: Random fault arrivals
- **Command**: 
  ```bash
  python pc_simulator/run_fault_local_no_bms.py --scenario scenarios/Probabilistic/internal_short_soft_probabilistic.yaml --monte-carlo --n-runs 800 --mode discharge --current 50.0 --duration 3600 --statistical-analysis
  ```

### 3. **thermal_runaway_probabilistic.yaml** - Thermal Runaway with Weibull
- **Feature**: Uniform escalation factor, Weibull timing
- **Timing**: Weibull distribution (aging-related)
- **Use Case**: Time-dependent thermal escalation
- **Command**: 
  ```bash
  python pc_simulator/run_fault_local_no_bms.py --scenario scenarios/Probabilistic/thermal_runaway_probabilistic.yaml --monte-carlo --n-runs 1000 --mode discharge --current 50.0 --duration 3600 --statistical-analysis
  ```

### 4. **capacity_fade_aging.yaml** - Capacity Fade with Weibull Aging
- **Feature**: Weibull distribution for fade factor
- **Timing**: Weibull model (aging-related)
- **Use Case**: Degradation modeling
- **Command**: 
  ```bash
  python pc_simulator/run_fault_local_no_bms.py --scenario scenarios/Probabilistic/capacity_fade_aging.yaml --monte-carlo --n-runs 500 --mode discharge --current 50.0 --duration 3600 --statistical-analysis
  ```

### 5. **resistance_increase_normal.yaml** - Normal Distribution + Poisson
- **Feature**: Normal distribution for resistance multiplier
- **Timing**: Poisson process (random arrivals)
- **Use Case**: Statistical resistance increase
- **Command**: 
  ```bash
  python pc_simulator/run_fault_local_no_bms.py --scenario scenarios/Probabilistic/resistance_increase_normal.yaml --monte-carlo --n-runs 800 --sampling-strategy sobol --mode discharge --current 50.0 --duration 3600 --statistical-analysis
  ```

### 6. **external_short_probabilistic.yaml** - External Short with Variable Duration
- **Feature**: Uniform resistance, Weibull timing, variable duration
- **Timing**: Weibull trigger, uniform duration
- **Use Case**: Pack-level fault with uncertainty
- **Command**: 
  ```bash
  python pc_simulator/run_fault_local_no_bms.py --scenario scenarios/Probabilistic/external_short_probabilistic.yaml --monte-carlo --n-runs 1000 --mode discharge --current 50.0 --duration 3600 --statistical-analysis
  ```

### 7. **self_discharge_probabilistic.yaml** - Self-Discharge with Normal Distribution
- **Feature**: Normal distribution for leakage current
- **Timing**: Poisson process
- **Use Case**: Statistical leakage modeling
- **Command**: 
  ```bash
  python pc_simulator/run_fault_local_no_bms.py --scenario scenarios/Probabilistic/self_discharge_probabilistic.yaml --monte-carlo --n-runs 800 --sampling-strategy random --mode discharge --current 0.0 --duration 3600 --statistical-analysis
  ```

### 8. **cell_imbalance_probabilistic.yaml** - Cell Imbalance with Multiple Distributions
- **Feature**: Uniform SOC variation, Normal capacity variation
- **Timing**: Fixed trigger
- **Use Case**: Pack-level imbalance uncertainty
- **Command**: 
  ```bash
  python pc_simulator/run_fault_local_no_bms.py --scenario scenarios/Probabilistic/cell_imbalance_probabilistic.yaml --monte-carlo --n-runs 600 --mode discharge --current 50.0 --duration 3600 --statistical-analysis
  ```

### 9. **multiple_faults_correlated.yaml** - Correlated Faults with Copula
- **Feature**: Multiple faults with Gaussian copula correlation
- **Timing**: Weibull for both faults
- **Use Case**: Thermal propagation with correlated faults
- **Command**: 
  ```bash
  python pc_simulator/run_fault_local_no_bms.py --scenario scenarios/Probabilistic/multiple_faults_correlated.yaml --monte-carlo --n-runs 1000 --mode discharge --current 50.0 --duration 3600 --statistical-analysis
  ```

### 10. **combined_degradation.yaml** - Multiple Degradation Faults
- **Feature**: Capacity fade + resistance increase with correlation
- **Timing**: Weibull for both (correlated)
- **Use Case**: Combined aging effects
- **Command**: 
  ```bash
  python pc_simulator/run_fault_local_no_bms.py --scenario scenarios/Probabilistic/combined_degradation.yaml --monte-carlo --n-runs 1000 --mode discharge --current 50.0 --duration 3600 --statistical-analysis
  ```

## Probabilistic Features Demonstrated

### Parameter Distributions:
- **Uniform**: `internal_short_mc.yaml`, `internal_short_soft_probabilistic.yaml`
- **Normal**: `resistance_increase_normal.yaml`, `self_discharge_probabilistic.yaml`
- **Weibull**: `capacity_fade_aging.yaml` (for aging parameters)

### Timing Models:
- **Weibull**: Aging-related faults (`thermal_runaway_probabilistic.yaml`, `capacity_fade_aging.yaml`)
- **Poisson**: Random fault arrivals (`resistance_increase_normal.yaml`, `self_discharge_probabilistic.yaml`)
- **Exponential**: Constant hazard rate (`internal_short_soft_probabilistic.yaml`)

### Advanced Features:
- **Correlated Faults**: `multiple_faults_correlated.yaml` (Gaussian copula)
- **Multiple Distributions**: `cell_imbalance_probabilistic.yaml` (uniform + normal)
- **Variable Duration**: `external_short_probabilistic.yaml`
- **Combined Faults**: `combined_degradation.yaml`

## Sampling Strategies

- **LHS (Latin Hypercube)**: Better coverage, recommended for most cases
- **Sobol**: Quasi-Monte Carlo, faster convergence
- **Random**: Standard random sampling

## Statistical Analysis Output

When using `--statistical-analysis`, you get:
- `ensemble_results.csv` - All run results
- `statistics_summary.csv` - Mean, std, percentiles, confidence intervals
- `soc_distribution.png` - Distribution plot
- `voltage_distribution.png` - Distribution plot

## Handling Fault Timing in Probabilistic Scenarios

### The Problem
In probabilistic scenarios, faults may trigger at random times (or not at all). Using a fixed `--duration 3600` means:
- If fault triggers at 3500s, you only see 100s of fault effects
- If fault never triggers, simulation completes without fault
- You can't observe full fault progression

### Solutions

#### Option 1: Wait for Fault (Recommended)
```bash
# Wait for fault to trigger, then extend simulation
python pc_simulator/run_fault_local_no_bms.py \
    --scenario scenarios/Probabilistic/multiple_faults_correlated.yaml \
    --mode discharge --current 50.0 --duration 3600 \
    --wait-for-fault \
    --extend-after-fault 600 \
    --max-duration 7200
```

**What this does:**
- Waits up to `--max-duration` (7200s) for fault to trigger
- Once fault triggers, extends simulation by `--extend-after-fault` (600s)
- Ensures you observe full fault effects

#### Option 2: Fixed Duration (For Monte Carlo)
```bash
# For MC ensemble, use fixed duration but track trigger times
python pc_simulator/run_fault_local_no_bms.py \
    --scenario scenarios/Probabilistic/multiple_faults_correlated.yaml \
    --monte-carlo --n-runs 1000 \
    --mode discharge --current 50.0 --duration 3600 \
    --statistical-analysis
```

**What this does:**
- Runs fixed 3600s for each MC run
- Tracks `fault_trigger_times_sec` in results
- You can filter results by whether fault triggered
- Statistical analysis includes fault trigger time statistics

#### Option 3: Long Duration (Simple)
```bash
# Use very long duration to ensure fault triggers
python pc_simulator/run_fault_local_no_bms.py \
    --scenario scenarios/Probabilistic/multiple_faults_correlated.yaml \
    --mode discharge --current 50.0 --duration 14400 \
    --statistical-analysis
```

**What this does:**
- Runs for 4 hours (14400s)
- Higher probability fault will trigger
- Simple but less efficient

### Recommended Approach

**For single runs:** Use `--wait-for-fault --extend-after-fault 600`
**For Monte Carlo:** Use fixed duration, analyze `fault_trigger_times_sec` in results

