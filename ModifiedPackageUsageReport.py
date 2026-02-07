
import pandas as pd
import argparse
import os
from datetime import datetime, timedelta

# Parse command line arguments
parser = argparse.ArgumentParser(description='Package Usage Report')
parser.add_argument('-D', '--directories', nargs='+', help='Directories to scan', required=True)
args = parser.parse_args()

# Function to load CSVs from a directory
def load_csvs(directory):
    files_packages_path = os.path.join(directory, 'files_packages.csv')
    files_info_path = os.path.join(directory, 'files_info.csv')
    if not os.path.exists(files_packages_path) or not os.path.exists(files_info_path):
        print(f"CSV files not found in {directory}")
        return None, None
    files_packages = pd.read_csv(files_packages_path)
    files_info = pd.read_csv(files_info_path)
    return files_packages, files_info

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
