#!/bin/bash

# File to store the output
output_file="all_package_files.txt"

# Empty the output file if it already exists
> "$output_file"

# List all packages and their installed files
for package in $(dpkg --get-selections | grep -v deinstall | cut -f1); do
    for file_path in $(dpkg -L "$package"); do
        if [ -e "$file_path" ]; then  # Check if the file exists
            echo "$file_path|$package" >> "$output_file"
        fi
    done
done

echo "Output written to $output_file"
