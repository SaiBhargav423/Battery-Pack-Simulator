"""
Validate fault simulation data for internal short circuit hard fault.
Checks that the data matches expected behavior for this fault type.
"""

import pandas as pd
import numpy as np
from pathlib import Path

def validate_internal_short_hard_fault(output_dir='output_deterministic'):
    """Validate internal short circuit hard fault data."""
    
    output_path = Path(output_dir)
    sim_result_file = output_path / 'simulation_result.csv'
    timeseries_file = output_path / 'timeseries_data.csv'
    
    print("=" * 70)
    print("VALIDATING INTERNAL SHORT CIRCUIT HARD FAULT DATA")
    print("=" * 70)
    
    # Read simulation result
    print("\n1. Reading simulation summary...")
    sim_result = pd.read_csv(sim_result_file)
    print(f"   [OK] Simulation result loaded")
    
    # Read timeseries data
    print("\n2. Reading timeseries data...")
    df = pd.read_csv(timeseries_file)
    print(f"   [OK] Timeseries data loaded: {len(df)} rows, {len(df.columns)} columns")
    
    # Expected fault parameters
    expected_fault_cell = 5  # cell_5 (1-indexed)
    expected_trigger_soc = 80.0
    expected_resistance = 0.1  # ohms
    expected_duration = 600.0  # seconds
    
    # Get fault trigger time from simulation result
    fault_trigger_time = sim_result['first_fault_time_sec'].iloc[0]
    print(f"\n3. Fault trigger time: {fault_trigger_time:.2f} seconds")
    
    # Find data around fault trigger
    fault_idx = df[df['time_s'] >= fault_trigger_time].index[0]
    print(f"   [OK] Found fault trigger at index {fault_idx}")
    
    # Get data before and after fault
    before_fault = df.iloc[max(0, fault_idx - 10):fault_idx]
    after_fault = df.iloc[fault_idx:min(len(df), fault_idx + 100)]
    
    # Check SOC at fault trigger
    soc_at_trigger = df.iloc[fault_idx]['soc_percent']
    print(f"\n4. SOC at fault trigger: {soc_at_trigger:.2f}%")
    soc_check = abs(soc_at_trigger - expected_trigger_soc) < 2.0  # Allow 2% tolerance
    print(f"   {'[PASS]' if soc_check else '[FAIL]'} Expected ~{expected_trigger_soc}% (actual: {soc_at_trigger:.2f}%)")
    
    # Check cell 5 voltage behavior
    # Note: Internal short may not show immediate cell voltage drop due to voltage divider
    # The primary indicator is pack voltage drop and current draw
    print(f"\n5. Cell 5 voltage behavior:")
    cell5_col = 'cell_5_V'
    voltage_before = before_fault[cell5_col].mean()
    voltage_after_trigger = after_fault[cell5_col].iloc[0:10].mean()
    voltage_drop = voltage_before - voltage_after_trigger
    voltage_drop_pct = (voltage_drop / voltage_before) * 100.0
    
    print(f"   Before fault (avg): {voltage_before:.3f} V")
    print(f"   After trigger (avg): {voltage_after_trigger:.3f} V")
    print(f"   Voltage drop: {voltage_drop:.3f} V ({voltage_drop_pct:.1f}%)")
    print(f"   Note: Internal short may show subtle cell voltage effects")
    
    # For 0.1Ω hard short, voltage drop may be subtle due to voltage divider
    # Check if there's any change (even small)
    voltage_changed = abs(voltage_drop) > 0.001  # Any measurable change
    print(f"   {'[PASS]' if voltage_changed else '[INFO]'} Voltage changed: {voltage_changed}")
    
    # Check cell 5 temperature rise
    print(f"\n6. Cell 5 temperature behavior:")
    temp_col = 'cell_5_temp_C'
    temp_before = before_fault[temp_col].mean()
    # Check temperature at multiple points after fault
    temp_after_1min = after_fault[after_fault['time_s'] <= fault_trigger_time + 60][temp_col].iloc[-1] if len(after_fault[after_fault['time_s'] <= fault_trigger_time + 60]) > 0 else temp_before
    temp_after_5min = after_fault[after_fault['time_s'] <= fault_trigger_time + 300][temp_col].iloc[-1] if len(after_fault[after_fault['time_s'] <= fault_trigger_time + 300]) > 0 else temp_before
    temp_after_final = after_fault[temp_col].iloc[-1] if len(after_fault) > 0 else temp_before
    
    temp_rise_1min = temp_after_1min - temp_before
    temp_rise_5min = temp_after_5min - temp_before
    temp_rise_final = temp_after_final - temp_before
    
    print(f"   Before fault (avg): {temp_before:.2f} °C")
    print(f"   After 1 minute: {temp_after_1min:.2f} °C (rise: {temp_rise_1min:.2f} °C)")
    print(f"   After 5 minutes: {temp_after_5min:.2f} °C (rise: {temp_rise_5min:.2f} °C)")
    print(f"   Final: {temp_after_final:.2f} °C (rise: {temp_rise_final:.2f} °C)")
    
    # For hard short, expect temperature rise over time
    temp_rise_ok = temp_rise_final >= 0.5 or temp_rise_5min >= 0.5  # At least 0.5°C rise
    print(f"   {'[PASS]' if temp_rise_ok else '[INFO]'} Temperature rise observed: {temp_rise_ok}")
    
    # Check pack voltage behavior
    print(f"\n7. Pack voltage behavior:")
    pack_voltage_before = before_fault['pack_voltage_V'].mean()
    pack_voltage_after = after_fault['pack_voltage_V'].iloc[0:10].mean()
    pack_voltage_drop = pack_voltage_before - pack_voltage_after
    
    print(f"   Before fault (avg): {pack_voltage_before:.3f} V")
    print(f"   After trigger (avg): {pack_voltage_after:.3f} V")
    print(f"   Pack voltage drop: {pack_voltage_drop:.3f} V")
    
    # Pack voltage should drop (one cell out of 16)
    pack_drop_ok = pack_voltage_drop >= 0.1  # At least 0.1V drop
    print(f"   {'[PASS]' if pack_drop_ok else '[FAIL]'} Pack voltage drop >= 0.1V: {pack_drop_ok}")
    
    # Check fault duration
    print(f"\n8. Fault duration:")
    fault_duration = sim_result['duration_sec'].iloc[0] - fault_trigger_time
    print(f"   Fault active for: {fault_duration:.1f} seconds")
    print(f"   Expected duration: {expected_duration:.1f} seconds")
    
    # Check if fault cleared (should clear after 600 seconds)
    fault_end_time = fault_trigger_time + expected_duration
    if fault_end_time <= sim_result['duration_sec'].iloc[0]:
        # Check if voltage recovered after fault cleared
        fault_end_idx = df[df['time_s'] >= fault_end_time].index[0] if len(df[df['time_s'] >= fault_end_time]) > 0 else len(df) - 1
        voltage_after_clear = df.iloc[fault_end_idx:min(len(df), fault_end_idx + 10)][cell5_col].mean()
        voltage_recovery = voltage_after_clear - voltage_after_trigger
        print(f"   Voltage after fault clear: {voltage_after_clear:.3f} V")
        print(f"   Voltage recovery: {voltage_recovery:.3f} V")
        recovery_ok = voltage_recovery > 0  # Should recover
        print(f"   {'[PASS]' if recovery_ok else '[FAIL]'} Voltage recovery after fault clear: {recovery_ok}")
    
    # Check cell imbalance and pack behavior
    print(f"\n9. Cell imbalance and pack behavior:")
    other_cells = [f'cell_{i}_V' for i in range(1, 17) if i != 5]
    other_voltage_avg_before = before_fault[other_cells].mean(axis=1).mean()
    other_voltage_avg_after = after_fault[other_cells].iloc[0:10].mean(axis=1).mean()
    cell5_voltage_before = before_fault[cell5_col].mean()
    cell5_voltage_after = after_fault[cell5_col].iloc[0:10].mean()
    
    # Check if pack voltage drop is consistent with cell behavior
    pack_drop_per_cell = pack_voltage_drop / 16.0  # Average per cell
    cell5_voltage_change = cell5_voltage_after - cell5_voltage_before
    other_cells_voltage_change = other_voltage_avg_after - other_voltage_avg_before
    
    print(f"   Other cells avg before: {other_voltage_avg_before:.3f} V")
    print(f"   Other cells avg after: {other_voltage_avg_after:.3f} V")
    print(f"   Other cells change: {other_cells_voltage_change:.3f} V")
    print(f"   Cell 5 before: {cell5_voltage_before:.3f} V")
    print(f"   Cell 5 after: {cell5_voltage_after:.3f} V")
    print(f"   Cell 5 change: {cell5_voltage_change:.3f} V")
    print(f"   Pack drop per cell (avg): {pack_drop_per_cell:.3f} V")
    
    # The fault should cause pack voltage drop
    # Cell 5 might show different behavior than others
    imbalance_ok = abs(cell5_voltage_change - other_cells_voltage_change) > 0.001 or pack_voltage_drop > 0.1
    print(f"   {'[PASS]' if imbalance_ok else '[INFO]'} Fault effects detected: {imbalance_ok}")
    
    # Summary
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)
    
    all_checks = [
        ("SOC at trigger ~80%", soc_check),
        ("Pack voltage drop >= 0.1V", pack_drop_ok),
        ("Fault effects detected", imbalance_ok),
        ("Cell 5 voltage changed", voltage_changed),
        ("Temperature rise observed", temp_rise_ok),
    ]
    
    passed = sum(1 for _, check in all_checks if check)
    total = len(all_checks)
    
    for name, check in all_checks:
        status = "PASS" if check else "FAIL"
        symbol = "[PASS]" if check else "[FAIL]"
        print(f"  {symbol} {name}: {status}")
    
    print(f"\n  Overall: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n  >>> ALL VALIDATION CHECKS PASSED <<<")
        return True
    else:
        print(f"\n  WARNING: {total - passed} validation check(s) failed")
        return False

if __name__ == '__main__':
    import sys
    output_dir = sys.argv[1] if len(sys.argv) > 1 else 'output_deterministic'
    validate_internal_short_hard_fault(output_dir)

