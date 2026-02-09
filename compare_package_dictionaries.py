import json

def read_dictionary_from_file(file_path):
    """
    Reads a dictionary from a JSON file.

    :param file_path: Path to the JSON file.
    :return: Dictionary read from the file.
    """
    with open(file_path, 'r') as file:
        dictionary = json.load(file)
    return dictionary

def find_missing_components(main_dict, subset_dict):
    """
    Finds components that are in the main dictionary but missing in the subset dictionary.

    :param main_dict: The main dictionary.
    :param subset_dict: The subset dictionary.
    :return: List of missing components.
    """
    missing_components = [component for component in main_dict if component not in subset_dict]
    return missing_components

# Assuming 'main_dict.json' is the file with the main dictionary
# and 'subset_dict.json' is the file with the subset dictionary
main_dict_path = './Dictionaries/VS8.json'
subset_dict_path = './Dictionaries/VSNull.json'

# Read the dictionaries from their respective files
main_dict = read_dictionary_from_file(main_dict_path)
subset_dict = read_dictionary_from_file(subset_dict_path)

# Find missing components
missing_components = find_missing_components(main_dict, subset_dict)

# Print missing components, if any
if missing_components:
    print("Missing components:", missing_components)
else:
    print("No components are missing.")
