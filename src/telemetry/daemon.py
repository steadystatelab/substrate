import time
import math
import logging
import sys
from collections import deque
from .db import init_db, insert_snapshot

# Attempt to import dependencies for Windows
try:
    import win32gui
    import pywintypes
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False

try:
    from pynput import mouse, keyboard
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False

# Setup minimal logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')

class WindowTracker:
    """Abstracts foreground window tracking to support cross-platform or mock fallback."""
    def get_foreground_window_handle_and_title(self):
        if WIN32_AVAILABLE:
            try:
                hwnd = win32gui.GetForegroundWindow()
                title = win32gui.GetWindowText(hwnd)
                return hwnd, title
            except Exception:
                return None, "Unknown"
        else:
            return None, "Mock-Window"


class BruckSignature:
    """
    Analyzes telemetry snapshots with threshold triggers and hysteresis.
    Replicates original math without numpy.
    """
    def __init__(self):
        self.heading_buffer = deque(maxlen=50)
        self.last_pos = None
        self.signal_cooldown = 0

    def calculate_entropy(self, current_pos):
        if self.last_pos is None:
            self.last_pos = current_pos
            return 0.0

        dx = current_pos[0] - self.last_pos[0]
        dy = current_pos[1] - self.last_pos[1]
        self.last_pos = current_pos

        if dx != 0 or dy != 0:
            angle = math.atan2(dy, dx)
            if angle < 0:
                angle += 2 * math.pi
            bin_index = int(angle / (math.pi / 4)) % 8
            self.heading_buffer.append(bin_index)

        if len(self.heading_buffer) < 50:
            return 0.0

        return self._compute_shannon()

    def _compute_shannon(self):
        counts = [0] * 8
        for b in self.heading_buffer:
            counts[b] += 1

        total = len(self.heading_buffer)
        probs = [c / total for c in counts if c > 0]
        return -sum([p * math.log2(p) for p in probs])

    def check_interruption_threshold(self, entropy, frag):
        """
        Evaluates thresholds against current state with hysteresis.
        """
        # Hardcoded thresholds from original logic to match legacy parity
        ENTROPY_THRESHOLD = 2.5
        FRAG_THRESHOLD = 5.0
        COOLDOWN_CYCLES = 30 # 3.0s hysteresis at 10Hz

        is_triggered = (entropy > ENTROPY_THRESHOLD and frag > FRAG_THRESHOLD)

        if is_triggered:
            self.signal_cooldown = COOLDOWN_CYCLES
            return True

        if self.signal_cooldown > 0:
            self.signal_cooldown -= 1
            return True

        return False


class TelemetryMonitor:
    def __init__(self):
        self.signature = BruckSignature()
        self.window_tracker = WindowTracker()

        # Internal State
        self.current_pos = (0, 0)
        self.last_keypress_time = time.time()
        self.last_window_handle = None
        self.last_window_title = "Unknown"

        # O(1) Window: 60 seconds @ 10Hz = 600 samples
        self.switch_history = deque([0]*600, maxlen=600)
        self.window_switch_total = 0

        self.cycle_count = 0
        self.is_running = False

        # Constants
        self.SAMPLING_RATE = 0.1 # 10Hz
        self.LOG_FREQUENCY = 50  # Snapshot logging every 5.0s
        self.CALIBRATION_THRESHOLD = 3000 # 5-minute calibration phase

    def _on_mouse_move(self, x, y):
        self.current_pos = (x, y)

    def _on_key_press(self, key):
        self.last_keypress_time = time.time()

    def _update_window_context(self):
        switched = 0
        curr, title = self.window_tracker.get_foreground_window_handle_and_title()

        if curr != self.last_window_handle:
            if self.last_window_handle is not None:
                switched = 1
            self.last_window_handle = curr
            self.last_window_title = title

        evicted = self.switch_history[0]
        self.window_switch_total = self.window_switch_total - evicted + switched
        self.switch_history.append(switched)

    def start(self):
        logging.info("TelemetryMonitor: Starting Daemon...")
        init_db()
        self.is_running = True

        m_listener = None
        k_listener = None

        if PYNPUT_AVAILABLE:
            m_listener = mouse.Listener(on_move=self._on_mouse_move)
            k_listener = keyboard.Listener(on_press=self._on_key_press)
            m_listener.start()
            k_listener.start()
        else:
            logging.warning("pynput is not available. Falling back to mock input.")

        next_tick = time.time()

        try:
            while self.is_running:
                # 1. Update rolling window state
                self._update_window_context()

                # 2. Extract metrics
                entropy = self.signature.calculate_entropy(self.current_pos)
                is_warmup = len(self.signature.heading_buffer) < 50
                context_frag = float(self.window_switch_total)
                kb_idle = time.time() - self.last_keypress_time

                # Update hysteresis
                self.signature.check_interruption_threshold(entropy, context_frag)

                mode = "CALIBRATION" if self.cycle_count < self.CALIBRATION_THRESHOLD else "OPERATIONAL"
                if is_warmup:
                    mode = "WARMUP"

                # 3. Aggregated 5.0 second logging
                if self.cycle_count % self.LOG_FREQUENCY == 0 and self.cycle_count > 0:
                    reported_entropy = round(entropy, 4) if not is_warmup else 0.0
                    reported_idle = round(kb_idle, 2)
                    insert_snapshot(
                        mouse_entropy=reported_entropy,
                        context_fragmentation=context_frag,
                        keyboard_idle_seconds=reported_idle,
                        window_title=self.last_window_title,
                        mode=mode
                    )
                    logging.info(f"SNAPSHOT SAVED: entropy={reported_entropy}, frag={context_frag}, idle={reported_idle}, mode={mode}")

                # 4. Drift-Corrected Cadence
                self.cycle_count += 1
                next_tick += self.SAMPLING_RATE
                sleep_time = max(0, next_tick - time.time())
                time.sleep(sleep_time)

        except KeyboardInterrupt:
            logging.info("TelemetryMonitor: Manual exit.")
        finally:
            self.is_running = False
            if m_listener:
                m_listener.stop()
            if k_listener:
                k_listener.stop()
            logging.info("TelemetryMonitor: Shutdown complete.")

if __name__ == "__main__":
    monitor = TelemetryMonitor()
    monitor.start()
