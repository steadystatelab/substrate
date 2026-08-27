import time
import logging
import os
import math
import sys
import json
from collections import deque

# Attempt to import dependencies
try:
    from pynput import mouse, keyboard
    import win32gui
    import win32pipe
    import win32file
    import pywintypes
except ImportError:
    print("CRITICAL: Missing dependencies. Please run: pip install pynput pywin32")
    sys.exit(1)

# Optional dependency: numpy
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

# --- CONFIGURATION INITIALIZATION ---
DEFAULT_CONFIG = {
    "SAMPLING_RATE": 0.1,
    "ENTROPY_THRESHOLD": 2.5,
    "FRAG_THRESHOLD": 5.0,
    "ROOT_DIR": r"G:\My Drive\_ANTIGRAV_BUILD_CORE"
}
CONFIG_PATH = r"G:\My Drive\_ANTIGRAV_BUILD_CORE\01_Blueprints\config.json"

def load_config():
    """
    Loads configuration from JSON file or initializes with defaults if missing.
    """
    if not os.path.exists(CONFIG_PATH):
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        try:
            with open(CONFIG_PATH, 'w') as f:
                json.dump(DEFAULT_CONFIG, f, indent=4)
            return DEFAULT_CONFIG
        except Exception as e:
            print(f"WARNING: Could not create config.json ({e}). Using hardcoded defaults.")
            return DEFAULT_CONFIG
    
    try:
        with open(CONFIG_PATH, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"ERROR: Could not read config.json ({e}). Using hardcoded defaults.")
        return DEFAULT_CONFIG

CONFIG = load_config()

# Resolved Paths and Constants
ROOT_DIR = CONFIG.get("ROOT_DIR", r"G:\My Drive\_ANTIGRAV_BUILD_CORE")
LOG_DIR = os.path.join(ROOT_DIR, "03_Telemetry")
LOG_FILE = os.path.join(LOG_DIR, "monitor_log.txt")
CALIB_REPORT_FILE = os.path.join(LOG_DIR, "calibration_report.json")
PIPE_NAME = r'\\.\pipe\BruckSignal'

SAMPLING_RATE = CONFIG.get("SAMPLING_RATE", 0.1)
ENTROPY_THRESHOLD = CONFIG.get("ENTROPY_THRESHOLD", 2.5)
FRAG_THRESHOLD = CONFIG.get("FRAG_THRESHOLD", 5.0)

LOG_FREQUENCY = 50   # Snapshot logging every 5.0s
COOLDOWN_CYCLES = 30 # 3.0s hysteresis
CALIBRATION_THRESHOLD = 3000 # 5-minute calibration phase

# Ensure system directories exist
os.makedirs(LOG_DIR, exist_ok=True)

# Logging Setup
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class BruckSignature:
    """
    Analyzes telemetry snapshots with threshold triggers and hysteresis.
    """
    def __init__(self):
        self.pipe_handle = None
        self.pipe_error_notified = False
        self.heading_buffer = deque(maxlen=50)
        self.last_pos = None
        self.signal_cooldown = 0
        logging.info("BruckSignature: Configuration-aware analysis module active.")

    def _get_pipe_handle(self):
        if self.pipe_handle is not None:
            return self.pipe_handle
        
        try:
            self.pipe_handle = win32file.CreateFile(
                PIPE_NAME,
                win32file.GENERIC_WRITE,
                0, None,
                win32file.OPEN_EXISTING,
                0, None
            )
            return self.pipe_handle
        except pywintypes.error:
            self.pipe_handle = None
            return None

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

        if HAS_NUMPY:
            probs_arr = np.array(probs)
            return -float(np.sum(probs_arr * np.log2(probs_arr)))
        else:
            return -sum([p * math.log2(p) for p in probs])

    def check_interruption_threshold(self, entropy, frag):
        """
        Evaluates thresholds against current state with hysteresis.
        """
        is_triggered = (entropy > ENTROPY_THRESHOLD and frag > FRAG_THRESHOLD)
        
        if is_triggered:
            self.signal_cooldown = COOLDOWN_CYCLES
            return True
        
        if self.signal_cooldown > 0:
            self.signal_cooldown -= 1
            return True
            
        return False

    def write_to_pipe(self, metrics):
        handle = self._get_pipe_handle()
        if not handle:
            if not self.pipe_error_notified:
                logging.warning(r"PIPE_DISCONNECT: \\.\pipe\BruckSignal unavailable.")
                self.pipe_error_notified = True
            return

        try:
            msg = f"METRICS:{metrics}\n".encode('utf-8')
            win32file.WriteFile(handle, msg)
            
            if self.pipe_error_notified:
                logging.info("PIPE_RECONNECTED: Signal stream restored.")
                self.pipe_error_notified = False
                
        except pywintypes.error:
            try:
                win32file.CloseHandle(handle)
            except:
                pass
            self.pipe_handle = None
            if not self.pipe_error_notified:
                logging.warning("PIPE_ERROR: Handle invalidated. Re-connecting...")
                self.pipe_error_notified = True

class TelemetryMonitor:
    def __init__(self):
        self.signature = BruckSignature()
        
        # Internal State
        self.current_pos = (0, 0)
        self.last_keypress_time = time.time()
        self.last_window_handle = None
        
        # O(1) Window: 60 seconds @ 10Hz = 600 samples
        self.switch_history = deque([0]*600, maxlen=600)
        self.window_switch_total = 0
        
        self.cycle_count = 0
        self.is_running = False
        
        # Calibration Session Buffers
        self.calib_entropy = []
        self.calib_frag = []

    def _on_mouse_move(self, x, y):
        self.current_pos = (x, y)

    def _on_key_press(self, key):
        self.last_keypress_time = time.time()

    def _update_window_context(self):
        switched = 0
        try:
            curr = win32gui.GetForegroundWindow()
            if curr != self.last_window_handle:
                if self.last_window_handle is not None:
                    switched = 1
                self.last_window_handle = curr
        except Exception:
            pass
        
        evicted = self.switch_history[0]
        self.window_switch_total = self.window_switch_total - evicted + switched
        self.switch_history.append(switched)

    def _generate_calibration_report(self):
        """
        Computes Mean and 95th Percentile for session data and saves to JSON.
        """
        logging.info("TelemetryMonitor: Finalizing calibration phase...")
        
        def get_stats(data):
            if not data: return {"mean": 0.0, "p95": 0.0}
            mean = sum(data) / len(data)
            sorted_data = sorted(data)
            p95 = sorted_data[int(0.95 * (len(data)-1))]
            return {"mean": round(mean, 4), "p95": round(p95, 4)}

        report = {
            "session_id": int(time.time()),
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
            "duration_samples": len(self.calib_entropy),
            "mouse_entropy": get_stats(self.calib_entropy),
            "context_fragmentation": get_stats(self.calib_frag),
            "config_baseline": {
                "entropy_threshold": ENTROPY_THRESHOLD,
                "frag_threshold": FRAG_THRESHOLD
            }
        }
        
        try:
            with open(CALIB_REPORT_FILE, 'w') as f:
                json.dump(report, f, indent=4)
            logging.info(f"CALIBRATION_REPORT: Summary persisted to {CALIB_REPORT_FILE}")
        except Exception as e:
            logging.error(f"CALIBRATION_REPORT: Failed to save report - {e}")
        
        # Flush buffers
        self.calib_entropy = []
        self.calib_frag = []

    def start(self):
        logging.info(f"TelemetryMonitor: Service started (ROOT: {ROOT_DIR}).")
        self.is_running = True
        
        m_listener = mouse.Listener(on_move=self._on_mouse_move)
        k_listener = keyboard.Listener(on_press=self._on_key_press)
        m_listener.start()
        k_listener.start()
        
        next_tick = time.time()
        
        try:
            while self.is_running:
                # 1. Update rolling window state
                self._update_window_context()
                
                # 2. Extract metrics
                entropy = self.signature.calculate_entropy(self.current_pos)
                is_warmup = len(self.signature.heading_buffer) < 50
                context_frag = float(self.window_switch_total)
                
                # 3. Calibration Data Capture
                if self.cycle_count < CALIBRATION_THRESHOLD:
                    if not is_warmup:
                        self.calib_entropy.append(entropy)
                    self.calib_frag.append(context_frag)
                elif self.cycle_count == CALIBRATION_THRESHOLD:
                    self._generate_calibration_report()
                
                # 4. Evaluation Logic
                kb_idle = time.time() - self.last_keypress_time
                interruption = self.signature.check_interruption_threshold(entropy, context_frag)
                
                metrics = {
                    "mouse_entropy": round(entropy, 4) if not is_warmup else 0.0,
                    "context_fragmentation": context_frag,
                    "keyboard_idle": round(kb_idle, 2),
                    "status": "WARMUP" if is_warmup else "ACTIVE",
                    "mode": "CALIBRATION" if self.cycle_count < CALIBRATION_THRESHOLD else "OPERATIONAL",
                    "interruption_signal": interruption
                }
                
                # 5. Persistence and Signaling
                if self.cycle_count % LOG_FREQUENCY == 0:
                    logging.info(f"SNAPSHOT: {metrics}")
                self.signature.write_to_pipe(metrics)
                
                # 6. Drift-Corrected Cadence
                self.cycle_count += 1
                next_tick += SAMPLING_RATE
                sleep_time = max(0, next_tick - time.time())
                time.sleep(sleep_time)
                
        except KeyboardInterrupt:
            logging.info("TelemetryMonitor: Manual exit.")
        finally:
            self.is_running = False
            m_listener.stop()
            k_listener.stop()
            # Kernel handle cleanup
            if self.signature.pipe_handle:
                try:
                    win32file.CloseHandle(self.signature.pipe_handle)
                    logging.info("TelemetryMonitor: Named pipe handle CLOSED.")
                except Exception as e:
                    logging.debug(f"TelemetryMonitor: Handle closure failed - {e}")
            logging.info("TelemetryMonitor: Final shutdown complete.")

if __name__ == "__main__":
    try:
        monitor = TelemetryMonitor()
        monitor.start()
    except Exception as e:
        print(f"FATAL SYSTEM ERROR: {e}")
        sys.exit(1)
