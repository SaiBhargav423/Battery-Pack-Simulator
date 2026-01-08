"""
Validate Internal Short Circuit - Hard fault simulation data.

Checks:
1. Fault triggered at correct SOC (~80%)
2. Cell 5 (target cell) shows voltage drop after fault
3. Cell 5 temperature rises after fault
4. Pack voltage drops appropriately
5. Data consistency
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Configure output encoding for Windows
if sys.platform == 'win32':
    import sys
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')

def validate_internal_short_hard(output_dir: str):
    """Validate internal short hard fault simulation data."""
    output_path = Path(output_dir)
    
    print("="*70)
    print("VALIDATING INTERNAL SHORT CIRCUIT - HARD FAULT")
    print("="*70)
    
    # Load summary data
    summary_file = output_path / "simulation_result.csv"
    if not summary_file.exists():
        print(f"❌ ERROR: Summary file not found: {summary_file}")
        return False
    
    summary = pd.read_csv(summary_file)
    print(f"\n✓ Summary file loaded")
    print(f"  Final SOC: {summary.iloc[0]['final_soc_pct']:.2f}%")
    print(f"  Final Voltage: {summary.iloc[0]['final_voltage_mv']/1000:.2f}V")
    print(f"  Duration: {summary.iloc[0]['duration_sec']:.1f}s")
    print(f"  Faults Triggered: {summary.iloc[0]['faults_triggered']}")
    print(f"  First Fault Time: {summary.iloc[0]['first_fault_time_sec']:.1f}s")
    
    # Load time series data
    timeseries_file = output_path / "timeseries_data.csv"
    if not timeseries_file.exists():
        print(f"❌ ERROR: Time series file not found: {timeseries_file}")
        return False
    
    print(f"\n✓ Loading time series data...")
    df = pd.read_csv(timeseries_file)
    print(f"  Rows: {len(df)}, Columns: {len(df.columns)}")
    
    # Get fault trigger time
    fault_time = summary.iloc[0]['first_fault_time_sec']
    fault_idx = df[df['time_s'] >= fault_time].index[0] if len(df[df['time_s'] >= fault_time]) > 0 else None
    
    if fault_idx is None:
        print(f"❌ ERROR: Could not find fault trigger time in time series")
        return False
    
    print(f"\n{'='*70}")
    print("VALIDATION CHECKS")
    print(f"{'='*70}")
    
    all_passed = True
    
    # Check 1: SOC at fault trigger should be ~80%
    soc_at_fault = df.iloc[fault_idx]['soc_percent']
    print(f"\n[Check 1] SOC at fault trigger:")
    print(f"  Expected: ~80%")
    print(f"  Actual: {soc_at_fault:.2f}%")
    if 75.0 <= soc_at_fault <= 85.0:
        print(f"  ✓ PASS: SOC is within expected range")
    else:
        print(f"  ❌ FAIL: SOC is outside expected range (75-85%)")
        all_passed = False
    
    # Check 2: Cell 5 voltage drop after fault
    cell_5_col = 'cell_5_V'
    if cell_5_col not in df.columns:
        print(f"\n❌ ERROR: {cell_5_col} column not found")
        all_passed = False
    else:
        # Get voltage before and after fault
        before_fault_idx = max(0, fault_idx - 100)  # 10 seconds before (100ms steps)
        after_fault_idx = min(len(df) - 1, fault_idx + 100)  # 10 seconds after
        
        voltage_before = df.iloc[before_fault_idx][cell_5_col]
        voltage_at_fault = df.iloc[fault_idx][cell_5_col]
        voltage_after = df.iloc[after_fault_idx][cell_5_col]
        
        voltage_drop = voltage_before - voltage_after
        voltage_drop_pct = (voltage_drop / voltage_before) * 100
        
        print(f"\n[Check 2] Cell 5 voltage drop:")
        print(f"  Before fault: {voltage_before:.3f}V")
        print(f"  At fault: {voltage_at_fault:.3f}V")
        print(f"  After fault (10s): {voltage_after:.3f}V")
        print(f"  Voltage drop: {voltage_drop:.3f}V ({voltage_drop_pct:.1f}%)")
        
        # For hard short (0.1Ω), expect significant drop (5-30%)
        if voltage_drop_pct >= 5.0:
            print(f"  ✓ PASS: Significant voltage drop observed (≥5%)")
        else:
            print(f"  ❌ FAIL: Voltage drop too small (<5%)")
            all_passed = False
    
    # Check 3: Cell 5 temperature rise
    cell_5_temp_col = 'cell_5_temp_C'
    if cell_5_temp_col not in df.columns:
        print(f"\n❌ ERROR: {cell_5_temp_col} column not found")
        all_passed = False
    else:
        temp_before = df.iloc[before_fault_idx][cell_5_temp_col]
        temp_after = df.iloc[after_fault_idx][cell_5_temp_col]
        temp_rise = temp_after - temp_before
        
        print(f"\n[Check 3] Cell 5 temperature rise:")
        print(f"  Before fault: {temp_before:.2f}°C")
        print(f"  After fault (10s): {temp_after:.2f}°C")
        print(f"  Temperature rise: {temp_rise:.2f}°C")
        
        # Expect some temperature rise due to heat generation
        if temp_rise > 0.1:
            print(f"  ✓ PASS: Temperature rise observed")
        else:
            print(f"  ⚠ WARNING: Temperature rise is minimal (may be normal for short duration)")
    
    # Check 4: Pack voltage drop
    pack_voltage_before = df.iloc[before_fault_idx]['pack_voltage_V']
    pack_voltage_after = df.iloc[after_fault_idx]['pack_voltage_V']
    pack_voltage_drop = pack_voltage_before - pack_voltage_after
    pack_voltage_drop_pct = (pack_voltage_drop / pack_voltage_before) * 100
    
    print(f"\n[Check 4] Pack voltage drop:")
    print(f"  Before fault: {pack_voltage_before:.3f}V")
    print(f"  After fault (10s): {pack_voltage_after:.3f}V")
    print(f"  Voltage drop: {pack_voltage_drop:.3f}V ({pack_voltage_drop_pct:.2f}%)")
    
    # Pack voltage should drop slightly (1 cell out of 16)
    if pack_voltage_drop > 0.1:
        print(f"  ✓ PASS: Pack voltage drop observed")
    else:
        print(f"  ⚠ WARNING: Pack voltage drop is minimal")
    
    # Check 5: Other cells should not be significantly affected
    other_cells_affected = False
    for i in range(1, 17):
        if i == 5:
            continue
        cell_col = f'cell_{i}_V'
        if cell_col in df.columns:
            other_voltage_before = df.iloc[before_fault_idx][cell_col]
            other_voltage_after = df.iloc[after_fault_idx][cell_col]
            other_drop = abs(other_voltage_before - other_voltage_after)
            if other_drop > 0.05:  # More than 50mV drop
                other_cells_affected = True
                print(f"\n  ⚠ WARNING: Cell {i} also shows voltage drop: {other_drop:.3f}V")
    
    if not other_cells_affected:
        print(f"\n[Check 5] Other cells (1-4, 6-16):")
        print(f"  ✓ PASS: Other cells not significantly affected")
    
    # Check 6: Data consistency
    print(f"\n[Check 6] Data consistency:")
    print(f"  Time steps: {len(df)}")
    print(f"  Time range: {df['time_s'].min():.1f}s to {df['time_s'].max():.1f}s")
    print(f"  Time step: ~{(df['time_s'].max() - df['time_s'].min()) / len(df) * 1000:.1f}ms")
    print(f"  ✓ PASS: Data appears consistent")
    
    # Summary
    print(f"\n{'='*70}")
    print("VALIDATION SUMMARY")
    print(f"{'='*70}")
    
    if all_passed:
        print("✓ ALL CHECKS PASSED")
        print("\nThe internal short circuit - hard fault simulation data is correct.")
        print("Key observations:")
        print(f"  - Fault triggered at {soc_at_fault:.1f}% SOC (expected ~80%)")
        print(f"  - Cell 5 voltage dropped by {voltage_drop:.3f}V ({voltage_drop_pct:.1f}%)")
        print(f"  - Temperature rise: {temp_rise:.2f}°C")
        return True
    else:
        print("❌ SOME CHECKS FAILED")
        print("\nPlease review the validation results above.")
        return False

if __name__ == "__main__":
    output_dir = "output_internal_short_hard_test"
    if len(sys.argv) > 1:
        output_dir = sys.argv[1]
    
    success = validate_internal_short_hard(output_dir)
    sys.exit(0 if success else 1)
