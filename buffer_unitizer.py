import pandas as pd
import re
import clipboard

# Headers patterns
headers_patterns = {
    'Memory': ['MB', 'GB'],
    'Storage': ['MB', 'GB', 'SSD', 'HDD'],
    'Processor': ['CPU', 'GHz']
}


def parse_cell(cell, patterns):
    regex = r"\b(" + '|'.join(patterns) + r")\b"
    matches = set(re.findall(regex, str(cell), re.IGNORECASE))
    for match in matches:
        cell = re.sub(match + r'\b', '', cell, flags=re.IGNORECASE).strip()
    matched_units = ' '.join(matches)
    return cell, matched_units


def update_sheet(sheet, headers_patterns):
    updated_sheet = sheet.copy()
    for column in sheet.columns:
        if column in headers_patterns:
            for i, cell in enumerate(sheet[column]):
                cleaned_value, unit_label = parse_cell(cell, headers_patterns[column])
                updated_sheet.at[i, column] = cleaned_value
                if unit_label:
                    updated_sheet.at[i, sheet.columns[0]] = f"{unit_label} {updated_sheet.at[i, sheet.columns[0]]}"
    return updated_sheet


def main():
    # Read data from clipboard into a DataFrame
    sheet = pd.read_clipboard()

    # Apply the formatting
    updated_sheet = update_sheet(sheet, headers_patterns)

    # Write the updated DataFrame back to clipboard
    clipboard.copy(updated_sheet.to_csv(index=False, sep='\t'))

    print("Updated data has been copied to clipboard. Please paste (CTRL+V) to see the results.")


if __name__ == "__main__":
    main()
