#!/usr/bin/env bash
set -x  # if anything fails  exit
if ! command -v shar &> /dev/null; then
  sudo apt install sharutils
  echo "sharutils Installed, proceeding"
fi
# Run AccessTimes.py in Creation Mode
# Call AccessTypes explicitly setting all arguments to thier default values
python3 AccessTimes.py --is_baseline=True --protected_packages=None --input_dir=insights-rand-1 --read_input_dir=insights-rand-1  --file_packages_suffix=aall_package_files.log --usage_suffix=usage.log --minimum_age_cutoff=45

python3 AccessTimes.py --is_baseline --read_input_dir=insights-rand-1