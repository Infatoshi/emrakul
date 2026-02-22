#!/bin/bash
# Capture cursor-agent traffic

# Start tcpdump in background
sudo tcpdump -i en0 -w /tmp/cursor_traffic.pcap 'host api2.cursor.sh' &
TCPDUMP_PID=$!

sleep 1

# Make a cursor request
echo "Making cursor request..."
cursor-agent --print --model gpt-5.2 "Say hello"

sleep 1

# Stop tcpdump
sudo kill $TCPDUMP_PID

echo "Captured traffic saved to /tmp/cursor_traffic.pcap"
