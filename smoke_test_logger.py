"""Smoke test for BotLogger."""
import re
import sys
import os
from collections import Counter
from datetime import datetime

sys.path.insert(0, ".")
from models import BatchStats
from bot_logger import BotLogger

LOG_FILE = "test_bot_activity.log"

# Clean up any previous test file
if os.path.exists(LOG_FILE):
    os.remove(LOG_FILE)

logger = BotLogger(LOG_FILE)

# Test info / warning / error
logger.info("TestComp", "Pesan info")
logger.warning("TestComp", "Pesan warning")
logger.error("TestComp", "Pesan error")

# Test error with exc_info
try:
    raise ValueError("contoh exception")
except ValueError:
    logger.error("TestComp", "Error dengan stack trace", exc_info=True)

# Test summary
stats = BatchStats(
    total_sessions=10,
    successful=7,
    failed=3,
    failure_reasons=Counter({"FORM_FILL": 2, "SEED_LOGIN": 1}),
    start_time=datetime.now(),
    end_time=datetime.now(),
)
logger.summary(stats)

# Verify log file content
with open(LOG_FILE, encoding="utf-8") as f:
    content = f.read()

print("--- LOG FILE CONTENT ---")
print(content)

# Verify format for lines that start with '['
pattern = r"^\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\] \[(INFO|WARNING|ERROR)\] \[.+\] .+"
log_lines = [l for l in content.splitlines() if l.startswith("[")]
for line in log_lines:
    assert re.match(pattern, line), f"Format tidak sesuai: {line!r}"

print("Semua baris log memenuhi format yang ditentukan.")

# Clean up
os.remove(LOG_FILE)
print("Smoke test PASSED.")
