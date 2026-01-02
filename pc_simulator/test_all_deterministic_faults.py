"""
Test all deterministic fault scenarios systematically.

This script runs simulations for each deterministic fault type with appropriate
parameters to observe fault effects, and documents the results.
"""

import subprocess
import json
import yaml
from pathlib import Path
from typing import Dict, List, Any
import time

# Base directory
BASE_DIR = Path(__file__).parent
SCENARIOS_DIR = BASE_DIR.parent / "scenarios" / "Deterministic"
OUTPUT_BASE = BASE_DIR / "output_deterministic_tests"

# Fault scenarios to test (excluding internal_short_hard which was already tested)
FAULT_SCENARIOS = [
    "internal_short_soft.yaml",
    "external_short.yaml",
    "overcharge.yaml",
    "overdischarge.yaml",
    "self_discharge.yaml",
    "open_circuit.yaml",
    "overheating.yaml",
    "thermal_runaway.yaml",
    "abnormal_temperature.yaml",
    "capacity_fade.yaml",
    "resistance_increase.yaml",
    "lithium_plating.yaml",
    "cell_imbalance.yaml",
    "electrolyte_leakage.yaml",
    "sensor_offset.yaml",
    "sensor_drift.yaml",
    "insulation_fault.yaml",
    "thermal_propagation.yaml",
    "cascading_failure.yaml",
]

# Simulation parameters for each fault type
# Format: (mode, current, duration, initial_soc, description)
SIMULATION_PARAMS = {
    "internal_short_soft.yaml": ("discharge", 50.0, 3600, 100.0, "Discharge to observe soft short effects"),
    "external_short.yaml": ("discharge", 50.0, 600, 100.0, "Short duration to observe external short"),
    "overcharge.yaml": ("charge", 50.0, 3600, 50.0, "Charge to trigger overcharge at 90% SOC"),
    "overdischarge.yaml": ("discharge", 50.0, 3600, 50.0, "Discharge to trigger overdischarge at 10% SOC"),
    "self_discharge.yaml": ("discharge", 0.0, 3600, 100.0, "Rest to observe self-discharge"),
    "open_circuit.yaml": ("discharge", 50.0, 600, 100.0, "Discharge to observe open circuit"),
    "overheating.yaml": ("discharge", 50.0, 600, 100.0, "Discharge to observe overheating"),
    "thermal_runaway.yaml": ("discharge", 50.0, 600, 100.0, "Discharge to observe thermal runaway"),
    "abnormal_temperature.yaml": ("discharge", 50.0, 600, 100.0, "Discharge to observe abnormal temperature"),
    "capacity_fade.yaml": ("discharge", 50.0, 3600, 100.0, "Discharge to observe capacity fade"),
    "resistance_increase.yaml": ("discharge", 50.0, 600, 100.0, "Discharge to observe resistance increase"),
    "lithium_plating.yaml": ("charge", 50.0, 3600, 50.0, "Charge to observe lithium plating"),
    "cell_imbalance.yaml": ("discharge", 50.0, 3600, 100.0, "Discharge to observe cell imbalance"),
    "electrolyte_leakage.yaml": ("discharge", 50.0, 600, 100.0, "Discharge to observe electrolyte leakage"),
    "sensor_offset.yaml": ("discharge", 50.0, 600, 100.0, "Discharge to observe sensor offset"),
    "sensor_drift.yaml": ("discharge", 50.0, 600, 100.0, "Discharge to observe sensor drift"),
    "insulation_fault.yaml": ("discharge", 50.0, 600, 100.0, "Discharge to observe insulation fault"),
    "thermal_propagation.yaml": ("discharge", 50.0, 600, 100.0, "Discharge to observe thermal propagation"),
    "cascading_failure.yaml": ("discharge", 50.0, 600, 100.0, "Discharge to observe cascading failure"),
}


def load_scenario(scenario_file: Path) -> Dict[str, Any]:
    """Load YAML scenario file."""
    with open(scenario_file, 'r') as f:
        return yaml.safe_load(f)


def run_simulation(scenario_file: str, mode: str, current: float, duration: float, 
                  initial_soc: float, output_dir: str) -> Dict[str, Any]:
    """Run a single fault simulation."""
    scenario_path = SCENARIOS_DIR / scenario_file
    output_path = OUTPUT_BASE / output_dir
    
    # Build command
    cmd = [
        "python", "run_fault_local_no_bms.py",
        "--scenario", str(scenario_path),
        "--mode", mode,
        "--current", str(current),
        "--duration", str(duration),
        "--initial-soc", str(initial_soc),
        "--output-dir", str(output_path)
    ]
    
    print(f"\n{'='*70}")
    print(f"Running: {scenario_file}")
    print(f"Mode: {mode}, Current: {current}A, Duration: {duration}s, Initial SOC: {initial_soc}%")
    print(f"{'='*70}")
    
    start_time = time.time()
    try:
        result = subprocess.run(
            cmd,
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout
        )
        elapsed = time.time() - start_time
        
        if result.returncode == 0:
            # Parse output
            output_lines = result.stdout.split('\n')
            fault_triggered = False
            fault_time = None
            final_soc = None
            final_voltage = None
            
            for line in output_lines:
                if "[Fault Triggered]" in line:
                    fault_triggered = True
                    # Extract time
                    try:
                        parts = line.split("at")
                        if len(parts) > 1:
                            fault_time = float(parts[1].split()[0])
                    except:
                        pass
                elif "Final SOC:" in line:
                    try:
                        final_soc = float(line.split(":")[1].split("%")[0].strip())
                    except:
                        pass
                elif "Final Voltage:" in line:
                    try:
                        final_voltage = float(line.split(":")[1].split("V")[0].strip())
                    except:
                        pass
            
            return {
                "success": True,
                "elapsed_time": elapsed,
                "fault_triggered": fault_triggered,
                "fault_time": fault_time,
                "final_soc": final_soc,
                "final_voltage": final_voltage,
                "output_dir": str(output_path),
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        else:
            return {
                "success": False,
                "elapsed_time": elapsed,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Timeout",
            "elapsed_time": time.time() - start_time
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "elapsed_time": time.time() - start_time
        }


def analyze_results(output_dir: Path, scenario_name: str) -> Dict[str, Any]:
    """Analyze simulation results."""
    results = {
        "scenario": scenario_name,
        "data_available": False,
        "summary": {}
    }
    
    sim_result_file = output_dir / "simulation_result.csv"
    timeseries_file = output_dir / "timeseries_data.csv"
    
    if sim_result_file.exists():
        import pandas as pd
        try:
            sim_result = pd.read_csv(sim_result_file)
            if len(sim_result) > 0:
                results["data_available"] = True
                results["summary"] = {
                    "final_soc": sim_result.iloc[0].get("final_soc_pct", None),
                    "final_voltage_mv": sim_result.iloc[0].get("final_voltage_mv", None),
                    "duration_sec": sim_result.iloc[0].get("duration_sec", None),
                    "fault_triggered": sim_result.iloc[0].get("faults_triggered", 0) > 0,
                    "fault_time": sim_result.iloc[0].get("first_fault_time_sec", None)
                }
        except Exception as e:
            results["error"] = f"Error reading simulation result: {e}"
    
    if timeseries_file.exists():
        import pandas as pd
        try:
            df = pd.read_csv(timeseries_file)
            results["timeseries_rows"] = len(df)
            results["timeseries_columns"] = len(df.columns)
            
            # Basic statistics
            if len(df) > 0:
                results["stats"] = {
                    "min_voltage": df["pack_voltage_V"].min(),
                    "max_voltage": df["pack_voltage_V"].max(),
                    "min_soc": df["soc_percent"].min(),
                    "max_soc": df["soc_percent"].max(),
                    "final_soc": df["soc_percent"].iloc[-1],
                    "final_voltage": df["pack_voltage_V"].iloc[-1]
                }
        except Exception as e:
            results["timeseries_error"] = str(e)
    
    return results


def main():
    """Main test execution."""
    print("="*70)
    print("DETERMINISTIC FAULT TESTING SUITE")
    print("="*70)
    print(f"Testing {len(FAULT_SCENARIOS)} fault scenarios")
    print(f"Output directory: {OUTPUT_BASE}")
    
    # Create output directory
    OUTPUT_BASE.mkdir(parents=True, exist_ok=True)
    
    # Results storage
    all_results = {}
    failed_tests = []
    
    # Run each test
    for i, scenario_file in enumerate(FAULT_SCENARIOS, 1):
        print(f"\n[{i}/{len(FAULT_SCENARIOS)}] Testing: {scenario_file}")
        
        # Get simulation parameters
        if scenario_file not in SIMULATION_PARAMS:
            print(f"  WARNING: No parameters defined for {scenario_file}, skipping")
            continue
        
        mode, current, duration, initial_soc, description = SIMULATION_PARAMS[scenario_file]
        
        # Create output directory name
        output_dir_name = scenario_file.replace(".yaml", "")
        
        # Run simulation
        result = run_simulation(
            scenario_file,
            mode,
            current,
            duration,
            initial_soc,
            output_dir_name
        )
        
        # Analyze results
        if result.get("success"):
            output_path = Path(result["output_dir"])
            analysis = analyze_results(output_path, scenario_file)
            result["analysis"] = analysis
        
        # Store results
        all_results[scenario_file] = result
        
        if not result.get("success"):
            failed_tests.append(scenario_file)
            print(f"  FAILED: {result.get('error', 'Unknown error')}")
        else:
            print(f"  SUCCESS: Elapsed {result['elapsed_time']:.1f}s")
            if result.get("fault_triggered"):
                print(f"  Fault triggered at: {result.get('fault_time', 'N/A')}s")
    
    # Generate report
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    successful = len(FAULT_SCENARIOS) - len(failed_tests)
    print(f"Total tests: {len(FAULT_SCENARIOS)}")
    print(f"Successful: {successful}")
    print(f"Failed: {len(failed_tests)}")
    
    if failed_tests:
        print(f"\nFailed tests:")
        for test in failed_tests:
            print(f"  - {test}")
    
    # Save detailed results
    report_file = OUTPUT_BASE / "test_report.json"
    with open(report_file, 'w') as f:
        json.dump(all_results, f, indent=2, default=str)
    
    print(f"\nDetailed report saved to: {report_file}")
    
    # Generate markdown report
    generate_markdown_report(all_results, OUTPUT_BASE / "test_report.md")
    
    print(f"\nMarkdown report saved to: {OUTPUT_BASE / 'test_report.md'}")


def generate_markdown_report(results: Dict[str, Any], output_file: Path):
    """Generate markdown test report."""
    with open(output_file, 'w') as f:
        f.write("# Deterministic Fault Testing Report\n\n")
        f.write(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("## Summary\n\n")
        
        successful = sum(1 for r in results.values() if r.get("success"))
        total = len(results)
        
        f.write(f"- **Total Tests**: {total}\n")
        f.write(f"- **Successful**: {successful}\n")
        f.write(f"- **Failed**: {total - successful}\n\n")
        
        f.write("## Test Results\n\n")
        
        for scenario_file, result in results.items():
            f.write(f"### {scenario_file}\n\n")
            
            if result.get("success"):
                f.write("**Status**: [PASSED]\n\n")
                f.write(f"- **Elapsed Time**: {result.get('elapsed_time', 0):.1f}s\n")
                
                if result.get("fault_triggered"):
                    f.write(f"- **Fault Triggered**: Yes (at {result.get('fault_time', 'N/A')}s)\n")
                else:
                    f.write("- **Fault Triggered**: No\n")
                
                if result.get("final_soc") is not None:
                    f.write(f"- **Final SOC**: {result.get('final_soc'):.2f}%\n")
                
                if result.get("final_voltage") is not None:
                    f.write(f"- **Final Voltage**: {result.get('final_voltage'):.2f}V\n")
                
                analysis = result.get("analysis", {})
                if analysis.get("data_available"):
                    summary = analysis.get("summary", {})
                    f.write(f"- **Data Available**: Yes\n")
                    if summary.get("timeseries_rows"):
                        f.write(f"- **Time Series Rows**: {summary.get('timeseries_rows', 'N/A')}\n")
            else:
                f.write("**Status**: [FAILED]\n\n")
                f.write(f"- **Error**: {result.get('error', 'Unknown error')}\n")
                if result.get("stderr"):
                    f.write(f"- **Stderr**: {result.get('stderr')[:200]}...\n")
            
            f.write(f"- **Output Directory**: `{result.get('output_dir', 'N/A')}`\n\n")
            f.write("---\n\n")


if __name__ == "__main__":
    main()

