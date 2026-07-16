import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

def setup_logger():
    if sys.platform == "win32":
        temp_dir = os.environ.get("TEMP", os.environ.get("TMP", "C:\\Temp"))
        log_dir = Path(temp_dir) / "ShadowMonitor"
    else:
        log_dir = Path("/tmp") / "ShadowMonitor"
        
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "shadow_monitor.log"

    logger = logging.getLogger("ShadowMonitor")
    logger.setLevel(logging.DEBUG)

    # Max 5MB per file, max 5 files
    handler = RotatingFileHandler(
        log_file,
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding='utf-8'
    )
    
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)
    return logger

log = setup_logger()
