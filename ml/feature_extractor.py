import csv
import os
import datetime
from scapy.all import TCP, IP
from ml.labeling_rule import AttackLabeler, goldeneye_start, goldeneye_end, slowloris_start, slowloris_end

class FeatureExtractor:
    def __init__(self, output_csv: str, window_size_sec: int = 10):
        self.output_csv = output_csv
        self.window_size_sec = window_size_sec
        
        # We use the labeler you just built!
        self.labeler = AttackLabeler([
            (goldeneye_start, goldeneye_end),
            (slowloris_start, slowloris_end)
        ])
        
        # State for the current window
        self.current_window_start_time = None
        self.packet_count = 0
        self.syn_count = 0
        self.total_packet_size = 0
        self.unique_src_ips = set()
        
        # Initialize CSV
        self._init_csv()

    def _init_csv(self):
        # Create header if file doesn't exist
        if not os.path.exists(self.output_csv):
            os.makedirs(os.path.dirname(self.output_csv), exist_ok=True)
            with open(self.output_csv, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    "timestamp", "connections_per_sec", "syn_rate", 
                    "unique_source_ips", "avg_packet_size", "label"
                ])

    def process_packet(self, packet):
        """Called for every packet in the PCAP stream."""
        if not packet.haslayer(IP):
            return # Skip non-IP packets

        # Scapy packet.time is a float (Unix epoch). Convert to datetime to use with your labeler.
        # Note: Scapy uses local timezone by default, but PCAPs are often UTC or local. 
        # For CIC-IDS2017, the timestamps in the CSV were local AST time. 
        # We will assume packet.time matches the epoch time of the attack.
        pkt_time = datetime.datetime.fromtimestamp(float(packet.time))

        if self.current_window_start_time is None:
            self.current_window_start_time = pkt_time

        # Calculate time difference
        time_diff = (pkt_time - self.current_window_start_time).total_seconds()

        # If we've crossed the 10-second boundary, flush the window!
        if time_diff >= self.window_size_sec:
            self._flush_window(self.current_window_start_time + datetime.timedelta(seconds=self.window_size_sec))
            # Reset state for next window
            self.current_window_start_time = pkt_time
            self.packet_count = 0
            self.syn_count = 0
            self.total_packet_size = 0
            self.unique_src_ips = set()

        # Accumulate stats
        self.packet_count += 1
        self.total_packet_size += len(packet)
        self.unique_src_ips.add(packet[IP].src)

        if packet.haslayer(TCP):
            # Check if SYN flag is set. TCP flags: 0x02 is SYN
            if packet[TCP].flags & 0x02:
                self.syn_count += 1

    def _flush_window(self, window_end_time: datetime.datetime):
        """Calculates features for the past 10 seconds and saves to CSV."""
        if self.packet_count == 0:
            return

        connections_per_sec = self.packet_count / self.window_size_sec
        syn_rate = self.syn_count / self.window_size_sec
        avg_packet_size = self.total_packet_size / self.packet_count
        num_unique_ips = len(self.unique_src_ips)

        # Get the label for this specific moment in time using your logic!
        label = self.labeler.get_label_for_window(window_end_time)

        # Write to CSV
        with open(self.output_csv, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                window_end_time.isoformat(), 
                connections_per_sec, 
                syn_rate, 
                num_unique_ips, 
                avg_packet_size, 
                label
            ])
