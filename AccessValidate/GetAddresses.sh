#!/bin/bash

# Function to get broadcast address for a network interface
get_broadcast_address() {
    interface="$1"
    ip -o -f inet addr show dev "$interface" | awk '/inet /{print $6}'
}

# Function to count ARP table entries
count_arptable_entries() {
    arp -a | wc -l
}

# Get a list of all network interfaces (excluding loopback)
interfaces=$(ip -o link show | awk -F': ' '{print $2}' | grep -v 'lo')

# Get the initial ARP table entry count
initial_count=$(count_arptable_entries)

# Iterate through each interface and get its broadcast address
for iface in $interfaces; do
    broadcast=$(get_broadcast_address "$iface")
    echo "Broadcast address for $iface: $broadcast"
    ping -b -c 5 -I "$iface" "$broadcast"
done

# Get the ARP table entry count after the ping
after_ping_count=$(count_arptable_entries)

# Calculate the difference
difference=$((after_ping_count - initial_count))

echo "Initial ARP table entry count: $initial_count"
echo "ARP table entry count after ping: $after_ping_count"
echo "Difference in entries: $difference"
