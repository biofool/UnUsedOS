import pandas as pd
import os
import argparse
from glob import glob

# Parse command line arguments
parser = argparse.ArgumentParser()
parser.add_argument("-D", "--directory", help="Directory to read csv files from")
args = parser.parse_args()

# Define function to load and merge csv files in a directory
def load_and_merge(directory):
    # Load the CSV files
    files_packages_path = os.path.join(directory, 'files_packages.csv')  # Columns: path, package
    files_info_path = os.path.join(directory, 'files_info.csv')  # Columns: path, creation_time, access_time
    files_packages = pd.read_csv(files_packages_path)
    files_info = pd.read_csv(files_info_path, delimiter='|')
    # Merge dataframes on 'path' with an outer join to find unmatched files
    merged_df = pd.merge(files_packages, files_info, on='path', how='outer', indicator=True)
    return merged_df

# Get a list of csv files from all subdirectories
directories = [x[0] for x in os.walk(args.directory)]

# Load and merge all csv files in all subdirectories
merged_dfs = [load_and_merge(directory) for directory in directories]

# Concatenate all merged dataframes
final_df = pd.concat(merged_dfs)

# Report files in files_packages that are not in files_info
unreported_files_packages = final_df[final_df['_merge'] == 'left_only']
print("Files in files_packages not in files_info:")
print(unreported_files_packages[['path']])

# Find directories with files not belonging to any package
# Extract directory names from paths
final_df['directory'] = final_df['path'].apply(lambda x: '/'.join(x.split('/')[:-1]))
# Filter out files that are not in files_packages
non_packaged_files = final_df[final_df['_merge'] == 'right_only']
# Group by directory and count files
directory_counts = non_packaged_files.groupby('directory').size()
print("\nDirectories with non-packaged files and their file counts:")
print(directory_counts)

# Group by 'package' and get the oldest 'access_time'
oldest_access_times = final_df.groupby('package')['access_time'].min()
# Sort the packages by access time in ascending order
sorted_packages = oldest_access_times.sort_values()