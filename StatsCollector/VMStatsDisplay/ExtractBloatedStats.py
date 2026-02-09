BloatedSTAT_KEY = 'BloatedStat'
VOWELS = "AEIOUaeiou"
open_files = {}  # Dictionary to keep track of open file descriptors

import base64


class Count_Base_64:
    def __init__(self):
        self.lines = 0
        self.errors = 0

    def increment_to_base64(self, value):
        # Get the value as bytes in big-endian (most significant byte first) order.
        value_as_bytes = (value + 1).to_bytes(6, 'big')
        return base64.b64encode(value_as_bytes).decode('utf-8').lstrip('A')

    def update_status(self, is_line):
        if is_line:
            self.lines += 1
        else:
            self.errors += 1

        lines_64 = self.increment_to_base64(self.lines)
        errors_64 = self.increment_to_base64(self.errors)

        print(f'\rBase 64 counters: Parsable Lines: {lines_64} Non-Parsable Lines: {errors_64}', end='', flush=True)


status = Count_Base_64()


def remove_vowels_and_convert_numbers(s):
    result = ''
    for char in s:
        if char in VOWELS:
            continue  # skip vowels
        elif char.isdigit():
            result += hex(int(char))[2:]  # convert digit to hex
        else:
            result += char
    return result


import re


def read_timestamp_and_hostname(before_vstat):
    if len(before_vstat[-1]) < 1:
        before_vstat = before_vstat[:-1]
    if not (
            all(item.isdigit() and len(item) == 2 for item in before_vstat[-4:-2]) and
            all(item.isdigit() and len(item) < 2 for item in before_vstat[-5]) and
            before_vstat[-6].isalpha()
    ):
        return None, None
    else:
        time_stamp = ' '.join(before_vstat[-6:-4]) + ' ' + ":".join(before_vstat[-4:-1])
        hostname = remove_vowels_and_convert_numbers(before_vstat[-1])
        return time_stamp, hostname


def write_line_to_file(filename, time_stamp, data_columns, open_files):
    modified_line = f'{time_stamp},{",".join(data_columns)}\n'
    if len(open_files) >= 10 and filename not in open_files:
        raise Exception("Maximum number of open files exceeded.")
    if filename not in open_files:
        open_files[filename] = open(filename, 'w')
        print(f"Opened file {filename}.")
    open_files[filename].write(modified_line)


bloated_keys = set()

def process_line(line, modified_hostname, time_host_re):
    try:
        if match := re.search(rf'({BloatedSTAT_KEY}\S+):', line, flags=re.IGNORECASE):
            bloated_key = match.group(1)
            before_vstat, after_vstat = re.split(f'{bloated_key}:', line, flags=re.IGNORECASE)
            data_columns = after_vstat.split()
            if bloated_key not in bloated_keys:
                print(f"Adding {bloated_key}")
                bloated_keys.add(bloated_key)
        else:
            return
        if bloated_key not in "BloatedStatIO":
            if data_columns:
                if not all(item.isnumeric() for item in data_columns):
                    if line.endswith("procs -----------memory---------- ---swap-- -----io---- -system-- ------cpu-----\n"):
                        status.update_status(True)
                    else:
                        status.update_status(False)
                    return
                status.update_status(True)
            else:
                status.update_status(False)
                return
        else:
            if line.endswith(']\n'):
                status.update_status(False)
                return


    except ValueError:
        status.update_status(False)
        return

    match = time_host_re.search(before_vstat)

    if match:
        timestamp = match.group(1)
    else:
        status.update_status(False)
        print(f"Missing timestamp for {line}")
        return

    filename = f'{modified_hostname}_{bloated_key}.log'
    try:
        write_line_to_file(filename, timestamp, data_columns, open_files)
    except Exception as e:
        raise Exception(f"")


from subprocess import Popen, PIPE


def process_file(input_data, hostname, re):
    with Popen(['sort', '-u'], stdin=input_data, stdout=PIPE) as sort_proc:
        for line in sort_proc.stdout:
            process_line(line.decode(), hostname, re)  # decode bytes to string

# def write_records():
#     for filename, lines in records.items():
#         with open(filename, 'w') as file:
#             file.writelines(lines)

def close_files():
    for file in open_files.values():
        file.close()


import sys
import os


def main():
    import re

    # Regular expression pattern to match timestamp and the following word
    time_host_re = re.compile(r'(\w+\s+\d+\s+\d{2}:\d{2}:\d{2})\s+(\S+)')

    # Extract matches
    input_source = None
    # Check if stdin is provided
    if not sys.stdin.isatty():
        input_source = sys.stdin
    else:
        # Check if the first argument is a readable file
        if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]) and os.access(sys.argv[1], os.R_OK):
            input_source = open(sys.argv[1], 'r')
        else:
            # Check for 'syslog.all'
            if os.path.isfile('syslog.all') and os.access('syslog.all', os.R_OK):
                input_source = open('syslog.all', 'r')
    # If an input source is determined
    time_host_re = re.compile(r'(\w+\s+\d+\s+\d{2}:\d{2}:\d{2})\s+(\S+)')
# example
    if input_source:
        try:
            first_line = input_source.readline().strip()
            # burn the first line of data for the hostname and simpler logic it can be misleading anyway if vmstat just started
            match = time_host_re.search(first_line)
            if match:
                timestamp = match.group(1)
            else:
                raise ValueError("The format of the first line is incorrect.")

            process_file(input_source,  remove_vowels_and_convert_numbers(match.group(2)), time_host_re
                         )
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            input_source.close()
            close_files()  # Ensure all files are closed at the end
    else:
        print("No valid input source found.")


if __name__ == "__main__":
    main()
