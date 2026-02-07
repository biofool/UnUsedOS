import pandas as pd
# Load the CSV files
files_packages = pd.read_csv('files_packages.csv')  # Columns: path, package
files_info = pd.read_csv('files_info.csv', delimiter='|')  # Columns: path, creation_time, access_time

# Merge dataframes on 'path' with an outer join to find unmatched files
merged_df = pd.merge(files_packages, files_info, on='path', how='outer', indicator=True)

# Report files in files_packages that are not in files_info
unreported_files_packages = merged_df[merged_df['_merge'] == 'left_only']
print("Files in files_packages not in files_info:")
print(unreported_files_packages[['path']])

# Find directories with files not belonging to any package
# Extract directory names from paths
files_info['directory'] = files_info['path'].apply(lambda x: '/'.join(x.split('/')[:-1]))
# Filter out files that are not in files_packages
non_packaged_files = merged_df[merged_df['_merge'] == 'right_only']
# Group by directory and count files
# directory_counts = non_packaged_files.groupby('directory').size()
# print("\nDirectories with non-packaged files and their file counts:")
# print(directory_counts)

merged_df = pd.merge(files_packages, files_info, on='path')

# Group by 'package' and get the oldest 'access_time'
oldest_access_times = merged_df.groupby('package')['access_time'].min()

# Sort the packages by access time in ascending order
sorted_packages = oldest_access_times.sort_values()
print(sorted_packages)