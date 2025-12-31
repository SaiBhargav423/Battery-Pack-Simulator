"""
Fault Injection Simulation Runner (Local - No BMS Connection)

This script runs battery pack simulations with fault injection for analysis purposes.
It does NOT connect to BMS hardware - use main.py for BMS testing.

This script supports:
- Deterministic and probabilistic fault injection
- Monte Carlo ensemble runs
- Time-dependent fault probabilities
- Correlated fault modeling
- Statistical analysis

IMPORTANT: When adding new fault injection features/options to this file,
ALSO update main.py to maintain feature parity for BMS testing!
"""

import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import time
from pathlib import Path
from typing import Optional, List
import yaml

from plant.pack_model import BatteryPack16S
from plant.run_cell_simulation import run_simulation
from fault_injection.fault_framework import FaultInjector, FaultMode
from fault_injection.fault_scenarios import load_scenario, create_fault_injector_from_scenario
from fault_injection.monte_carlo import MonteCarloFaultInjector, EnsembleStatistics
from fault_injection.statistical_analysis import EnsembleAnalyzer, RiskQuantifier


def run_fault_simulation(
    scenario_file: str,
    mode: str = 'discharge',
    current_amp: float = 1.0,
    duration_sec: Optional[float] = None,
    target_soc_pct: Optional[float] = None,
    initial_soc_pct: float = 100.0,
    dt_ms: float = 100.0,
    temperature_c: float = 25.0,
    monte_carlo: bool = False,
    n_runs: int = 100,
    sampling_strategy: str = 'lhs',
    statistical_analysis: bool = False,
    output_dir: str = 'output',
    save_plots: bool = True
):
    """
    Run fault injection simulation.
    
    Args:
        scenario_file: Path to YAML fault scenario file
        mode: 'charge' or 'discharge'
        current_amp: Current in Amperes
        duration_sec: Simulation duration in seconds (None = use target_soc)
        target_soc_pct: Target SOC in percent (None = use duration)
        initial_soc_pct: Initial SOC in percent
        dt_ms: Time step in milliseconds
        temperature_c: Ambient temperature in °C
        monte_carlo: Enable Monte Carlo ensemble runs
        n_runs: Number of MC runs
        sampling_strategy: 'lhs', 'sobol', or 'random'
        statistical_analysis: Enable statistical analysis
        output_dir: Output directory for results
        save_plots: Save plots
    """
    # Load scenario
    scenario = load_scenario(scenario_file)
    scenario_name = scenario.get('name', 'fault_simulation')
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    if monte_carlo:
        # Run Monte Carlo ensemble
        print(f"Running Monte Carlo ensemble: {n_runs} runs with {sampling_strategy} sampling...")
        results = run_monte_carlo_ensemble(
            scenario, mode, current_amp, duration_sec, target_soc_pct,
            initial_soc_pct, dt_ms, temperature_c, n_runs, sampling_strategy
        )
        
        # Save ensemble results
        results_df = pd.DataFrame(results)
        results_df.to_csv(output_path / 'ensemble_results.csv', index=False)
        
        if statistical_analysis:
            # Perform statistical analysis
            analyzer = EnsembleAnalyzer()
            stats = analyzer.compute_ensemble_stats(results, metric_name='final_soc_pct')
            
            # Save statistics
            stats_df = pd.DataFrame([stats])
            stats_df.to_csv(output_path / 'statistics_summary.csv', index=False)
            
            print("\nStatistical Summary:")
            for key, value in stats.items():
                print(f"  {key}: {value:.4f}")
        
        if save_plots:
            # Create plots
            create_ensemble_plots(results, output_path)
    else:
        # Single simulation run
        print(f"Running single simulation with scenario: {scenario_name}")
        result = run_single_fault_simulation(
            scenario, mode, current_amp, duration_sec, target_soc_pct,
            initial_soc_pct, dt_ms, temperature_c,
            wait_for_fault=wait_for_fault,
            extend_after_fault=extend_after_fault,
            max_duration_sec=max_duration_sec
        )
        
        # Save result
        result_df = pd.DataFrame([result])
        result_df.to_csv(output_path / 'simulation_result.csv', index=False)
        
        print(f"\nSimulation completed:")
        print(f"  Final SOC: {result.get('final_soc_pct', 0):.2f}%")
        print(f"  Final Voltage: {result.get('final_voltage_mv', 0)/1000:.2f}V")
    
    print(f"\nResults saved to: {output_path}")


def run_single_fault_simulation(
    scenario: dict,
    mode: str,
    current_amp: float,
    duration_sec: Optional[float],
    target_soc_pct: Optional[float],
    initial_soc_pct: float,
    dt_ms: float,
    temperature_c: float,
    wait_for_fault: bool = False,
    extend_after_fault: Optional[float] = None,
    max_duration_sec: Optional[float] = None
) -> dict:
    """Run single fault injection simulation."""
    # Create fault injector
    fault_injector = create_fault_injector_from_scenario(scenario)
    
    # Create pack
    pack = BatteryPack16S(
        cell_capacity_ah=100.0,
        initial_soc_pct=initial_soc_pct,
        ambient_temp_c=temperature_c,
        seed=scenario.get('seed', 42)
    )
    
    # Determine current direction
    current_ma = current_amp * 1000.0
    if mode == 'charge':
        current_ma = abs(current_ma)
    else:  # discharge
        current_ma = -abs(current_ma)
    
    # Simulation loop
    step = 0
    elapsed_time = 0.0
    max_steps = 1000000  # Safety limit
    
    # Data storage
    time_data = []
    soc_data = []
    voltage_data = []
    
    # Determine stopping condition
    fault_triggered = False
    first_fault_time = None
    
    if duration_sec is not None:
        target_time = duration_sec
        
        # If wait_for_fault, extend target_time if fault hasn't triggered
        if wait_for_fault:
            # Check if any fault will trigger within reasonable time
            # For probabilistic scenarios, we'll wait up to max_duration_sec
            max_wait_time = max_duration_sec if max_duration_sec is not None else target_time * 10
            target_time = max_wait_time
        
        while elapsed_time < target_time and step < max_steps:
            # Update fault injector
            pack_state = pack.get_pack_state()
            fault_injector.update(elapsed_time * 1000.0, pack_state)
            
            # Check if fault just triggered
            if not fault_triggered:
                fault_stats = fault_injector.get_statistics()
                if fault_stats['active_faults'] > 0:
                    fault_triggered = True
                    first_fault_time = elapsed_time
                    print(f"  [Fault Triggered] First fault at {elapsed_time:.1f} seconds")
                    
                    # If extend_after_fault is set, extend simulation duration
                    if extend_after_fault is not None:
                        target_time = elapsed_time + extend_after_fault
                        print(f"  [Extended] Simulation extended to {target_time:.1f} seconds to observe fault effects")
            
            # Apply faults to pack
            fault_injector.apply_to_pack(pack)
            
            # Apply faults to cells
            for i, cell in enumerate(pack._cells):
                fault_injector.apply_to_cell(cell, i)
            
            # Update pack
            pack.update(current_ma=current_ma, dt_ms=dt_ms, ambient_temp_c=temperature_c)
            
            # Store data
            time_data.append(elapsed_time)
            soc_data.append(pack.get_pack_soc())
            voltage_data.append(pack.get_pack_voltage())
            
            step += 1
            elapsed_time += dt_ms / 1000.0
            
            # If wait_for_fault and fault triggered, check if we should stop
            if wait_for_fault and fault_triggered:
                # If extend_after_fault is None, stop shortly after fault triggers
                if extend_after_fault is None:
                    # Default: continue for 10% of original duration or 60 seconds, whichever is smaller
                    post_fault_duration = min(duration_sec * 0.1 if duration_sec else 60.0, 60.0)
                    if elapsed_time >= first_fault_time + post_fault_duration:
                        print(f"  [Stopping] {post_fault_duration:.1f} seconds after fault trigger")
                        break
    else:
        # Stop at target SOC
        target_soc = target_soc_pct
        if mode == 'discharge':
            while pack.get_pack_soc() > target_soc and step < max_steps:
                pack_state = pack.get_pack_state()
                fault_injector.update(elapsed_time * 1000.0, pack_state)
                fault_injector.apply_to_pack(pack)
                for i, cell in enumerate(pack._cells):
                    fault_injector.apply_to_cell(cell, i)
                pack.update(current_ma=current_ma, dt_ms=dt_ms, ambient_temp_c=temperature_c)
                time_data.append(elapsed_time)
                soc_data.append(pack.get_pack_soc())
                voltage_data.append(pack.get_pack_voltage())
                step += 1
                elapsed_time += dt_ms / 1000.0
        else:  # charge
            while pack.get_pack_soc() < target_soc and step < max_steps:
                pack_state = pack.get_pack_state()
                fault_injector.update(elapsed_time * 1000.0, pack_state)
                fault_injector.apply_to_pack(pack)
                for i, cell in enumerate(pack._cells):
                    fault_injector.apply_to_cell(cell, i)
                pack.update(current_ma=current_ma, dt_ms=dt_ms, ambient_temp_c=temperature_c)
                time_data.append(elapsed_time)
                soc_data.append(pack.get_pack_soc())
                voltage_data.append(pack.get_pack_voltage())
                step += 1
                elapsed_time += dt_ms / 1000.0
    
    # Get fault statistics
    fault_stats = fault_injector.get_statistics()
    fault_trigger_times = []
    for fault_state in fault_injector._fault_states:
        if fault_state.triggered and fault_state.trigger_time is not None:
            fault_trigger_times.append(fault_state.trigger_time)
    
    return {
        'final_soc_pct': pack.get_pack_soc(),
        'final_voltage_mv': pack.get_pack_voltage(),
        'duration_sec': elapsed_time,
        'n_steps': step,
        'faults_triggered': fault_stats['active_faults'],
        'fault_trigger_times_sec': fault_trigger_times,
        'first_fault_time_sec': min(fault_trigger_times) if fault_trigger_times else None
    }


def run_monte_carlo_ensemble(
    scenario: dict,
    mode: str,
    current_amp: float,
    duration_sec: Optional[float],
    target_soc_pct: Optional[float],
    initial_soc_pct: float,
    dt_ms: float,
    temperature_c: float,
    n_runs: int,
    sampling_strategy: str
) -> List[dict]:
    """Run Monte Carlo ensemble of simulations."""
    results = []
    
    for run_id in range(n_runs):
        if (run_id + 1) % 10 == 0:
            print(f"  Run {run_id + 1}/{n_runs}...")
        
        # Create new fault injector for each run (with different seed)
        scenario_copy = scenario.copy()
        scenario_copy['seed'] = scenario.get('seed', 42) + run_id
        fault_injector = create_fault_injector_from_scenario(scenario_copy)
        
        # Run simulation
        result = run_single_fault_simulation(
            scenario_copy, mode, current_amp, duration_sec, target_soc_pct,
            initial_soc_pct, dt_ms, temperature_c,
            wait_for_fault=False,  # For MC, use fixed duration
            extend_after_fault=None,
            max_duration_sec=None
        )
        result['run_id'] = run_id
        results.append(result)
    
    return results


def create_ensemble_plots(results: List[dict], output_path: Path):
    """Create plots for ensemble results."""
    df = pd.DataFrame(results)
    
    # Distribution plot
    plt.figure(figsize=(10, 6))
    plt.hist(df['final_soc_pct'], bins=50, edgecolor='black', alpha=0.7)
    plt.xlabel('Final SOC (%)')
    plt.ylabel('Frequency')
    plt.title('Distribution of Final SOC')
    plt.grid(True, alpha=0.3)
    plt.savefig(output_path / 'soc_distribution.png', dpi=150)
    plt.close()
    
    # Voltage distribution
    plt.figure(figsize=(10, 6))
    plt.hist(df['final_voltage_mv'] / 1000.0, bins=50, edgecolor='black', alpha=0.7)
    plt.xlabel('Final Voltage (V)')
    plt.ylabel('Frequency')
    plt.title('Distribution of Final Voltage')
    plt.grid(True, alpha=0.3)
    plt.savefig(output_path / 'voltage_distribution.png', dpi=150)
    plt.close()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Run fault injection simulation (Local - No BMS Connection). '
                   'Use main.py for BMS hardware testing.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single simulation with fault
  python run_fault_local_no_bms.py --scenario scenarios/Deterministic/internal_short_hard.yaml --mode discharge --current 50.0 --duration 3600
  
  # Monte Carlo ensemble
  python run_fault_local_no_bms.py --scenario scenarios/Probabilistic/internal_short_mc.yaml --monte-carlo --n-runs 1000 --mode discharge --current 50.0 --duration 3600 --statistical-analysis
        """
    )
    parser.add_argument('--scenario', type=str, required=True,
                       help='Path to YAML fault scenario file')
    parser.add_argument('--mode', type=str, default='discharge',
                       choices=['charge', 'discharge'],
                       help='Simulation mode')
    parser.add_argument('--current', type=float, default=1.0,
                       help='Current in Amperes')
    parser.add_argument('--duration', type=float, default=None,
                       help='Duration in seconds')
    parser.add_argument('--target-soc', type=float, default=None,
                       help='Target SOC in percent')
    parser.add_argument('--initial-soc', type=float, default=100.0,
                       help='Initial SOC in percent')
    parser.add_argument('--dt', type=float, default=100.0,
                       help='Time step in milliseconds')
    parser.add_argument('--temperature', type=float, default=25.0,
                       help='Ambient temperature in °C')
    parser.add_argument('--monte-carlo', action='store_true',
                       help='Enable Monte Carlo ensemble runs')
    parser.add_argument('--n-runs', type=int, default=100,
                       help='Number of MC runs')
    parser.add_argument('--sampling-strategy', type=str, default='lhs',
                       choices=['lhs', 'sobol', 'random'],
                       help='MC sampling strategy')
    parser.add_argument('--statistical-analysis', action='store_true',
                       help='Enable statistical analysis')
    parser.add_argument('--output-dir', type=str, default='output',
                       help='Output directory')
    parser.add_argument('--no-plots', action='store_true',
                       help='Disable plot generation')
    parser.add_argument('--wait-for-fault', action='store_true',
                       help='Wait for fault to trigger (extends duration if needed, up to --max-duration)')
    parser.add_argument('--extend-after-fault', type=float, default=None,
                       help='Extend simulation duration by this many seconds after fault triggers')
    parser.add_argument('--max-duration', type=float, default=None,
                       help='Maximum duration when waiting for fault (default: 10x --duration)')
    
    args = parser.parse_args()
    
    run_fault_simulation(
        scenario_file=args.scenario,
        mode=args.mode,
        current_amp=args.current,
        duration_sec=args.duration,
        target_soc_pct=args.target_soc,
        initial_soc_pct=args.initial_soc,
        dt_ms=args.dt,
        temperature_c=args.temperature,
        monte_carlo=args.monte_carlo,
        n_runs=args.n_runs,
        sampling_strategy=args.sampling_strategy,
        statistical_analysis=args.statistical_analysis,
        output_dir=args.output_dir,
        save_plots=not args.no_plots,
        wait_for_fault=args.wait_for_fault,
        extend_after_fault=args.extend_after_fault,
        max_duration_sec=args.max_duration
    )


if __name__ == '__main__':
    main()

