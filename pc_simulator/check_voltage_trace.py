import pandas as pd
import sys

csv_file = sys.argv[1] if len(sys.argv) > 1 else 'output_final2/timeseries_data.csv'
df = pd.read_csv(csv_file)
fault_time = 709.6

# Get data around fault trigger
around_fault = df[(df['time_s'] >= fault_time - 1) & (df['time_s'] <= fault_time + 5)]

print("Voltage trace around fault trigger:")
print(f"{'Time':<8} {'Cell5_V':<10} {'Other_avg':<10} {'Pack_V':<10}")
print("-" * 45)

for idx, row in around_fault.iterrows():
    other_avg = sum([row[f'cell_{i}_V'] for i in [1,2,3,4,6,7]])/6
    print(f"{row['time_s']:>7.1f}s {row['cell_5_V']:>9.3f}V {other_avg:>9.3f}V {row['pack_voltage_V']:>9.3f}V")

