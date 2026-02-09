# File Access and Modification Analysis

## Overview

This program uses `find` to examine a directory tree or filesystem: for the last time a file was accessed or changed. It
also determines whether either of these events has happened since the file was created. This analysis is designed for
Ubuntu versions 20 and later.
It stores the last modification time and whether the file was access more than threshold seconds after it was modified

    This Application WhatsUnused.sh is in beta the installer is still in alpha test"

## Data Collection

If this is the first time you are using the BloatedStatsCollector

I recommend you manually run the following commands

    sudo mkdir /var/log/bloated/find
    sudo chown fc /var/log/bloated/find
    nice /usr/bin/find / -xdev -type f -printf "%p|%T@|%A@\\n" >/var/log/bloated/find/FileAccessDates.log 2>/var/log/bloated/find/FileAccessDates.csv.err &
    nohup bash -c 'vmstat 60 | logger -t BloatedStatVM' &
    wait

Once you get a command prompt back you can download the Bloated configuration and email me the box location once it's
uploaded
This will not install the collector which means it will stop running at the next reboot

Eventually we will be installing some version of the collector
