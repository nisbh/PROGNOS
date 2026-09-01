import time
import datetime
import sys
from scapy.all import PcapReader
from ml.feature_extractor import FeatureExtractor

def replay_pcap(pcap_path: str, speed_multiplier: float = 1.0, output_csv: str = "data/training_features.csv", live_mode: bool = True):
    """
    Replays a PCAP file, optionally maintaining the original timing between packets,
    and feeds them into the feature extractor.
    
    :param pcap_path: Path to the PCAP file.
    :param speed_multiplier: >1.0 for faster replay, <1.0 for slower.
    :param live_mode: If False, skips all sleeping (blasts through PCAP as fast as possible for training).
    """
    print(f"Starting replay of {pcap_path}")
    print(f"Live mode: {live_mode}, Speed: {speed_multiplier}x")
    
    extractor = FeatureExtractor(output_csv=output_csv)
    
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
                    
                    if pcap_delta > 0 and live_mode:
                        # Wait until it's time to send this packet
                        target_real_time = last_real_time + (pcap_delta / speed_multiplier)
                        sleep_duration = target_real_time - current_real_time
                        
                        if sleep_duration > 0:
                            time.sleep(sleep_duration)
                    
                    last_pcap_time = current_pcap_time
                    last_real_time = time.time()
                
                # Pass the packet to the feature extractor
                try:
                    extractor.process_packet(packet)
                except Exception as e:
                    print(f"Error processing packet: {e}")
                    
    except FileNotFoundError:
        print(f"Error: Could not find PCAP file at {pcap_path}")
        
    print("Replay finished.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m ml.replay_pacing <path_to_pcap>")
        print("Example: python -m ml.replay_pacing data/Wednesday-workingHours.pcap")
        sys.exit(1)
        
    pcap_file = sys.argv[1]
    replay_pcap(pcap_file, live_mode=False)
