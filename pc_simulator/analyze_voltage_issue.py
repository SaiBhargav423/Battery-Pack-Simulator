import pandas as pd

df = pd.read_csv('output_final3/timeseries_data.csv')
fault_time = 709.6

# Get data at 710s (after fault)
row = df[df['time_s'] >= 710.0].iloc[0]
other_avg = sum([row[f'cell_{i}_V'] for i in [1,2,3,4,6,7]])/6

print(f"At {row['time_s']:.1f}s (after fault trigger):")
print(f"  Cell 5 voltage: {row['cell_5_V']:.3f}V")
print(f"  Other cells avg: {other_avg:.3f}V")
print(f"  Pack voltage: {row['pack_voltage_V']:.3f}V")
print(f"\nExpected Cell 5 voltage (with 16.7% drop from other cells):")
print(f"  {other_avg * 0.833:.3f}V")
print(f"\nDifference: {row['cell_5_V'] - other_avg * 0.833:.3f}V")
print(f"\nThis suggests the voltage divider is NOT being applied to Cell 5")

