# Function to collect metrics from an ESXi host
function Collect-ESXiMetrics {
    param (
        [VMware.VimAutomation.ViCore.Types.V1.Inventory.VMHost]$vmHost,
        [string]$metricsFilePath
    )

    $metrics = Get-Content -Path $metricsFilePath
    $collectedMetrics = @{}

    foreach ($metric in $metrics) {
        if ($metric -and -not $collectedMetrics.ContainsKey($metric)) {
            try {
                $metricData = Get-Stat -Entity $vmHost -Stat $metric -MaxSamples 1 -ErrorAction Stop | Select-Object -ExpandProperty Value
                $collectedMetrics[$metric] = $metricData
            } catch {
                Write-Warning "Failed to collect metric '$metric' for host $($vmHost.Name): $_"
            }
        }
    }

    return $collectedMetrics
}
function ZabbixSender {
    param (
        [string]$zabbixServer,
        [string]$hostName,
        [string]$metricKey,
        [string]$metricValue
    )

    # Format the data as if it came from syslog on the ESXi server
    # Note: Adjust the format as per your syslog standards
    $syslogMessage = "host=$hostName key=$metricKey value=$metricValue"

    # Use logger to log the message with the tag as the ESXi host name
    logger -t $hostName $syslogMessage

    # The following line is a placeholder for sending data to Zabbix
    # You need to replace this with actual code or command to send data to Zabbix
    Write-Host "Sending to Zabbix: $syslogMessage"
}

function Send-ToZabbix {
    param (
        [string]$zabbixServer,
        [string]$hostName,
        [hashtable]$data
    )

    foreach ($entry in $data.GetEnumerator()) {
        # Format the data for Zabbix. Adjust according to your Zabbix setup
        $formattedData = "$($entry.Key) $($entry.Value)"

        # Send the data to Zabbix. Replace with the actual command or method for sending to your Zabbix server
        ZabbixSender -z $zabbixServer -s $hostName -k $entry.Key -o $entry.Value
    }
}
# Main Script
$vcenter = "vcsa.corp.vigilent.com"
$username = "administrator@vsphere.local"
$plainPassword = $env:ESXI_PASSWORD
$securePassword = ConvertTo-SecureString -String $plainPassword -AsPlainText -Force
Set-PowerCLIConfiguration -Scope User -ParticipateInCEIP $false.
Set-PowerCLIConfiguration -InvalidCertificateAction Ignore -Confirm:$false
$credential = New-Object System.Management.Automation.PSCredential ($username, $securePassword)
Connect-VIServer -Server $vcenter -Credential $credential

$vmHosts = Get-VMHost
$vmHosts_metric_files = $args

foreach ($vmHost in $vmHosts)
{
    # Construct expected metrics file name based on VMHost name
    $expectedFileName = "$( $vmHost.Name )_metrics_config.txt"

    # Find the matching file in the provided list
    $matchingFile = $vmHosts_metric_files | Where-Object { $_ -match [regex]::Escape($expectedFileName) }

    if (-not$matchingFile)
    {
        Write-Host "No metrics file found for VMHost: $( $vmHost.Name )"
        continue
    }

    if (-not(Test-Path $matchingFile))
    {
        Write-Host "File not found: $matchingFile"
        continue
    }

    # Collect metrics for the VMHost
    $collectedData = Collect-ESXiMetrics -vmHost $vmHost -metricsFilePath $matchingFile

    # Process the collected data
    Write-Host "Collected metrics for VMHost: $( $vmHost.Name )"
    $collectedData = Collect-ESXiMetrics -vmHost $vmHost -metricsFilePath $matchingFile

    # Process the collected data
    Write-Host "Collected metrics for VMHost: $( $vmHost.Name )"
    foreach ($entry in $collectedData.GetEnumerator())
    {
        Write-Host "Key: $( $entry.Key ), Value: $( $entry.Value )"
    }
    Send-ToZabbix -zabbixServer $zabbixServer -hostName $vmHost.Name -data $collectedData

}

Disconnect-VIServer -Server $vcenter -Confirm:$false
