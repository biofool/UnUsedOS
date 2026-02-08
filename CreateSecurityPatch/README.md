# Unable Unattended Patching - Version 0.5 Alpha

This  Shell script automates the deployment of unattended-upgrades in your development
environment. It includes automated fetching and updating of unattended upgrades, and additionally generates logs of all
upgrades applied within the last 7 days.

> Note: This script does not need to be deployed to a production environment. It is designed to live solely on the patch
> generator.

## Installation

What the script does for you
1. Install `unattended-upgrades` package:
    ```Shell Script
    sudo apt-get install unattended-upgrades
    ```

2. Configure `unattended-upgrades` package (Interactive just type yes):
    ```Shell Script
    sudo dpkg-reconfigure unattended-upgrades
    ```
   ```Text
3. ```
   SELECT CANCEL and then NO on the following text input screens

                                     ┌────┤ Daemons using outdated libraries ├─────┐
                                     │                                             │ 
                                     │                                             │ 
                                     │ Which services should be restarted?         │ 
                                     │                                             │ 
                                     │    [*] cron.service                         │ 
                                     │    [ ] dbus.service                         │ 
                                     │    [ ] getty@tty1.service                   │ 
                                     │    [ ] networkd-dispatcher.service          │ 
                                     │    [*] packagekit.service                   │ 
                                     │    [*] polkit.service                       │ 
                                     │    [ ] systemd-logind.service               │ 
                                     │    [*] systemd-manager                      │ 
                                     │    [*] udisks2.service                      │ 
                                     │    [ ] user@1000.service                    │ 
                                     │                                             │ 
                                     │                                             │ 
                                     │          <Ok>              <Cancel>         │ 
                                     │                                             │ 
                                     └─────────────────────────────────────────────┘       
   
   
      ┌────────────────────────────────────────┤ Configuring unattended-upgrades ├─────────────────────────────────────────┐
      │                                                                                                                    │ 
      │ Applying updates on a frequent basis is an important part of keeping systems secure. By default, updates need to   │ 
      │ be applied manually using package management tools. Alternatively, you can choose to have this system              │ 
      │ automatically download and install important updates.                                                              │ 
      │                                                                                                                    │ 
      │ Automatically download and install stable updates?                                                                 │ 
      │                                                                                                                    │ 
      │                                  <Yes>                                     <No>                                    │ 
      │                                                                                                                    │ 
      └────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘ 
                                                                                                                         






3. Download only the packages which are upgradable:
   ```Shell Script
    sudo unattended-upgrade --download-only
    ```

## Output Logs

The script generates logs for all the updates made in the last 7 days and stores them in a file. The name of this
logfile will be formed using the hostname of the machine and the current date, and it will be stored in /var/log/vems/.
You can view these logs using the following code:
