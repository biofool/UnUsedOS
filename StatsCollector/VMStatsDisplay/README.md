Reads the output of vmstat and creates a set of graphs allowing you to view the stats organized by area.
This array (excerpted from the code)
Defines the grouping and the legend.

VMStatdisplay is a sub folder of VStatsCollector which installs a stats collector that runs at boot time and records the necessary stats in syslog.

    'procs': {'r': 'Processes waiting for runtime', 'b': 'Processes in uninterruptible sleep'},
    'memory': {'swpd': 'Virtual memory used', 'free': 'Idle memory', 'buff': 'Memory used as buffers',
               'cache': 'Memory used as cache'},
    'swap': {'si': 'Memory swapped in from disk', 'so': 'Memory swapped to disk'},
    'io': {'bi': 'Blocks received from block device', 'bo': 'Blocks sent to block device'},
    'system': {'in': 'Interrupts per second', 'cs': 'Context switches per second'},
    'cpu': {'us': 'CPU time for user code', 'sy': 'CPU time for kernel code', 'wa': 'CPU idle with disk I/O request',
            'st': 'Stolen CPU time'},
    'idle': {'id': 'CPU idle with no disk I/O request'}


Sample plot

    gunzip Smns-DV-lsk-Lbrry-pk-cln_VEMSStatVM.log.gz
    vmstat_dashboard.py -i Smns-DV-lsk-Lbrry-pk-cln_VEMSStatVM.log
    [Smns-DV-lsk-Lbrry-pk-cln_VEMSStatVM_plots.pdf
gunzip [Smns-DV-lsk-Lbrry-pk-cln_VEMSStatVM.log.gz](Smns-DV-lsk-Lbrry-pk-cln_VEMSStatVM.log.gz)
[vmstat_dashboard.py](vmstat_dashboard.py) -i [Smns-DV-lsk-Lbrry-pk-cln_VEMSStatVM.log](Smns-DV-lsk-Lbrry-pk-cln_VEMSStatVM.log)
[Smns-DV-lsk-Lbrry-pk-cln_VEMSStatVM_plots.pdf](Smns-DV-lsk-Lbrry-pk-cln_VEMSStatVM_plots.pdf)
