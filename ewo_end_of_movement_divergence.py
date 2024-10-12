class EWOEndofMovementDivergenceDetector:
    def __init__(self, pullback_threshold=0.8):
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
        self.patterns = []  # To store detected patterns

    def process_event(self, event_type, height):
        """
        Process an incoming event.

        :param event_type: Type of the event ('LOCAL_MIN', 'LOCAL_MAX', 'HEIGHT')
        :param height: The HEIGHT value associated with the event
        """
        if event_type == 'HEIGHT':
            self.handle_height(height)
        elif event_type in ['LOCAL_MIN', 'LOCAL_MAX']:
            self.handle_extrema(event_type, height)
        else:
            print(f"Unknown event type: {event_type}")

    def handle_extrema(self, event_type, height):
        if self.state == 'Idle':
            # Set initial pivot
            self.current_pivot_height = height
            self.pivot_type = event_type
            self.state = 'WaitingPullback'
            print(f"Pivot ({event_type}) detected. Recorded pivot height: {height}")
        elif self.state in ['WaitingPullback', 'WaitingIncrease']:
            if event_type == self.pivot_type:
                if self.should_update_pivot(height):
                    # Update pivot to more significant point
                    print(f"New {event_type} received with more significant height {height}. Pivot updated from {self.current_pivot_height} to {height}")
                    self.current_pivot_height = height
                    self.pullback_height = None
                    self.height_after_pullback = None
                    self.state = 'WaitingPullback'
                elif self.state == 'WaitingIncrease' and self.height_after_pullback is not None and self.is_pattern_complete(height):
                    # Complete the pattern
                    pattern = {
                        'pivot_type': self.pivot_type,
                        'initial_pivot_height': self.current_pivot_height,
                        'pullback_height': self.pullback_height,
                        'new_pivot_height': height
                    }
                    self.patterns.append(pattern)
                    print(f"Pattern completed: {pattern}")
                    # Reset for next pattern detection
                    self.current_pivot_height = height
                    self.pullback_height = None
                    self.height_after_pullback = None
                    self.state = 'WaitingPullback'
                else:
                    # Do not update pivot; continue waiting
                    print(f"New {event_type} with height {height} does not replace pivot or complete pattern.")
            else:
                # Different pivot type received; ignore
                print(f"Received {event_type} while tracking {self.pivot_type}; ignoring.")

    def handle_height(self, height):
        if self.state == 'WaitingPullback':
            required_pullback_height = self.calculate_required_pullback()
            if self.is_pullback_detected(height, required_pullback_height):
                self.pullback_height = height
                self.state = 'WaitingIncrease'
                print(f"Pullback detected for {self.pivot_type}. Height: {height}, Required: {required_pullback_height}")
        elif self.state == 'WaitingIncrease':
            if self.is_height_moving_in_expected_direction_after_pullback(height):
                self.height_after_pullback = height
                print(f"Height movement detected after {self.pivot_type} pullback. Current height: {height}")

    def calculate_required_pullback(self):
        """Calculate the required pullback height based on the pivot and threshold."""
        pivot_abs = abs(self.current_pivot_height)
        return pivot_abs * (1 - self.pullback_threshold)

    def should_update_pivot(self, height):
        """Determine if the pivot should be updated based on the new height."""
        if abs(height) > abs(self.current_pivot_height):
            return True
        return False

    def is_pullback_detected(self, height, required_pullback_height):
        """Check if a pullback is detected based on the pivot type and height."""
        if abs(height) <= required_pullback_height:
            return True
        return False

    def is_height_moving_in_expected_direction_after_pullback(self, height):
        """Check if the height is moving in the expected direction after the pullback."""
        if self.pivot_type == 'LOCAL_MIN':
            return abs(height) > abs(self.pullback_height)
        elif self.pivot_type == 'LOCAL_MAX':
            return abs(height) > abs(self.pullback_height)
        return False

    def is_pattern_complete(self, height):
        """Check if the pattern is complete based on the pivot type and new extrema height."""
        if abs(height) > abs(self.current_pivot_height):
            return True
        return False

    def get_patterns(self):
        """Return the list of detected patterns."""
        return self.patterns

# Example Usage
if __name__ == "__main__":
    detector = PatternDetector(pullback_threshold=0.8)  # 80% pullback towards zero

    # Simulated sequence of events with negative and positive HEIGHT values
    events = [
        # LOCAL_MIN Pattern (negative heights)
        ('HEIGHT', -10),
        ('LOCAL_MIN', -10),    # Pivot set to -10
        ('LOCAL_MIN', -12),    # Pivot updated to -12 (more significant)
        ('HEIGHT', -2),        # Pullback detected (-2 is 80% closer to zero from -10 and -12)
        ('HEIGHT', -3),        # Height movement detected (moving away from pullback height)
        ('LOCAL_MIN', -15),    # Pattern completed (-15 is more significant than pivot -12)

        # LOCAL_MAX Pattern (positive heights)
        ('HEIGHT', 8),
        ('LOCAL_MAX', 8),      # Pivot set to 8
        ('HEIGHT', 1.6),       # Pullback detected (1.6 is 80% closer to zero from 8)
        ('HEIGHT', 2),         # Height movement detected
        ('LOCAL_MAX', 10),     # Pattern completed (10 is more significant than pivot 8)

        # Additional Patterns
        ('HEIGHT', -5),
        ('LOCAL_MIN', -5),     # Pivot set to -5
        ('HEIGHT', -1),        # Pullback detected (-1 is 80% closer to zero from -5)
        ('HEIGHT', -1.5),      # Height movement detected
        ('LOCAL_MIN', -6),     # Pattern completed (-6 is more significant than pivot -5)

        ('HEIGHT', 6),
        ('LOCAL_MAX', 6),      # Pivot set to 6
        ('HEIGHT', 1.2),       # Pullback detected (1.2 is 80% closer to zero from 6)
        ('HEIGHT', 1.5),       # Height movement detected
        ('LOCAL_MAX', 7),      # Pattern completed (7 is more significant than pivot 6),
    ]

    for event in events:
        detector.process_event(*event)

    print("\nDetected Patterns:")
    for pattern in detector.get_patterns():
        print(pattern)
