import pandas as pd

# Step 1: Read the Excel file
df = pd.read_excel('/Users/kkron/projects/Vigilent/Security/UnusedOS/input.xlsx')

# Step 2: Pivot the DataFrame
df_transposed = df.transpose()

# Step 3: Break out Configuration column
# Assuming that the Configuration column is a comma-separated string of values
df_transposed['Configuration'] = df_transposed['Configuration'].str.split(',')

# Explode the Configuration column into separate rows
df_transposed = df_transposed.explode('Configuration')

# Step 4: Write to Excel
# Install the openpyxl engine to handle xlsx files
df_transposed.to_excel('/Users/kkron/projects/Vigilent/Security/UnusedOS/output.xlsx', engine='openpyxl')
