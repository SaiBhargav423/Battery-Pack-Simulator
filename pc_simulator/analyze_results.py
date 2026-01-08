"""Quick script to analyze fault simulation results."""
import pandas as pd
import sys

if len(sys.argv) > 1:
    csv_file = sys.argv[1]
else:
    csv_file = 'output_test/timeseries_data.csv'

df = pd.read_csv(csv_file)
fault_time = 709.6

# Get data points
before = df[df['time_s'] < fault_time].iloc[-1]
after_5s = df[df['time_s'] > fault_time + 5]
if len(after_5s) > 0:
    after = after_5s.iloc[0]
else:
    after = df.iloc[-1]
final = df.iloc[-1]

print('=' * 80)
print('INTERNAL SHORT CIRCUIT FAULT ANALYSIS')
print('=' * 80)
print(f'\nBEFORE FAULT (at {before["time_s"]:.1f}s):')
print(f'  Cell 5 Voltage: {before["cell_5_V"]:.3f} V')
print(f'  Cell 5 Temp: {before["cell_5_temp_C"]:.1f} °C')
print(f'  Pack Voltage: {before["pack_voltage_V"]:.3f} V')
print(f'  Pack SOC: {before["soc_percent"]:.2f}%')

print(f'\nAFTER FAULT (at {after["time_s"]:.1f}s, {after["time_s"] - fault_time:.1f}s after trigger):')
print(f'  Cell 5 Voltage: {after["cell_5_V"]:.3f} V')
print(f'  Cell 5 Temp: {after["cell_5_temp_C"]:.1f} °C')
print(f'  Pack Voltage: {after["pack_voltage_V"]:.3f} V')

print(f'\nFINAL (at {final["time_s"]:.1f}s):')
print(f'  Cell 5 Voltage: {final["cell_5_V"]:.3f} V')
print(f'  Cell 5 Temp: {final["cell_5_temp_C"]:.1f} °C')
print(f'  Pack Voltage: {final["pack_voltage_V"]:.3f} V')
print(f'  Pack SOC: {final["soc_percent"]:.2f}%')

print(f'\n' + '=' * 80)
print('FAULT EFFECTS SUMMARY:')
print('=' * 80)

voltage_drop = before["cell_5_V"] - final["cell_5_V"]
voltage_drop_pct = (voltage_drop / before["cell_5_V"]) * 100.0
temp_rise = final["cell_5_temp_C"] - before["cell_5_temp_C"]

print(f'\nVOLTAGE DROP (Cell 5):')
print(f'  Initial: {before["cell_5_V"]:.3f} V')
print(f'  Final: {final["cell_5_V"]:.3f} V')
print(f'  Drop: {voltage_drop:.3f} V ({voltage_drop_pct:.1f}%)')

print(f'\nTEMPERATURE RISE (Cell 5):')
print(f'  Initial: {before["cell_5_temp_C"]:.1f} °C')
print(f'  Final: {final["cell_5_temp_C"]:.1f} °C')
print(f'  Rise: {temp_rise:.1f} °C over {final["time_s"] - fault_time:.1f} seconds')

# Compare with other cells
other_cells_avg_voltage = (final["cell_1_V"] + final["cell_2_V"] + final["cell_3_V"] + 
                          final["cell_4_V"] + final["cell_6_V"] + final["cell_7_V"]) / 6
voltage_difference = other_cells_avg_voltage - final["cell_5_V"]

print(f'\nCELL IMBALANCE:')
print(f'  Cell 5 Voltage: {final["cell_5_V"]:.3f} V')
print(f'  Other cells avg: {other_cells_avg_voltage:.3f} V')
print(f'  Difference: {voltage_difference:.3f} V')

print(f'\n' + '=' * 80)
print('VALIDATION vs LITERATURE:')
print('=' * 80)
print(f'  Expected voltage drop: 10-30% for 0.1Ω hard short')
print(f'  Actual voltage drop: {voltage_drop_pct:.1f}%')
print(f'  Status: {"✓ PASS" if voltage_drop_pct >= 5.0 else "✗ FAIL (too small)"}')

print(f'\n  Expected temp rise: 20-50°C within minutes')
print(f'  Actual temp rise: {temp_rise:.1f}°C over {final["time_s"] - fault_time:.1f}s')
print(f'  Status: {"✓ PASS" if temp_rise >= 5.0 else "✗ FAIL (too small)"}')

