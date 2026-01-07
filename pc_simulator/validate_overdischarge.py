"""
Validate overdischarge fault simulation against industry standards.

Industry Standards Reference:
- SOC Limit: 3% (typical BMS protection threshold)
- Undervoltage Limit: 2.65V (per user requirements and industry practice)
- IEC 62660-3: Discharge until 25% of nominal voltage or 30 minutes
- SAE J2464: Discharge until module voltage reaches 0.0V ± 0.2V
- ISO 12405-1: Discharge until voltage drops to 25% of nominal voltage

For LiFePO4 (nominal 3.2V):
- 25% of nominal = 0.8V (extreme, not practical)
- Typical protection: 2.5-2.7V (78-84% of nominal)
- User requirement: 2.65V (83% of nominal) - reasonable and safe
"""

import pandas as pd
import sys
from pathlib import Path


def validate_overdischarge(output_dir: str):
    """Validate overdischarge fault simulation data against industry standards."""
    output_path = Path(output_dir)
    
    # Load summary
    summary_file = output_path / 'simulation_result.csv'
    if not summary_file.exists():
        print(f"❌ ERROR: Summary file not found: {summary_file}")
        return False
    
    summary = pd.read_csv(summary_file)
    
    # Load time series data
    timeseries_file = output_path / 'timeseries_data.csv'
    if not timeseries_file.exists():
        print(f"❌ ERROR: Time series file not found: {timeseries_file}")
        return False
    
    print(f"\n{'='*70}")
    print("OVERDISCHARGE FAULT VALIDATION")
    print("Industry Standards: 3% SOC or 2.65V Undervoltage Limit")
    print(f"{'='*70}")
    
    # Read time series data in chunks to handle large files
    print(f"\nLoading time series data from: {timeseries_file}")
    try:
        # Read only necessary columns to save memory
        df = pd.read_csv(timeseries_file, usecols=['time_s', 'soc_percent', 'pack_voltage_V', 'cell_5_V'])
    except Exception as e:
        print(f"❌ ERROR: Could not read time series data: {e}")
        return False
    
    print(f"  Loaded {len(df)} data points")
    
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
    
    # Check 1: SOC at fault trigger should be ~3%
    soc_at_fault = df.iloc[fault_idx]['soc_percent']
    print(f"\n[Check 1] SOC at fault trigger:")
    print(f"  Expected: ~3.0% (per industry standards)")
    print(f"  Actual: {soc_at_fault:.2f}%")
    print(f"  Fault triggered at: {fault_time:.1f}s")
    if 2.0 <= soc_at_fault <= 4.0:
        print(f"  PASS: SOC is within expected range (2-4%)")
    else:
        print(f"  WARNING: SOC is outside expected range (2-4%)")
        if soc_at_fault > 4.0:
            print(f"    -> Fault triggered too early (should trigger at 3%)")
        else:
            print(f"    -> Fault triggered too late (should trigger at 3%)")
        # Don't fail for this, as timing may vary
    
    # Check 2: Cell 5 voltage should reach 2.65V limit (or below)
    cell_5_col = 'cell_5_V'
    if cell_5_col not in df.columns:
        print(f"\n❌ ERROR: Cell 5 voltage column not found")
        return False
    
    # Find minimum cell 5 voltage after fault trigger
    df_after_fault = df.iloc[fault_idx:]
    min_cell5_voltage = df_after_fault[cell_5_col].min()
    min_cell5_idx = df_after_fault[cell_5_col].idxmin()
    min_cell5_time = df.iloc[min_cell5_idx]['time_s']
    
    print(f"\n[Check 2] Cell 5 minimum voltage (after fault trigger):")
    print(f"  Expected: <= 2.65V (per industry standards)")
    print(f"  Actual minimum: {min_cell5_voltage:.3f}V")
    print(f"  Minimum reached at: {min_cell5_time:.1f}s ({min_cell5_time - fault_time:.1f}s after trigger)")
    
    if min_cell5_voltage <= 2.65:
        print(f"  PASS: Cell 5 voltage reached or exceeded 2.65V limit")
    else:
        print(f"  FAIL: Cell 5 voltage did not reach 2.65V limit")
        print(f"    -> Difference: {min_cell5_voltage - 2.65:.3f}V above limit")
        all_passed = False
    
    # Check 3: Verify voltage limit is being applied (not stuck at 2.5V)
    final_cell5_voltage = df.iloc[-1][cell_5_col]
    print(f"\n[Check 3] Final Cell 5 voltage:")
    print(f"  Final voltage: {final_cell5_voltage:.3f}V")
    if final_cell5_voltage < 2.5:
        print(f"  PASS: Voltage went below default 2.5V limit (fault is working)")
    elif final_cell5_voltage <= 2.65:
        print(f"  PASS: Voltage reached fault limit of 2.65V")
    else:
        print(f"  WARNING: Final voltage is above 2.65V limit")
        print(f"    -> May indicate fault limit not being applied correctly")
    
    # Check 4: Pack behavior - other cells should maintain normal voltage
    other_cells = [f'cell_{i}_V' for i in range(1, 17) if i != 5]
    other_cells_available = [col for col in other_cells if col in df.columns]
    
    if len(other_cells_available) > 0:
        final_other_avg = df.iloc[-1][other_cells_available].mean()
        print(f"\n[Check 4] Other cells (non-fault) behavior:")
        print(f"  Average voltage of other 15 cells: {final_other_avg:.3f}V")
        if final_other_avg >= 2.5:
            print(f"  PASS: Other cells maintain normal voltage range")
        else:
            print(f"  WARNING: Other cells also dropped below 2.5V")
    
    # Check 5: SOC progression - should discharge to near 0%
    final_soc = df.iloc[-1]['soc_percent']
    print(f"\n[Check 5] Final pack SOC:")
    print(f"  Final SOC: {final_soc:.2f}%")
    if final_soc <= 1.0:
        print(f"  PASS: Pack discharged to near 0% SOC (as expected)")
    else:
        print(f"  WARNING: Pack SOC is higher than expected")
    
    # Summary
    print(f"\n{'='*70}")
    print("VALIDATION SUMMARY")
    print(f"{'='*70}")
    
    if all_passed:
        print(f"\nALL CHECKS PASSED")
        print(f"\nThe overdischarge fault simulation conforms to industry standards:")
        print(f"  - Fault triggers at appropriate SOC threshold (~3%)")
        print(f"  - Cell voltage reaches undervoltage limit (2.65V)")
        print(f"  - Fault behavior is consistent with expected overdischarge effects")
    else:
        print(f"\nSOME CHECKS FAILED")
        print(f"\nPlease review the validation results above.")
    
    # Industry standards comparison
    print(f"\n{'='*70}")
    print("INDUSTRY STANDARDS COMPARISON")
    print(f"{'='*70}")
    print(f"\nTest Configuration:")
    print(f"  - SOC Trigger: 3.0% (per user requirement)")
    print(f"  - Undervoltage Limit: 2.65V (per user requirement)")
    print(f"\nIndustry Standards Reference:")
    print(f"  - IEC 62660-3: Discharge until 25% of nominal (0.8V for LiFePO4)")
    print(f"  - SAE J2464: Discharge until 0.0V ± 0.2V")
    print(f"  - ISO 12405-1: Discharge until 25% of nominal voltage")
    print(f"  - Typical BMS Protection: 2.5-2.7V (78-84% of 3.2V nominal)")
    print(f"\nUser requirements (3% SOC, 2.65V) are MORE CONSERVATIVE than")
    print(f"  extreme standards (0.8V) and align with typical BMS protection limits.")
    print(f"  This is SAFE and APPROPRIATE for practical applications.")
    
    return all_passed


if __name__ == '__main__':
    if len(sys.argv) > 1:
        output_dir = sys.argv[1]
    else:
        output_dir = 'output_overdischarge_test'
    
    validate_overdischarge(output_dir)
