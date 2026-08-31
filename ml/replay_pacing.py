import time
import datetime
from scapy.all import PcapReader
from ml.feature_extractor import process_packet  # To be implemented by Nilesh

def replay_pcap(pcap_path: str, speed_multiplier: float = 1.0):
    """
    Replays a PCAP file, maintaining the original timing between packets,
    and feeds them into the feature extractor.
    
    :param pcap_path: Path to the PCAP file.
    :param speed_multiplier: >1.0 for faster replay, <1.0 for slower.
    """
    print(f"Starting replay of {pcap_path} at {speed_multiplier}x speed...")
    
    first_packet = True
    last_pcap_time = None
    last_real_time = None
    
    try:
        with PcapReader(pcap_path) as pcap_reader:
            for packet in pcap_reader:
                # Scapy packet times are usually in seconds (Unix epoch float)
                current_pcap_time = float(packet.time)
                current_real_time = time.time()
                
                if first_packet:
                    last_pcap_time = current_pcap_time
                    last_real_time = current_real_time
                    first_packet = False
                else:
                    # Calculate how much time passed in the PCAP vs real life
                    pcap_delta = current_pcap_time - last_pcap_time
                    
                    if pcap_delta > 0:
                        # Wait until it's time to send this packet
                        target_real_time = last_real_time + (pcap_delta / speed_multiplier)
                        sleep_duration = target_real_time - current_real_time
                        
                        if sleep_duration > 0:
                            time.sleep(sleep_duration)
                    
                    last_pcap_time = current_pcap_time
                    last_real_time = time.time()
                
                # Pass the packet to Nilesh's feature extractor
                try:
                    # process_packet is responsible for accumulating stats into the 10-second windows
                    process_packet(packet)
                except Exception as e:
                    print(f"Error processing packet: {e}")
                    
    except FileNotFoundError:
        print(f"Error: Could not find PCAP file at {pcap_path}")
        
    print("Replay finished.")

if __name__ == "__main__":
    # Example usage (Nisarg to update path when ready for Block F)
    # replay_pcap("path/to/Thursday-15-02-2018_TrafficForML_CICFlowMeter.pcap", speed_multiplier=1.0)
    print("Replay pacing harness ready.")
