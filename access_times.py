# Sample data
import pandas as pd
import os

KERNEL_VER = '/boot/vmlinuz-.*'


def print_intervals(df, intervals):
    # Check if 'access_time' column exists
    if 'access_time' not in df.columns:
        return [0]  # if 'access_time'
    seconds_in_a_day = 86400
    counts = [len(df)]
    if 'access_time_days' not in df.columns:
        df['access_time'] = pd.to_numeric(df['access_time'], errors='coerce')
        intervals_in_seconds = [x * seconds_in_a_day for x in intervals]
        previous_interval_seconds = 0
        for interval_seconds in intervals_in_seconds:
            count = df[(df['access_time'] > previous_interval_seconds) & (df['access_time'] <= interval_seconds)].shape[
                0]
            counts.append(count)
            previous_interval_seconds = interval_seconds
    else:
        previous_interval_days = 0
        for interval_days in intervals:
            count = \
                df[(df['access_time_days'] > previous_interval_days) & (df['access_time_days'] <= interval_days)].shape[0]
            counts.append(count)
            previous_interval_days = interval_days
    return counts


# Example usage
# Assuming `df` is your DataFrame and it either has 'access_time_days' or 'access_time' columns
# intervals = [13, 28, 45]
# print_intervals(df, intervals)

def read_csv_filter_convert(file_path_local, column_names, numeric_tail, delimiter='|'):
    """
    Reads a CSV local_file, filtering lines with exactly len(column_names) columns and where the last {numeric_tail}
     columns must be numeric.

    Parameters:
    - file_path: Path to the CSV local_file.

    Returns:
    - A DataFrame containing valid rows.
    - The count of fields that could not be converted to numbers.
    """
    valid_rows = []  # List to store valid rows
    non_convertible_count = 0  # Count of non-convertible fields

    with open(file_path_local, 'r') as local_file:
        for line in local_file:
            columns = line.strip().split(delimiter)  # Assuming '|' as the delimiter, adjust if necessary

            if len(columns) == len(column_names):  # Check if the line has exactly 3 columns
                try:
                    # Attempt to convert 2nd and 3rd columns to floats
                    for conv_item in range(1, numeric_tail + 1):
                        columns[-conv_item] = float(columns[-conv_item])
                    valid_rows.append(columns)  # Add to valid rows if successful
                except ValueError:
                    # Count each failed conversion attempt
                    non_convertible_count += 1

    # Create DataFrame from valid rows
    df = pd.DataFrame(valid_rows, columns=column_names)

    return df, non_convertible_count


def create_package_dframes(rp_file_packages, rp_file_usage):
    """
    Reads and processes package files and usage logs to generate insights into file access patterns.

    Parameters:
    - rp_file_packages: input for package files.
    - rp_file_usage: input for usage log files.

    Returns:
    - A collection of DataFrames with processed data.
    """
    # Construct file paths
    # Define columns for reading CSVs
    file_package_map = ['path', 'package']
    file_times_map = ['path', 'creation_time', 'access_time']

    # Read and process package files

    packages_df, dirty_packages = read_csv_filter_convert(
        rp_file_packages, file_package_map, 0, '|')

    # Read and process usage logs
    usage_df, non_convertible_count = read_csv_filter_convert(
        rp_file_usage, file_times_map, 2, delimiter='|')
    seconds_in_a_day = 86400
    # Process access times
    debug_interval = [8, 91, 1000]
    counts = print_intervals(usage_df, debug_interval)
    print(f"Total number of entries in df: {len(usage_df)}")
    print("Count array:", counts)
    usage_df['access_time_days'] = (usage_df['access_time'] // seconds_in_a_day).astype(int)
    min_day = usage_df['access_time_days'].min()
    usage_df['access_time_days_normalized'] = usage_df['access_time_days'] - min_day
    print(f"Total number of entries in df after days: {len(usage_df)}")
    counts = print_intervals(usage_df, debug_interval)
    print("Count array:", counts)
    # Identify unneeded files based on access times
    #
    # Aggregate data to count files per normalized access day
    rp_daily_counts = usage_df.groupby('access_time_days_normalized').size()

    # Merge DataFrames to identify unmatched files
    rp_merged_df = pd.merge(packages_df, usage_df, on='path', how='outer', indicator=True)
    print(f"Total number of entries in rp_merged_df : {len(rp_merged_df)}")
    counts = print_intervals(rp_merged_df, debug_interval)
    print("Count array:", counts)
 #   rp_merged_df['directory'] = rp_merged_df['path'].apply(lambda x: os.path.dirname(x) if pd.notnull(x) else x)
    rp_merged_df.fillna({'package': 'Unknown', 'creation_time': pd.NaT, 'access_time': pd.NaT}, inplace=True)
    rp_merged_df = rp_merged_df[~rp_merged_df['package'].str.contains('Unknown|unknown')]
    running_kernel = \
        rp_merged_df[rp_merged_df['path'].str.contains('%s' % KERNEL_VER, regex=True)].nsmallest(1, 'access_time_days')[
            'path'].values[0]

    print(f"Total number of entries in rp_merged_df : {len(rp_merged_df)}")
    counts = print_intervals(rp_merged_df, debug_interval)
    print("Count array:", counts)
    print(f"Total number of entries in packages_df : {len(packages_df)}")
    counts = print_intervals(packages_df, debug_interval)
    print("Count array:", counts)
    # from UnusedOS.DescribeDataFrames import write_dataframes_to_md
    # write_dataframes_to_md()
    return packages_df, rp_daily_counts, rp_merged_df, usage_df, running_kernel


if __name__ == "__main__":
    import argparse
    import os


    def check_directory(directory):
        if not os.path.isdir(directory):
            raise argparse.ArgumentTypeError(f"{directory} is not a valid directory in {os.path.abspath(os.curdir)}")
        return directory


    file_packages_suffix = "all_package_files.log"
    file_usage_suffix = "usage.log"

    parser = argparse.ArgumentParser(description='Advanced Argument Processor')
    parser.add_argument('--is_baseline', type=bool, default=False, help='Set is_baseline (True/False)')
    parser.add_argument('--protected_packages', type=str, help='Specify protected packages')
    parser.add_argument('--input_dir', type=check_directory, help='Specify input directory')
    parser.add_argument('--file_packages_suffix', type=str, default=file_packages_suffix,
                        help='Specify file packages suffix')
    parser.add_argument('--usage_suffix', type=str, default=file_usage_suffix, help='Specify usage suffix')
    parser.add_argument('--minimum_age_cutoff', type=int, default=45, help='Specify minimum age cutoff')
    # minimum_age_cutoff = args.minimum_age_cutoff
    # if minimum_age_cutoff <= 0:
    #     raise argparse.ArgumentTypeError(f"{minimum_age_cutoff} is not a positive integer")
    # # Validate if rp_file_packages and usage_suffix exist in the read_input_dir

    args = parser.parse_args()
    is_baseline = args.is_baseline
    protected_packages = args.protected_packages
    input_dir = args.input_dir
    file_packages_suffix = args.file_packages_suffix
    usage_suffix = args.usage_suffix

    package_file_path = os.path.join(input_dir, f"{input_dir}-{file_packages_suffix}")
    if not os.path.exists(package_file_path):
        raise argparse.ArgumentTypeError(f"{file_packages_suffix} does not exist in {input_dir}")
    usage_file_path = os.path.join(input_dir, f"{input_dir}-{usage_suffix}")

    if not os.path.exists(usage_file_path):
        raise argparse.ArgumentTypeError(f"{usage_suffix} does not exist in {input_dir}")

    print("is_baseline:", is_baseline)
    print("protected_packages:", protected_packages)
    print("read_input_dir:", input_dir)
    print("rp_file_packages:", file_packages_suffix)
    print("usage_suffix:", usage_suffix)

    # Now you can use these variables in your program
    print("is_baseline:", is_baseline)
    print("protected_packages:", protected_packages)
    print("input_folder:", input_dir)
    # %%

    # Process files
    files_packages_df, daily_counts, merged_df, unneeded_files, version = (
        create_package_dframes(package_file_path,
                               usage_file_path))
    from shlex import join

    # rp_daily_counts = df.groupby('access_time_days_normalized').size()

    merged_df_sorted = merged_df.sort_values("access_time")
    latest_access_per_time = merged_df_sorted[["access_time", "package"]].groupby('access_time').tail(1)
    packages = (latest_access_per_time[["access_time", "package"]].drop_duplicates(["package"]))
    #
    never_include_packages = ["base-files", "coreutils"]  # replace with your list of package names
    protected_packages = 'protected_packages.txt'
    with open('%s' % protected_packages, 'w') as file:
        for item in never_include_packages:
            file.write(str(item) + '\n')

    with open(protected_packages, 'r') as file:
        never_include_packages = [line.strip() for line in file]
    reporting_intervals = [13, 28, 45]

    filtered_packages = packages[~packages["package"].isin(never_include_packages)]
    dpkg_commands = [pkg for pkg in filtered_packages["package"]]
    # Define reporting_intervals based on age ranges (in days)

    # Initialize the previous interval limit
    previous_interval = 0

    # Filter packages based on their ages falling into the reporting_intervals
    for interval in reporting_intervals:
        packages_in_interval = \
            merged_df[
                (merged_df['access_time_days'] > previous_interval) & (merged_df['access_time_days'] <= interval)][
                'package'].unique()

        print(f"Packages in the age interval {previous_interval + 1}-{interval} days:")
        for package in packages_in_interval:
            print(package)

        # Update the previous_interval for the next iteration
        previous_interval = interval
