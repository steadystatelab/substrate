import sqlite3
import os
import time
import tracemalloc
from unittest.mock import patch, MagicMock
import os

# Override DB path for tests before importing the module
os.environ["TELEMETRY_DB_PATH"] = "data/test_telemetry.db"

from src.telemetry.db import init_db, insert_snapshot, DB_PATH
from src.telemetry.daemon import TelemetryMonitor

def test_db_provisioning_and_schema():
    if DB_PATH.exists():
        os.remove(DB_PATH)

    init_db()

    assert DB_PATH.exists(), "Database file was not created"

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(telemetry_snapshots)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}

    assert "id" in columns
    assert "timestamp" in columns
    assert "mouse_entropy" in columns
    assert "context_fragmentation" in columns
    assert "keyboard_idle_seconds" in columns
    assert "window_title" in columns
    assert "mode" in columns

def test_atomic_inserts():
    if DB_PATH.exists():
        os.remove(DB_PATH)

    init_db()
    insert_snapshot(1.23, 4.5, 10.0, "Test Window", "OPERATIONAL")

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM telemetry_snapshots")
        rows = cursor.fetchall()

    assert len(rows) == 1
    row = rows[0]

    # row layout: id, timestamp, mouse_entropy, context_fragmentation, keyboard_idle_seconds, window_title, mode
    assert row[2] == 1.23
    assert row[3] == 4.5
    assert row[4] == 10.0
    assert row[5] == "Test Window"
    assert row[6] == "OPERATIONAL"


@patch('src.telemetry.daemon.time.sleep', return_value=None) # Don't actually sleep during test
def test_memory_footprint(mock_sleep):
    # Simulate a run to check memory
    tracemalloc.start()

    monitor = TelemetryMonitor()

    # mock the db functions to avoid I/O or test in-memory overhead
    with patch('src.telemetry.daemon.init_db'), patch('src.telemetry.daemon.insert_snapshot'):
        # run a simulated loop for 100 cycles (10 seconds)
        # we bypass the while loop by calling the loop logic directly
        monitor.is_running = True

        # prime the structures
        for _ in range(100):
            monitor._update_window_context()
            monitor.current_pos = (monitor.current_pos[0] + 1, monitor.current_pos[1] + 1)
            entropy = monitor.signature.calculate_entropy(monitor.current_pos)

    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    peak_mb = peak / 10**6
    assert peak_mb < 50.0, f"Peak memory usage exceeded 50MB constraint: {peak_mb} MB"
