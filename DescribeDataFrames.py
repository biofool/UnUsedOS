import json
import sys


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
        "name": "packages_df",
        "source": "packages_input_file",
        "purpose": " file paths and associated packages from the package files log."
    },
    {
        "name": "usage_df",
        "source": "usage_input_file",
        "purpose": " file usage information including path, creation time, and last access time."
    },
    {
        "name": "files_info_filtered",
        "source": "df after dropping rows with NaN access times",
        "purpose": "Filtered version of 'df', excluding rows with NaN access times."
    },
    {
        "name": "unneeded_files",
        "source": "files_info_filtered with access times beyond a certain threshold",
        "purpose": "Subset of 'files_info_filtered' identifying files not accessed within a specified recent period."
    },
    # {
    #     "name": "df",
    #     "source": "files_info_filtered grouped by normalized access days",
    #     "purpose": "Aggregation of file access counts per normalized access day."
    # },
    {
        "name": "filtered_df",
        "source": "files_info_filtered filtered by a specific range of normalized access days",
        "purpose": "Files accessed within a specific timeframe relative to the system's last build date."
    },
    {
        "name": "merged_df",
        "source": "Outer join of files_packages_df and files_info_filtered on 'path'",
        "purpose": "Merged dataset to identify unmatched files between packages and usage logs."
    },
    {
        "name": "latest_access_per_time",
        "source": '"merged_df_sorted[["access_time", "package"]].groupby(\'access_time\').tail(1)"',
        "purpose": "Merged dataset to identify last access of  packages ."

    },

    {
        "name": "packaged_files",
        "source": "merged_df with '_merge' indicator as 'both'",
        "purpose": "Filtered 'merged_df' to only include files that are found in both packages and usage logs."
    }
]
def write_dataframes_to_md(df_readme = 'DFReadme', dataframes_analysis = dataframes_analysis):
    with open('%s.md' % df_readme, 'w') as file:
        for dataframe in dataframes_analysis:
            # Placeholder DataFrame call - replace `your_dataframe` with actual DataFrame variable
            # dataframe_structure_as_json(your_dataframe, dataframe["purpose"])
            file.write(f"--- DataFrame: {dataframe['name']} ---")
            file.write(f"Source: {dataframe['source']}")
            file.write(f"Purpose: {dataframe['purpose']}\n")
            file.write(dataframe.dtypes.to_string())
