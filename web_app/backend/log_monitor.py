"""
Log File Monitor

Continuously monitors the runtime error log file and reports on new errors.
Can be used to track runtime issues in real-time.
"""

import time
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from logger import get_log_file_path, get_recent_errors


class LogMonitor:
    """Monitor for runtime error log file."""
    
    def __init__(self, log_file: Optional[Path] = None):
        self.log_file = log_file or get_log_file_path()
        self.last_position = 0
        self.last_check_time = time.time()
        
        # Initialize position to end of file
        if self.log_file.exists():
            self.last_position = self.log_file.stat().st_size
    
    def get_new_errors(self) -> List[str]:
        """
        Get new error entries since last check.
        
        Returns:
            List of new error log lines
        """
        if not self.log_file.exists():
            return []
        
        new_errors = []
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                # Seek to last position
                f.seek(self.last_position)
                
                # Read new content
                new_content = f.read()
                if new_content:
                    new_errors = [line for line in new_content.split('\n') if line.strip()]
                
                # Update position
                self.last_position = f.tell()
        except Exception as e:
            print(f"[LOG_MONITOR] Error reading log file: {e}")
        
        return new_errors
    
    def get_all_errors(self) -> List[str]:
        """
        Get all error entries from log file.
        
        Returns:
            List of all error log lines
        """
        return get_recent_errors(limit=1000)
    
    def get_error_count(self) -> int:
        """
        Get total number of error entries in log file.
        
        Returns:
            Number of error entries
        """
        if not self.log_file.exists():
            return 0
        
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                # Count ERROR level entries
                error_count = sum(1 for line in lines if 'ERROR' in line)
                return error_count
        except Exception as e:
            print(f"[LOG_MONITOR] Error counting errors: {e}")
            return 0
    
    def get_log_stats(self) -> Dict:
        """
        Get statistics about the log file.
        
        Returns:
            Dictionary with log statistics
        """
        stats = {
            'log_file': str(self.log_file),
            'exists': self.log_file.exists(),
            'error_count': 0,
            'file_size': 0,
            'last_modified': None,
            'new_errors_since_last_check': 0
        }
        
        if self.log_file.exists():
            try:
                stat = self.log_file.stat()
                stats['file_size'] = stat.st_size
                stats['last_modified'] = datetime.fromtimestamp(stat.st_mtime).isoformat()
                stats['error_count'] = self.get_error_count()
                
                # Check for new errors
                new_errors = self.get_new_errors()
                stats['new_errors_since_last_check'] = len(new_errors)
            except Exception as e:
                stats['error'] = str(e)
        
        return stats
    
    def watch(self, interval: float = 1.0, callback=None):
        """
        Continuously monitor log file for new errors.
        
        Args:
            interval: Check interval in seconds
            callback: Optional callback function to call when new errors are found
        """
        print(f"[LOG_MONITOR] Starting to monitor: {self.log_file}")
        print(f"[LOG_MONITOR] Check interval: {interval} seconds")
        print(f"[LOG_MONITOR] Press Ctrl+C to stop\n")
        
        try:
            while True:
                new_errors = self.get_new_errors()
                
                if new_errors:
                    print(f"[LOG_MONITOR] {len(new_errors)} new error(s) detected at {datetime.now().isoformat()}")
                    for error in new_errors:
                        print(f"  {error}")
                    print()
                    
                    if callback:
                        callback(new_errors)
                
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\n[LOG_MONITOR] Monitoring stopped")


# Global monitor instance
_monitor_instance = None

def get_monitor() -> LogMonitor:
    """Get or create global log monitor instance."""
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = LogMonitor()
    return _monitor_instance


if __name__ == '__main__':
    # Example usage: monitor log file
    monitor = LogMonitor()
    
    def on_new_error(errors):
        """Callback for new errors."""
        print(f"⚠️  {len(errors)} new error(s) detected!")
    
    # Start monitoring
    monitor.watch(interval=1.0, callback=on_new_error)
