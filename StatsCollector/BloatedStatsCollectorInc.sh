#! /bin/bash
host=$(hostname -s)
log_dir=/var/log
outfilebase="${log_dir}/${host}-FileAccessDates"
# shellcheck disable=SC2034
outfile="${outfilebase}.csv"
bin_dir=/usr/local/bin
csv_sep='|'
