import pandas as pd
import sys

csv_file = sys.argv[1] if len(sys.argv) > 1 else 'output_final2/timeseries_data.csv'
df = pd.read_csv(csv_file)
fault_time = 709.6

# Get data right before and after fault
before = df[df['time_s'] < fault_time].iloc[-1]
after = df[df['time_s'] > fault_time].iloc[0]

print(f"BEFORE FAULT (at {before['time_s']:.1f}s):")
print(f"  Cell 5: {before['cell_5_V']:.3f}V")
other_before = sum([before[f'cell_{i}_V'] for i in [1,2,3,4,6,7]])/6
print(f"  Other cells avg: {other_before:.3f}V")

print(f"\nAFTER FAULT (at {after['time_s']:.1f}s, {after['time_s'] - fault_time:.2f}s after trigger):")
print(f"  Cell 5: {after['cell_5_V']:.3f}V")
other_after = sum([after[f'cell_{i}_V'] for i in [1,2,3,4,6,7]])/6
print(f"  Other cells avg: {other_after:.3f}V")

cell5_drop = before['cell_5_V'] - after['cell_5_V']
cell5_drop_pct = (cell5_drop / before['cell_5_V']) * 100

print(f"\nCELL 5 VOLTAGE DROP:")
print(f"  Drop: {cell5_drop:.3f}V ({cell5_drop_pct:.1f}%)")
print(f"  Expected: 10-30% for 0.1Ω hard short")
print(f"  Status: {'✓ PASS' if cell5_drop_pct >= 5.0 else '✗ FAIL'}")

