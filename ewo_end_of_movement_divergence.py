import csv
from datetime import datetime

class EWOEndofMovementDivergenceDetector:
    def __init__(self, pullback_threshold=0.6):
        """
        Initialize the PatternDetector.

        :param pullback_threshold: The percentage (0-1) representing the desired pullback.
                                   For example, 0.8 means an 80% pullback towards zero from the pivot.
        """
        if not (0 <= pullback_threshold <= 1):
            raise ValueError("pullback_threshold must be between 0 and 1.")
        self.pullback_threshold = pullback_threshold
        self.reset()

    def reset(self):
        """Reset the detector to its initial state."""
        self.state = 'Idle'
        self.current_pivot_height = None
        self.pivot_type = None  # 'LOCAL_MIN' or 'LOCAL_MAX'
        self.pullback_height = None
        self.height_after_pullback = None
        self.required_pullback_height = None  # To store the required pullback height
        self.patterns = []  # To store detected patterns
        self.bars_since_pivot = 0  # Counter for the number of bars since pivot

    def process_event(self, timestamp_str, event_type, height):
        """
        Process an incoming event.

        :param event_type: Type of the event ('LOCAL_MIN', 'LOCAL_MAX', 'HEIGHT')
        :param height: The HEIGHT value associated with the event
        """
        print(f"Processing event: Type={event_type}, Height={height}, Current State={self.state}")
        if event_type == 'HEIGHT':
            self.handle_height(timestamp_str, height)
        elif event_type in ['LOCAL_MIN', 'LOCAL_MAX']:
            self.handle_extrema(timestamp_str, event_type, height)
        else:
            print(f"Unknown event type: {event_type}")
        # Increment bars since pivot if not in 'Idle' state
        if self.state != 'Idle':
            self.bars_since_pivot += 1
            if self.bars_since_pivot > 120:
                print(f"Pattern did not complete within 120 bars. Resetting to Idle.")
                self.reset()

    def handle_extrema(self, timestamp_str, event_type, height):
        log_prefix = f"[{timestamp_str}]"
        print(f"{log_prefix} Handling extrema: Event Type={event_type}, Height={height}, State={self.state}")
        if self.state == 'Idle':
            # Set initial pivot
            self.current_pivot_height = height
            self.pivot_type = event_type
            self.state = 'WaitingPullback'
            self.bars_since_pivot = 0  # Reset counter
            print(f"{log_prefix} Pivot ({event_type}) detected. Recorded pivot height: {height}")
        elif self.state in ['WaitingPullback', 'WaitingIncrease']:
            if event_type == self.pivot_type:
                if self.should_update_pivot(height):
                    # Update pivot to more significant point
                    print(f"{log_prefix} New {event_type} received with more significant height {height}. Pivot updated from {self.current_pivot_height} to {height}")
                    self.current_pivot_height = height
                    self.pullback_height = None
                    self.height_after_pullback = None
                    self.required_pullback_height = None
                    self.bars_since_pivot = 0  # Reset counter
                    self.state = 'WaitingPullback'
                elif self.state == 'WaitingIncrease' and self.height_after_pullback is not None and self.is_pattern_complete(height):
                    # Complete the pattern
                    pattern = {
                        'pivot_type': self.pivot_type,
                        'initial_pivot_height': self.current_pivot_height,
                        'pullback_height': self.pullback_height,
                        'required_pullback_height': self.required_pullback_height,
                        'new_pivot_height': height,
                        'pullback_evaluation': {
                            'actual_pullback_height': self.pullback_height,
                            'required_pullback_height': self.required_pullback_height,
                            'is_pullback_valid': abs(self.pullback_height) <= abs(self.required_pullback_height)
                        }
                    }
                    self.patterns.append(pattern)
                    print(f"{log_prefix} Pattern completed: {pattern}")
                    # Reset for next pattern detection
                    self.reset()
                else:
                    # Do not update pivot; continue waiting
                    print(f"{log_prefix} New {event_type} with height {height} does not replace pivot or complete pattern.")
            else:
                # Opposite pivot type received; reset to Idle
                print(f"{log_prefix} Received opposite pivot ({event_type}) before pattern completion. Resetting to Idle.")
                self.reset()

    def handle_height(self, timestamp_str, height):
        log_prefix = f"[{timestamp_str}]"
        print(f"{log_prefix} Handling height: Height={height}, State={self.state}")
        if self.state == 'WaitingPullback':
            required_pullback_height = self.calculate_required_pullback()
            print(f"{log_prefix} Calculated required pullback height: {required_pullback_height}")
            if self.is_pullback_detected(height, required_pullback_height):
                self.pullback_height = height
                self.required_pullback_height = required_pullback_height
                self.state = 'WaitingIncrease'
                self.bars_since_pivot = 0  # Reset counter
                print(f"{log_prefix} Pullback detected for {self.pivot_type}. Height: {height}, Required: {required_pullback_height}")
            else:
                print(f"{log_prefix} No pullback detected. Current height: {height}, Required pullback: {required_pullback_height}")
        elif self.state == 'WaitingIncrease':
            if self.is_height_moving_in_expected_direction_after_pullback(height):
                self.height_after_pullback = height
                print(f"Height movement detected after {self.pivot_type} pullback. Current height: {height}")
            else:
                print(f"{log_prefix} Height not moving in expected direction. Current height: {height}, Pullback height: {self.pullback_height}")

    def calculate_required_pullback(self):
        """Calculate the required pullback height based on the pivot and threshold."""
        pivot_abs = abs(self.current_pivot_height)
        required_pullback = pivot_abs * (1 - self.pullback_threshold)
        print(f"Calculated pullback requirement: Pivot={self.current_pivot_height}, Threshold={self.pullback_threshold}, Required={required_pullback}")
        return required_pullback

    def should_update_pivot(self, height):
        """Determine if the pivot should be updated based on the new height."""
        print(f"Checking if pivot should be updated: Current Pivot={self.current_pivot_height}, New Height={height}")
        if abs(height) > abs(self.current_pivot_height):
            print(f"Pivot should be updated.")
            return True
        print(f"Pivot should not be updated.")
        return False

    def is_pullback_detected(self, height, required_pullback_height):
        """Check if a pullback is detected based on the pivot type and height."""
        print(f"Checking pullback: Current Height={height}, Required Pullback Height={required_pullback_height}")
        if abs(height) <= required_pullback_height:
            print(f"Pullback detected.")
            return True
        print(f"Pullback not detected.")
        return False

    def is_height_moving_in_expected_direction_after_pullback(self, height):
        """Check if the height is moving in the expected direction after the pullback."""
        print(f"Checking height movement after pullback: Pullback Height={self.pullback_height}, Current Height={height}")
        if self.pivot_type == 'LOCAL_MAX':
            # Expecting height to increase after a pullback from a local max
            if height > self.pullback_height:
                print(f"Height is moving upwards as expected after LOCAL_MAX pullback.")
                return True
        elif self.pivot_type == 'LOCAL_MIN':
            # Expecting height to decrease after a pullback from a local min
            if height < self.pullback_height:
                print(f"Height is moving downwards as expected after LOCAL_MIN pullback.")
                return True
        print(f"Height is not moving in expected direction.")
        return False

    def is_pattern_complete(self, height):
        """Check if the pattern is complete based on the pivot type and new extrema height."""
        print(f"Checking if pattern is complete: Current Pivot Height={self.current_pivot_height}, New Height={height}")
        if self.pivot_type == 'LOCAL_MAX' and height <= self.current_pivot_height:
            print(f"Pattern is complete for LOCAL_MAX.")
            return True
        elif self.pivot_type == 'LOCAL_MIN' and height >= self.current_pivot_height:
            print(f"Pattern is complete for LOCAL_MIN.")
            return True
        print(f"Pattern is not complete.")
        return False

    def get_patterns(self):
        """Return the list of detected patterns."""
        return self.patterns

def parse_bool(value):
    """Helper function to parse boolean strings from CSV."""
    return value.strip().lower() == 'true'

def main():
    detector = EWOEndofMovementDivergenceDetector(pullback_threshold=0.6)  # 80% pullback towards zero

    csv_file_path = 'output/ewo_output.csv'  # Path to the CSV file

    try:
        with open(csv_file_path, mode='r', newline='') as csvfile:
            reader = list(csv.DictReader(csvfile))
            last_200_rows = reader[-200:] if len(reader) > 200 else reader

            for row in last_200_rows:
                timestamp_str = row['Timestamp']
                ewo_value = float(row['EWO_Value'])
                is_max = parse_bool(row['Is_Max'])
                is_min = parse_bool(row['Is_Min'])

                # Determine the event type
                if is_max:
                    event_type = 'LOCAL_MAX'
                elif is_min:
                    event_type = 'LOCAL_MIN'
                else:
                    event_type = 'HEIGHT'

                # Optionally, parse the timestamp if needed
                # timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")

                # Process the event
                detector.process_event(timestamp_str, event_type, ewo_value)

        # After processing all events, print the detected patterns
        print("\nDetected Patterns:")
        for idx, pattern in enumerate(detector.get_patterns(), start=1):
            print(f"Pattern {idx}:")
            print(f"  Pivot Type: {pattern['pivot_type']}")
            print(f"  Initial Pivot Height: {pattern['initial_pivot_height']}")
            print(f"  Required Pullback Height: {pattern['required_pullback_height']}")
            print(f"  Pullback Height: {pattern['pullback_height']}")
            print(f"  Pullback Evaluation:")
            print(f"    Actual Pullback Height: {pattern['pullback_evaluation']['actual_pullback_height']}")
            print(f"    Required Pullback Height: {pattern['pullback_evaluation']['required_pullback_height']}")
            print(f"    Is Pullback Valid: {pattern['pullback_evaluation']['is_pullback_valid']}")
            print(f"  New Pivot Height: {pattern['new_pivot_height']}\n")

    except FileNotFoundError:
        print(f"Error: The file {csv_file_path} does not exist.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
