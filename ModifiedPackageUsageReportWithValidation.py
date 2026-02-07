
import pandas as pd
import argparse
import os
from datetime import datetime, timedelta

# New read_validate_csv function
def read_validate_csv(file_path_local, column_names, numeric_tail, delimiter='|'):
    valid_rows = []
    non_convertible_count = 0

    with open(file_path_local, 'r') as file:
        for line in file:
            columns = line.strip().split(delimiter)
            if len(columns) == len(column_names):
                try:
                    for item in range(1, numeric_tail + 1):
                        columns[-item] = float(columns[-item])
                    valid_rows.append(columns)
                except ValueError:
                    non_convertible_count += 1

    df = pd.DataFrame(valid_rows, columns=column_names)
    return df, non_convertible_count

# Updated function to load CSVs using read_validate_csv
def load_csvs(directory):
    files_packages_path = os.path.join(directory, 'files_packages.csv')
    files_info_path = os.path.join(directory, 'files_info.csv')
    error_threshold = 0.05  # 5% error threshold
    
    # Adjustments for files_packages.csv
    files_packages, non_convertible_count_packages = read_validate_csv(files_packages_path, ['path', 'package'], 0, ',')
    if non_convertible_count_packages / len(files_packages) > error_threshold:
        print(f"Too many errors in {files_packages_path}, skipping file.")
        return None, None
    
    # Adjustments for files_info.csv
    files_info, non_convertible_count_info = read_validate_csv(files_info_path, ['path', 'creation_time', 'access_time'], 2, '|')
    if non_convertible_count_info / len(files_info) > error_threshold:
        print(f"Too many errors in {files_info_path}, skipping file.")
        return None, None
    
    return files_packages, files_info

# Parse command line arguments
parser = argparse.ArgumentParser(description='Package Usage Report')
parser.add_argument('-D', '--directories', nargs='*', default=['./'], help='Directories to scan')

args = parser.parse_args()

# Function to filter packages not accessed in the last 90 days
def filter_old_packages(files_info):
    ninety_days_ago = datetime.now() - timedelta(days=90)
    files_info['access_time'] = pd.to_datetime(files_info['access_time'])
    return files_info[files_info['access_time'] < ninety_days_ago]

# Main processing
common_packages = None
for directory in args.directories:
    files_packages, files_info = load_csvs(directory)
    if files_packages is None or files_info is None:
        continue
    files_info_filtered = filter_old_packages(files_info)
    if common_packages is None:
        common_packages = set(files_packages['package'])
    else:
        common_packages.intersection_update(files_packages['package'])

# Display packages common in all directories
print("Packages not accessed in the last 90 days and common across all directories:")
for package in common_packages:
    print(package)
