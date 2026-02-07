import sys
import logging

# Configure the logger
logger = logging.getLogger('csv_error')
logger.setLevel(logging.ERROR)
#  Convert file_access.csv to file_access.psv
#  find UnusedOS/ -type f -name '*.csv' -print0 | xargs -0 -I {} sh -c 'echo {} "$(echo {} | sed "s/^[^-]*-//;s/,/|/g;s/.csv/.psv/")"'
# Create a file handler to log errors
file_handler = logging.FileHandler('error.log')
file_handler.setLevel(logging.ERROR)

# Create a formatter and set it for the handler
formatter = logging.Formatter('%(levelname)s: %(message)s')
file_handler.setFormatter(formatter)

# Add the handler to the logger
logger.addHandler(file_handler)

# Check if there are two command-line arguments
if len(sys.argv) != 3:
    print("Usage: python replace_last_3_commas.py package_file_path output_file")
    sys.exit(1)

input_file = sys.argv[1]
output_file = sys.argv[2]

try:
    with open(input_file, 'r') as fin, open(output_file, 'w') as fout:
        header=("path", "creation_time", "access_time")
        fout.write('|'.join(header) + '\n')
        for line in fin:
            input_text = line.strip()

            # Split the text into parts using rsplit
            parts = input_text.rsplit(',', 2)

            # Check if there are enough parts (at least 3 to replace 2 commas)
            if len(parts) == 3:
                # Replace the last two commas with a different character or string
                modified_text = parts[0] + '|' + '|'.join(parts[1:])
            else:
                # Make sure pipe seperated is 3 fields
                modified_text = input_text

            parts = modified_text.rsplit('|', 3)
            if len(parts) == 3:
                # Write the modified text to the output file
                fout.write('|'.join(parts) + '\n')
            else:
                logger.error("Unparseable: " + input_text)

except Exception as e:
    # Log the error using logger
    logger.error(str(e))
    print("An error occurred. See error.log for details.")
    sys.exit(1)
