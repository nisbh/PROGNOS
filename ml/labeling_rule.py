import datetime
from typing import List, Tuple

# Define the risk horizon windows (in seconds)
IMMINENT_WINDOW = 30
NEAR_TERM_WINDOW = 120  # 2 minutes
ELEVATED_WINDOW = 300   # 5 minutes

class AttackLabeler:
    def __init__(self, attack_windows: List[Tuple[datetime.datetime, datetime.datetime]]):
        """
        Initializes the labeler with known attack windows.
        
        :param attack_windows: A list of tuples containing (start_time, end_time) of known attacks.
                               These will be extracted from the CIC-IDS2018 CSVs.
        """
        # Sort windows by start time to optimize searching if needed
        self.attack_windows = sorted(attack_windows, key=lambda x: x[0])

    def get_label_for_window(self, window_end_time: datetime.datetime) -> str:
        """
        Determines the label for a 10-second traffic window based on how close it is to an attack.
        
        :param window_end_time: The timestamp at the end of the 10-second window.
        :return: One of 'IMMINENT', 'NEAR-TERM', 'ELEVATED', or 'NORMAL'
        """
        min_time_to_attack = float('inf')

        for attack_start, attack_end in self.attack_windows:
            # If the window is during the attack, we can label it IMMINENT or simply ignore/drop it 
            # depending on whether we only want strictly pre-attack forecasting.
            # Assuming we label in-progress attacks as IMMINENT as well:
            if attack_start <= window_end_time <= attack_end:
                return "IMMINENT"

            # Calculate time until this specific attack starts
            time_to_attack = (attack_start - window_end_time).total_seconds()

            # If the attack is in the future, check if it's the closest one we've found
            if time_to_attack > 0 and time_to_attack < min_time_to_attack:
                min_time_to_attack = time_to_attack

        # Apply the labeling recipe based on the closest future attack
        if min_time_to_attack <= IMMINENT_WINDOW:
            return "IMMINENT"
        elif min_time_to_attack <= NEAR_TERM_WINDOW:
            return "NEAR-TERM"
        elif min_time_to_attack <= ELEVATED_WINDOW:
            return "ELEVATED"
        else:
            return "NORMAL"

# Exact start/end timestamps for GoldenEye & Slowloris 
# extracted from Wednesday-workingHours.pcap_ISCX.csv

goldeneye_start = datetime.datetime(2017, 7, 5, 11, 10, 0)
goldeneye_end = datetime.datetime(2017, 7, 5, 11, 19, 0)

slowloris_start = datetime.datetime(2017, 7, 5, 2, 24, 0)
slowloris_end = datetime.datetime(2017, 7, 5, 10, 11, 0)

# --- Example Usage for Wednesday-05-07-2017 (CIC-IDS2017) ---
if __name__ == "__main__":
    labeler = AttackLabeler(attack_windows=[
        (goldeneye_start, goldeneye_end),
        (slowloris_start, slowloris_end)
    ])

    # Test the labeler
    test_time = goldeneye_start - datetime.timedelta(seconds=15)
    print(f"15 seconds before attack: {labeler.get_label_for_window(test_time)}") # Expected: IMMINENT
    
    test_time = goldeneye_start - datetime.timedelta(seconds=90)
    print(f"90 seconds before attack: {labeler.get_label_for_window(test_time)}") # Expected: NEAR-TERM
    
    test_time = goldeneye_start - datetime.timedelta(seconds=240)
    print(f"4 minutes before attack: {labeler.get_label_for_window(test_time)}") # Expected: ELEVATED
    
    test_time = goldeneye_start - datetime.timedelta(minutes=10)
    print(f"10 minutes before attack: {labeler.get_label_for_window(test_time)}") # Expected: NORMAL
