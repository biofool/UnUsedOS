# Connect to the vCenter Server
$vcenter = "vcsa.corp.vigilent.com"
$username = "administrator@vsphere.local"
$plainPassword = $env:ESXI_PASSWORD

# Convert plain password to SecureString
$securePassword = ConvertTo-SecureString -String $plainPassword -AsPlainText -Force

Set-PowerCLIConfiguration -InvalidCertificateAction Ignore -Confirm:$false
$credential = New-Object System.Management.Automation.PSCredential ($username, $securePassword)
Connect-VIServer -Server $vcenter -Credential $credential

# Retrieve all ESXi Hosts managed by the vCenter Server
$vmHosts = Get-VMHost

function Get-ESXiPerformanceMetrics {
    param (
        [VMware.VimAutomation.ViCore.Types.V1.Inventory.VMHost]$vmHost,
        [System.Security.SecureString]$securePassword
    )

    # Get metrics for the given VMHost
    $metrics = Get-StatType -Entity $vmHost

    # Write metrics to a configuration file
    $metrics | Out-File -FilePath "$($vmHost.Name)_metrics_config.txt"

    return $metrics
}

foreach ($vmHost in $vmHosts) {
    try {
        Get-ESXiPerformanceMetrics -vmHost $vmHost -securePassword $securePassword
    } catch {
        Write-Host "Error retrieving metrics for host: $($vmHost.Name)"
        Write-Host $_.Exception.Message
    }
}

# Disconnect from the vCenter Server
Disconnect-VIServer -Server $vcenter -Confirm:$false
