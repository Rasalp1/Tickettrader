#BEGRÄNSAR REQUESTSEN TILL GEMINI API
#GRÄNS: 15 RPM

import time
from collections import deque
import threading

class RateLimiter:
    def __init__(self, max_calls, time_window):
        self.max_calls = max_calls
        self.time_window = time_window
        self.call_times = deque()
        self.lock = threading.Lock()  # Use a lock for thread safety

    def check(self):
        """
        Checks if a new call is allowed.  If allowed, records the current time.
        If not allowed, it waits until the next call is allowed.
        This function is thread-safe.

        Returns:
            None:  It either allows the call (and records the time) or waits.
        """
        with self.lock:  # Acquire the lock
            current_time = time.time()
            # Remove calls that are outside the time window
            while self.call_times and self.call_times[0] <= current_time - self.time_window:
                self.call_times.popleft()

            # Check if we've reached the limit
            if len(self.call_times) < self.max_calls:
                self.call_times.append(current_time)  # Record the time of this call
                return  # Allow the call
            else:
                # Wait until the next call is allowed
                wait_time = self.call_times[0] - (current_time - self.time_window)
                print(f"Rate limit exceeded. Waiting {wait_time:.2f} seconds.")
                time.sleep(wait_time)
                self.call_times.append(time.time())  # Add current time after waiting
                return  # Allow the call after waiting

