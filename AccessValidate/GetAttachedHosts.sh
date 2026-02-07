#!/bin/bash
namp(){
  # Use nmap to confirm hosts on the network using the CIDRs
nmap_results=$(mktemp)
for cidr in "${cidrs[@]}"; do
    echo "Scanning CIDR: $cidr"
    nmap -T3 -sn "$cidr" | awk '/for /{print $NF}' >> "$nmap_results"
done
}
# Get a list of all network interfaces (excluding loopback)
interfaces=$(ip -o link show | awk -F': ' '{print $2}' | grep -v 'lo')

# Initialize an empty array to store CIDRs
cidrs=()

# Loop through each interface and get its CIDR
for iface in $interfaces; do
    cidr=$(ip -o -f inet addr show dev "$iface" | awk '{print $4}')
    cidrs+=("$cidr")
done

# Print the list of CIDRs
echo "List of CIDRs:"
for cidr in "${cidrs[@]}"; do
    echo "$cidr"
done

# Use arp -a to display the ARP table
arp -a | awk '{print $2}' | tr -d '()' > arp_ips.txt


# Extract IP addresses from arp and nmap results
known_hosts_arpreport=$(arp -a | awk '{print $2}' | tr -d '()')
known_hosts_nmapreport=$(awk '/for /{print $NF}' "$nmap_results")

# Combine and deduplicate IP addresses
known_hosts_all=$(echo -e "$known_hosts_arpreport\n$known_hosts_nmapreport" | sort -u)

# Report differences
echo "Differences between arp and nmap results:"
comm -3 <(echo "$known_hosts_arpreport" | sort) <(echo "$known_hosts_nmapreport" | sort)

# Create knownhosts.txt file
known_hosts_file="knownhosts.txt"
echo "$known_hosts_all" > "$known_hosts_file"
echo "Known hosts written to $known_hosts_file."

# Clean up nmap_results temporary file
rm "$nmap_results"
