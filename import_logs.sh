#!/bin/bash
# Import all fileaccess.csv files in $dir to working set
# Verifies that files use "|" symbols for seperators and partially anonymizes them

find UnusedOS/ -type f -name '*.csv' -print0 | xargs -0 -I {} sh -c 'echo {} "$(echo {} | sed "s/^[^-]*-//;s/,/|/g;s/.csv/.psv/")"'
