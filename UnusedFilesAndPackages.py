#!/usr/bin/env python
import json


import os
import pprint

import pandas as pd
from matplotlib import pyplot as plt

import access_times

files_packages_columns = ['path', 'package']
files_info_columns = ['path', 'creation_time', 'access_time']

input_dir = "insights-rand-1"
file_packages_suffix = "all_package_files.log"
file_usage_suffix = "usage.log"
packages_input_file = os.path.join(input_dir, f"{input_dir}-{file_packages_suffix}")
usage_input_file = os.path.join(input_dir, f"{input_dir}-{file_usage_suffix}")
files_packages_df, DirtyPackages = access_times.read_csv_filter_convert(packages_input_file, files_packages_columns, 0,
                                                                        '|')
# Aggregate the data to count files per normalized access day
input_dir = "insights-rand-1"
file_packages_suffix = "all_package_files.log"
file_usage_suffix = "usage.log"

# Example usage
file_path = usage_input_file  # Update this to the path of your CSV file
df, non_convertible_count = access_times.read_csv_filter_convert(file_path, files_info_columns, 2, delimiter='|')

print(df.head())  # Preview the valid data
print(f"Number of rows that could not be converted: {non_convertible_count}")

# Convert access_time to days (ignoring fractional seconds)
seconds_in_a_day = 86400

# Filter out rows where 'access_time_numeric' is NaN (i.e., non-convertible values)
initial_row_count = df.shape[0]
files_info_filtered = df.dropna(subset=['access_time']).copy()
final_row_count = files_info_filtered.shape[0]

dropped_rows = initial_row_count - final_row_count
print(f'The number of dropped rows is {dropped_rows}')

# In[6]:


files_info_filtered['access_time_days'] = (files_info_filtered['access_time'] // seconds_in_a_day).astype(int)

# Normalize so the earliest time is day 0
min_day = files_info_filtered['access_time_days'].min()

files_info_filtered['access_time_days_normalized'] = files_info_filtered['access_time_days'] - min_day
min_day = files_info_filtered['access_time_days_normalized'].min()
access_time_max = files_info_filtered['access_time_days_normalized'].max() - 45

unneeded_files = files_info_filtered[files_info_filtered['access_time_days_normalized'] > access_time_max]
unneeded_files.describe()

# In[7]:


# Aggregate the data to count files per normalized access day
daily_counts = files_info_filtered.groupby('access_time_days_normalized').size()
print(files_info_filtered.describe())
# Define the min and max thresholds for access_time_days_normalized
min_threshold = files_info_filtered['access_time_days_normalized'].max() - 14
max_threshold = 7

# Use boolean indexing to filter rows within the defined range
filtered_df = files_info_filtered[(files_info_filtered['access_time_days_normalized'] >= min_threshold) & (
        files_info_filtered['access_time_days_normalized'] <= max_threshold)]

# Calculate the percentage
percentage = (len(filtered_df) / len(files_info_filtered)) * 100

print(f"Percentage of rows where access_time_days_normalized is between max - 14 and 7 is: {percentage}%")
#
# # Plot an Area Graph
plt.figure(figsize=(12, 6))
plt.fill_between(daily_counts.index, daily_counts.values, step="pre", alpha=0.4)
plt.plot(daily_counts.index, daily_counts.values, label='Files LastAccessed Day')

plt.title('File Access Distribution Over Days')
plt.xlabel('Days Since System Build')
plt.ylabel('Number of Files Accessed')
plt.legend()
plt.grid(True)
# plt.show()
# # Plot an Area Graph


# In[8]:


# Create DataFra
# Convert epoch microseconds to days and normalize
# Assuming 'creation_time' and 'access_time' are in microseconds

print(f"Loaded {len(files_packages_df)} valid records from {packages_input_file} with {DirtyPackages} errors.")
files_packages_df

# In[9]:


# Merge dataframes on 'path' with an outer join to find unmatched files
merged_df = pd.merge(files_packages_df, files_info_filtered, on='path', how='outer', indicator=True)

# Report files in files_packages that are not in files_info
unreported_files_packages = merged_df[merged_df['_merge'] == 'left_only']
print("Files in files_packages not in files_info:")
print(unreported_files_packages[['path']])

# Add 'directory' column to merged_df by extracting it from the 'path' column
merged_df['directory'] = merged_df['path'].apply(lambda x: '/'.join(x.split('/')[:-1]) if pd.notnull(x) else x)
merged_df.fillna({'package': 'Unknown', 'creation_time': pd.NaT, 'access_time': pd.NaT}, inplace=True)

# Filter out files that are not in files_packages
non_packaged_files = merged_df[merged_df['_merge'] == 'right_only']

# Group by directory and count files
directory_counts = non_packaged_files.groupby('directory').size()
top_10_directories = directory_counts.nlargest(10)

print("\nTop 10 directories with non-packaged files and their file counts:")
print(top_10_directories)
oldest_access_times = merged_df
try:
    # Assert that 'access_time' is datetime type
    # assert pd.api.types.is_integer(merged_df['access_time'])

    # Group by 'package' and get the oldest 'access_time'
    try:
        # Group by 'package' and get the oldest 'access_time'
        oldest_access_times = merged_df.groupby('package')['access_time'].min()
    except Exception as e:
        print(f"An error occurred while processing the data: {e}")

    if merged_df.duplicated(['path']).any():
        duplicates = merged_df[merged_df.duplicated(['path'], keep=False)]

        print("Duplicate paths found after merging. Please review the data.")
        print(merged_df[['path', 'package']])

        # Sort the packages by access time in ascending order

    # Sort the packages by access time in ascending order
    sorted_packages = oldest_access_times.sort_values()

# except AssertionError:
except Exception as e:
    print(f"'access_time' is not of datetime type. Please check your 'files_info.csv' file.{e}")

# In[10]:


packaged_files = merged_df[merged_df['_merge'] == 'both']
df_sorted = packaged_files.sort_values(by=['package', 'path', 'access_time'])
print("\npackaged_files.sort_values(by=['package', 'path', 'access_time']:")

print(df_sorted[['package', 'path', 'access_time']])



def dataframe_structure_as_json(df, descriptor):
    """
    Prints the structure of a pandas DataFrame as JSON, including a descriptor.

    Parameters:
    - df: Pandas DataFrame whose structure is to be printed.
    - descriptor: Text description of the DataFrame.
    """
    # Generate DataFrame structure
    structure = {
        "descriptor": descriptor,
        "columns": list(df.columns),
        "dtypes": df.dtypes.apply(lambda x: str(x)).to_dict(),
        "shape": df.shape
    }

    # Convert structure to JSON and print
    print(json.dumps(structure, indent=4))


# List of DataFrames created in the provided code snippet, their data source, and purpose
dataframes_analysis = [
    {
        "name": "files_packages_df",
        "df": files_packages_df,
        "source": "packages_input_file",
        "purpose": "Contains file paths and associated packages from the package files log."
    },
    {
        "name": "df",
        "df": df,
        "source": "usage_input_file",
        "purpose": "Holds file usage information including path, creation time, and last access time."
    },
    {
        "name": "files_info_filtered",
        "df": files_info_filtered,
        "source": "df after dropping rows with NaN access times",
        "purpose": "Filtered version of 'df', excluding rows with NaN access times."
    },
    {
        "name": "unneeded_files",
        "df": unneeded_files,
        "source": "files_info_filtered with access times beyond a certain threshold",
        "purpose": "Subset of 'files_info_filtered' identifying files not accessed within a specified recent period."
    },
    {
        "name": "daily_counts",
        "df": daily_counts,
        "source": "files_info_filtered grouped by normalized access days",
        "purpose": "Aggregation of file access counts per normalized access day."
    },
    {
        "name": "filtered_df",
        "df": filtered_df,
        "source": "files_info_filtered filtered by a specific range of normalized access days",
        "purpose": "Files accessed within a specific timeframe relative to the system's last build date."
    },
    {
        "name": "merged_df",
        "df": merged_df,
        "source": "Outer join of files_packages_df and files_info_filtered on 'path'",
        "purpose": "Merged dataset to identify unmatched files between packages and usage logs."
    },
    {
        "name": "packaged_files",
        "df": packaged_files,
        "source": "merged_df with '_merge' indicator as 'both'",
        "purpose": "Filtered 'merged_df' to only include files that are found in both packages and usage logs."
    }
]

# Placeholder for DataFrame structure analysis. Actual DataFrame instances not available in this context.
# The following code snippet is an example of how to call `dataframe_structure_as_json` with analysis.
with open('DFReadme.md', 'w') as file:
    for dataframe in dataframes_analysis:
        # Placeholder DataFrame call - replace `your_dataframe` with actual DataFrame variable
        # dataframe_structure_as_json(your_dataframe, dataframe["purpose"])
        file.write(f"--- DataFrame: {dataframe['name']} ---\n")
        file.write(f"Source: {dataframe['source']}\n")
        file.write(f"Purpose: {dataframe['purpose']}\n")
        file.write(pprint.pformat(dataframe['df'].dtypes, indent=4))
        file.write("\n\n")
