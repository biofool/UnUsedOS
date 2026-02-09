# Function to collect ESXi metrics
Set-PowerCLIConfiguration -InvalidCertificateAction Ignore -Confirm:$false
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

# Function to read VMHost metrics
function Read-VMHostMetrics {
    param (
        [VMware.VimAutomation.ViCore.Types.V1.Inventory.VMHost]$vmHost,
        [string[]]$vmHostMetricsFiles
    )

    if ($vmHostMetricsFiles.Length -eq 0) {
        Write-Host "Usage: Read-VMHostMetrics <file1> <file2> ..."
        exit
    }

    foreach ($file in $vmHostMetricsFiles) {
        if (-not (Test-Path $file)) {
            Write-Host "File not found: $file"
            continue
        }

        $vmHostName = [System.IO.Path]::GetFileNameWithoutExtension($file) -replace "_metrics_config", ""
        $metrics = Get-Content -Path $file
        Write-Host "Processing metrics for VMHost: $vmHostName"
        foreach ($metric in $metrics) {
            Write-Host "`tMetric: $metric"
        }
    }
}

# Main Script
$vcenter = "vcsa.corp.vigilent.com"
$username = "administrator@vsphere.local"
$plainPassword = $env:ESXI_PASSWORD
$securePassword = ConvertTo-SecureString -String $plainPassword -AsPlainText -Force

Set-PowerCLIConfiguration -InvalidCertificateAction Ignore -Confirm:$false
$credential = New-Object System.Management.Automation.PSCredential ($username, $securePassword)
Connect-VIServer -Server $vcenter -Credential $credential
# Retrieve all ESXi Hosts managed by the vCenter Server
$vmHosts = Get-VMHost
$vmHosts_metric_files = $args
Read-VMHostMetrics -vmHostMetricsFiles $vmHosts_metric_files

Disconnect-VIServer -Server $vcenter -Confirm:$false
