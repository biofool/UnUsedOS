#!/bin/bash

# Source the included file
#. ./WhatsUnusedInc.sh

# Initialize debug mode
debug_mode=off

# Function to display usage information
usage() {
    if [ "$#" -gt 0 ]; then
        echo "$1"
        echo "Usage: $0 [OPTIONS]"
    else
        echo "Usage: $0 [OPTIONS]"
        echo "  OPTIONS:"
        echo "    -t, --threshold SECONDS"
        echo "                     Set the time threshold in SECONDS (default: 600)."
        echo "    -d, --directories DIRS"
        echo "                     Specify a colon-separated list of directories to search."
        echo "                     (default: all mounted ext4 file systems)."
        echo "    -u, --unused_window SECONDS"
        echo "                     Set the time window in days during which a file must not"
        echo "                     have been modified or read to be considered unused (default: 30)."
        echo "    -m, --monitor"
        echo "                     Run in monitor loops with sort -u & sleep minutes between loops."
        echo "                     no -m run once"
        echo "                     -m=n>0 (monitor for N+1 iteration)"
        echo "                     -m=0 infinite loop"
        echo "    -s, --sleep"
        echo "                     In monitor mode sleep N minutes between find runs."
        echo "    -D, --debug"
        echo "                     Enable debug mode to output additional information."
        echo "    -h               Show this help message and exit."
        echo "     [-l|--log_dir LOG_DIRECTORY]"
        echo "              Specify the log directory (default: /var/log)"
    fi
}
# Default values
threshold=600
d_flag=false
sleep=1
time=60
find_args=(-xdev -type f -printf "%p|%T@|%A@\\n")
log_dir="/var/log"
loop_arg_cnt="1"

# Log and evaluate function
log_and_eval() {
    local cmd=$1
    local log_tag=$2

    # Log the command
    echo "Executing command: $cmd" | logger -t "$log_tag"
    # Execute the command and log its output
    eval "$cmd"
}


# Array of commands
command_array=("find" "tar" "ps" "vmstat")
typeset -A cmd_paths

for cmd in "${command_array[@]}"; do
    cmd_path=$(which "$cmd" 2>/dev/null)
    if [[ -n "$cmd_path" ]]; then
        cmd_paths["$cmd"]="$cmd_path"
        log_and_eval "${cmd_paths["$cmd"]} --version" "Bloated_file_stats_commands"
    else
        print "Command not found: $cmd"
        exit 1
    fi
done

zparseopts -E -l:t:=threshold -d:=directories -m:=loop_arg_cnt -s:=sleep -D=debug_mode -h=show_help
if [[ -z "$directories" ]]; then
    echo "Error: -d argument is mandatory."
    exit 1
fi

if [[ -n "$show_help" ]]; then
    usage
    exit 0
fi

# Define the sort_u function
sort_u() {
    local outfile=$1
    echo "Sorting and deduplicating output..."
    local temp_file
    temp_file=$(mktemp)
    log_and_eval "nice ${cmd_paths[sort]} -u <${outfile} > ${temp_file}" "BloatedStats_cmd_sort"
    cp "${temp_file}" "${outfile}"
    echo "Output sorted and deduplicated."
}

# Function to execute the find command

monitor=on
if [[ ! "$sleep" =~ ^[0-9]+$ ]] || (( sleep < 10 )) || (( sleep > 200 )); then
    usage "Sleep duration must be an integer between 10 and 200."
    exit 1
fi
# Array of directories
dir_array=("$log_dir" "/etc" "/tmp")

# Get valid directories
for dir in "${dir_array[@]}"; do
    if [[ -d "$dir" ]]; then
        log_and_eval "type $dir" "Bloated_file_stats_commands"
    else
        print "Directory not found: $dir"
        exit 1
    fi
done

shift $((OPTIND - 1))

# Debug mode check
if [ "$debug_mode" = "on" ]; then
    set -x # Enable shell debugging
fi

if [ "$d_flag" = false ]; then
    echo "Error: -d argument is mandatory."
    exit 1
fi

outfilebase="${log_dir}/${host}-FileAccessDates"
outfile="${outfilebase}.csv"
echo "Threshold: $threshold"
echo "Directories: $directories"

# Define the find command arguments
echo "$loop_arg_cnt requested"
sort_u() {
    outfile=$1
    echo "Sorting and deduplicating output..."
    temp_file=$(mktemp)
    log_and_eval "nice ${cmd_paths['sort']} -u \<${outfile} \> ${temp_file}" "BloatedStats_cmd_sort"
    cp "${temp_file}" "${outfile}"
    echo "Output sorted and deduplicated."
}

# Function to execute the find command
Bloated_file_stats() {
    echo "Executing find and ps command..."
    log_and_eval "${cmd_paths[ps] ax" "BloatedStats_cmd_processes"
    find="nice ${cmd_paths['find'] ${directories} ${find_args} 2\>${outfile}.err 1\>\>${outfile}"
    if [[ ! -e "${outfile}" ]]; then
        echo "AAAAFile|0Modification|Access,V0.5" > "${outfile}"
    fi
    (sleep 1; head -n 5 "${outfile}" ) &
   log_and_eval "$find" "BloatedStats_cmd_find"
   echo "First 5 lines of output (if available):"
   sort_u "$outfile"
   if [[ -z $monitor ]]; then
       c_loops=-1
   else
       # Initialize c_loops based on loop_arg_cnt
       c_loops=$((loop_arg_cnt == 0 ? 1 : loop_arg_cnt))
   fi

   echo "ENTERING Monitor mode ..."

   while [ "$c_loops" -ge 0 ]; do
       echo "Loop count down: c_loops=$c_loops, loop_arg_cnt=$loop_arg_cnt"
       log_and_eval "$find" "BloatedStats_find_cmd"
       echo "Find command executed, process ID: $!"

       echo "Sleeping for $sleep minutes..."
       sleep $(($sleep * $time))
       sort_u "$outfile"
       if [ "$loop_arg_cnt" -gt 0 ]; then
           ((c_loops -= 1))
       fi
       echo "$loop_arg_cnt remaining"
   done
}

# Trap SIGHUP signal and restart find
trap Bloated_file_stats SIGHUP

# Start the find process
Bloated_file_stats

# Collecting system stats
vmstat_cmd="vmstat"
vmstat_interval=60
log_and_eval "${vmstat_cmd} $vmstat_interval" "BloatedStats_vmstat"

# Tar command
tar_args="-C /etc zcf $log_dir/${host}-etc.tgz ."
log_and_eval "nice ${cmd_paths['tar'] ${tar_args}" "BloatedStats_tar"
