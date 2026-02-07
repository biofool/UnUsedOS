import os
import traceback
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import re
import argparse

# Define file path and columns
columns = "timestamp,r,b,swpd,free,buff,cache,si,so,bi,bo,in,cs,us,sy,id,wa,st".split(',')
# Define descriptions
vmstat_descriptions = {
    'procs': {'r': 'Processes waiting for runtime', 'b': 'Processes in uninterruptible sleep'},
    'memory': {'swpd': 'Virtual memory used', 'free': 'Idle memory', 'buff': 'Memory used as buffers',
               'cache': 'Memory used as cache'},
    'swap': {'si': 'Memory swapped in from disk', 'so': 'Memory swapped to disk'},
    'io': {'bi': 'Blocks received from block device', 'bo': 'Blocks sent to block device'},
    'system': {'in': 'Interrupts per second', 'cs': 'Context switches per second'},
    'cpu': {'us': 'CPU time for user code', 'sy': 'CPU time for kernel code', 'wa': 'CPU idle with disk I/O request',
            'st': 'Stolen CPU time'},
    'idle': {'id': 'CPU idle with no disk I/O request'}
}

# Function to extract and parse the timestamp from each line
def extract_timestamp(line):
    time_regex = r"([A-Za-z]{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})"
    match = re.search(time_regex, line)
    if match:
        return match.group(1)
    else:
        raise ValueError(f"Timestamp not found in line: {line}")

def aggregate_large_df(df, timestamp_col='timestamp', threshold=40000, target_size=20000, descriptions=None):
    if len(df) > threshold:
        if timestamp_col not in df.columns:
            raise ValueError(f"The DataFrame does not have a column named '{timestamp_col}'.")
        df[timestamp_col] = pd.to_datetime(df[timestamp_col])
        resample_interval = calculate_resample_interval(df, target_size, timestamp_col)

        # Create a copy of the DataFrame with timestamp as index for resampling
        df_copy = df.set_index(timestamp_col)

        aggregated_min = df_copy.resample(resample_interval).min()
        aggregated_max = df_copy.resample(resample_interval).max()

        aggregated_df = pd.concat([aggregated_min.add_suffix('_min'), aggregated_max.add_suffix('_max')], axis=1)

        if descriptions:
            for group in descriptions:
                group_desc = descriptions[group].copy()
                for col, desc in group_desc.items():
                    descriptions[group][f'{col}_min'] = f"Min {desc}"
                    descriptions[group][f'{col}_max'] = f"Max {desc}"

        # Reset index to bring timestamp back as a column
        return aggregated_df.reset_index()
    else:
        return df

def calculate_resample_interval(df, target_size, timestamp_col='timestamp'):
    total_duration = (df[timestamp_col].max() - df[timestamp_col].min()).total_seconds()
    desired_interval_seconds = total_duration / target_size
    if desired_interval_seconds < 1:
        desired_interval_seconds = 1  # Set minimum interval to 1 second
    return f'{int(desired_interval_seconds)}s'



def plot_data_group(plot_site, name, plot_data, descriptions, pdf):
    plot_cols = descriptions[name].keys()
    fig, ax = plt.subplots(figsize=(20, 5))
    legend = []

    for plot_col in plot_cols:
        if plot_col not in plot_data.columns:
            print(f"Skipping missing column: {plot_col}")
            continue

        plot_data[f'{plot_col}'] = pd.to_numeric(plot_data[f'{plot_col}'])
        description = descriptions[name][f'{plot_col}']
        legend.append(description)
        ax.plot(plot_data['timestamp'], plot_data[f'{plot_col}'], label=description, lw=0.25)

    ax.set_title(f'Site: {plot_site} | Data Group: {name}')
    ax.set_xlabel("Dates", loc='left')
    ax.set_ylabel("Values")
    plt.xticks(fontsize=8, rotation=45)
    plt.subplots_adjust(bottom=.25)
    ax.legend(legend, loc='upper center', bbox_to_anchor=(0.5, -0.1), ncol=2)  # move legend under the graph
    pdf.savefig(fig)
    plt.close(fig)



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', help='Specifies the input file path')
    args = parser.parse_args()
    file_path = args.input
    data_dict = {col: [] for col in columns}

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The specified file does not exist: {file_path}")

    with open(file_path, 'r') as f:
        lines = [line.rstrip('\n') for line in f.readlines()]

        for line in lines:
            try:
                timestamp_str = extract_timestamp(line)
                data_values = line.split(",")[1:]
                data_dict['timestamp'].append(timestamp_str)

                for i, col in enumerate(columns[1:]):
                    value = pd.to_numeric(data_values[i], errors='coerce')
                    if pd.isna(value):
                        print(f"Value {data_values[i]} at index {i} is NaN")
                    else:
                        data_dict[col].append(value)
            except Exception as e:
                print(f"Error processing line: {line}")
                traceback.print_exc()
                continue

    data = pd.DataFrame(data_dict)
    now = datetime.now()
    data['timestamp'] = pd.to_datetime(data['timestamp'], format='%b %d %H:%M:%S')
    data['timestamp'] = data['timestamp'].apply(
        lambda x: x.replace(year=now.year if x.month <= now.month else now.year - 1))

    non_numeric_indices = set()
    for col in data.columns:
        temp_series = pd.to_numeric(data[col], errors='coerce')
        non_numeric_indices.update(temp_series[temp_series.isna()].index)

    if non_numeric_indices:
        print("Non-numeric records found at indices:")
        print(non_numeric_indices)
        print("Non-numeric records details:")
        print(data.loc[non_numeric_indices])
    else:
        print("No non-numeric records found.")

    data_clean = data.drop(frozenset(non_numeric_indices))

    for col in data_clean.columns:
        data_clean[col] = pd.to_numeric(data_clean[col], errors='coerce')

    df_aggregated = aggregate_large_df(data_clean, descriptions=vmstat_descriptions)

    pdf_file_name = os.path.splitext(file_path)[0] + '_plots.pdf'

    with PdfPages(pdf_file_name) as pdf:
        site_name = os.path.basename(file_path)
        for group in vmstat_descriptions.keys():
            try:
                plot_data_group(site_name, group, df_aggregated, vmstat_descriptions, pdf)
            except Exception as e:
                traceback.print_exc()
                print(f"Failed to process group {group}: {e}")

    print(df_aggregated.dtypes)
    print(df_aggregated.head())
