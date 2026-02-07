# Connect to the ESXi Host
# Define vCenter Server details
$vcenter = "vcsa.corp.vigilent.com" # Replace with your vCenter Server host name or IP address
$username = "administrator@vsphere.local" # Replace with your vCenter Server username
$password = "yourpassword" # Replace with your vCenter Server password

Set-PowerCLIConfiguration -InvalidCertificateAction Ignore -Confirm:$false
Connect-VIServer -Server $vcenter -User $username -Password $password

Set-PowerCLIConfiguration -InvalidCertificateAction Ignore -Confirm:$false

# SNMP Settings
$snmpCommunity = "vigilent_fcllc" # Replace with your desired community string
$snmpTarget = "10.3.1.1" # Replace with your Zabbix server IP address
Connect-VIServer -Server $vcenter -User $username -Password $password

# Retrieve all ESXi Hosts managed by the vCenter Server
$vmHosts = Get-VMHost
$snmpLogLevel = "info" # Set the log level (debug, info, warning, error)

# Retrieve all ESXi Hosts managed by the vCenter Server

foreach ($vmHost in $vmHosts) {
    Write-Host "Configuring SNMP settings on host: $($vmHost.Name)"

    try {
        $esxcli = Get-EsxCli -VMHost $vmHost

        if ($null -eq $esxcli) {
            throw "Unable to get ESXCLI for host: $($vmHost.Name)"
        }

        # Configure SNMP settings using ESXCLI V1 syntax with loglevel
        $esxcli.system.snmp.set($null, $null, $null, $null, $null, $null, $snmpCommunity, $null, $null, $null, $null, $true, $null, $null, $snmpLogLevel, $null)
        $esxcli.system.snmp.add($null, $null, $null, "$snmpTarget@162 $snmpCommunity", $null)

        # Restart SNMP Service to Apply Changes
        $esxcli.system.snmp.restart($null)
    } catch {
        Write-Host "Error configuring SNMP on host: $($vmHost.Name)"
        Write-Host $_.Exception.Message
    }
}


# Disconnect from the vCenter Server...

# Disconnect from the vCenter Server
Disconnect-VIServer -Server $vcenter -Confirm:$false
