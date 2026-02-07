Two applicationns

# Memory  and system utilizations Analysis
## First install using [installVMCollector.sh](installVMCollector.sh)
This will collect VMStat info into syslog file.
Once ou have enough data run the syslog file through the standalone python script.
[VMStatsDisplay/ExtractVEMSStats.py](VMStatsDisplay%2FExtractVEMSStats.py)
This script will extract all of the VEMSStat records from the inpout file and stage them for the various graphing/analysis applications.

To see a system overview run  [vmstat_dashboard.py](VMStatsDisplay%2Fvmstat_dashboard.py).  This will create .png files of the plots and display them for browsing if you are running a gui.


# File Access and Modification Analysis


## Overview

This program uses `find` to examine a directory tree or filesystem: for the last time a file was accessed or changed. It
also determines whether either of these events has happened since the file was created. This analysis is designed for
Ubuntu versions 20 and later.
It stores the last modification time and whether the file was access more than threshold seconds after it was modified

    This Application WhatsUnused.sh is in alpha the installer is still in alpha test"

## Usage

To use this [VEMSFileUsageStats.sh](VEMSFileUsageStats.sh), provide a path to the directory or filesystem you want to analyze.

		Usage: $0 [OPTIONS]"
		  OPTIONS:"
		    -t, --threshold SECONDS"
		                     Set the time threshold in SECONDS (default: 600)."
		    -d, --directories DIRS"
		                     Specify a colon-separated list of directories to search."
		                     (default: all mounted ext4 file systems)."
		    -u, --unused_window SECONDS"
		                     Set the time window in days during which a file must not"
		                     have been modified or read to be considered unused (default: 30)."
		    -m, --monitor"
		                     Run in monitor loops with sort -u & sleep minutes between loops."
								    no -m run once"
				    				      -m=n>0 (monitor for N+1 iteration)"
		    						      -m=0 infinte loop"
		    -s, --sleep"
		                     In monitor mode sleep N minutes between find runs."
		    -D, --debug"
		                     Enable debug mode to output additional information."
		                     Debug also shortens the sleep time to 6 seconds"
		    -h       Show this help message and exit."
		"

# Find Command Output Explanation

This script uses the `find` command to locate files in a specified directory tree that have not been accessed or
modified within a certain time frame.
Line 2 of the file is a version string that hasn't been tested with csv readers
./collector2.sh,0,0,v1, ../.. /tmp,-xdev -type f ( -mtime +30 -o -atime +30 ) -printf
%p,%T@,%A@\n../../aws_security_incident_response.docx,1677433493.066,1677433519.457,ish+-:26.392

Outputs are:
#Unused.csv:
Files that have neither been modified nor accessed in the
#Unused.err:
##All the errors find encountered which should be 0 for a privileges user

