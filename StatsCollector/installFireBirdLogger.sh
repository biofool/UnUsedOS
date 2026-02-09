#! /bin/bash
log_conf="/log_conf"
log_dir="/var/log/bloated"
# bin_dir="/usr/local/bin"
# Trace configuration example
cat>$log_dir/$log_conf<<EOF
database=* {
    enabled = true
    time_threshold = 0
    log_connections = true
    log_transactions = true
    log_statement_prepare = true
    log_statement_free = true
    log_statement_start = true
    log_statement_finish = true
    log_procedure_start = true
    log_procedure_finish = true
    log_trigger_start = true
    log_trigger_finish = true
    log_context = true
    print_plan = true
    print_perf = true
}
EOF
fbtracemgr -start -config your_trace_config_file.conf -user sysdba -password your_password
