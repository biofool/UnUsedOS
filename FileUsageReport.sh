
output_file="/var/log/vems/NoRead28Days_$(hostname)${current_date}.log"
sudo find / -xdev ! -atime -28 -type f -printf '%p|%AY-%Am-%Ad,%AH:%AM:%AS\n' |sudo tee -a "${output_file}" > /dev/null &
output_file="/var/log/vems/Read28Days_$(hostname)${current_date}.log"
sudo find / -xdev -atime -28 -type f -printf '%p|%AY-%Am-%Ad,%AH:%AM:%AS\n' |sudo tee -a "${output_file}" > /dev/null
wait