"""
Watch Log File Script

Continuously monitors the runtime error log file and displays new errors in real-time.
Run this script in a separate terminal to track runtime issues.
"""

import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.resolve()
sys.path.insert(0, str(backend_dir))

from log_monitor import LogMonitor
from logger import get_log_file_path

def main():
    """Main function to watch log file."""
    log_file = get_log_file_path()
    
    print("=" * 80)
    print("Runtime Error Log Monitor")
    print("=" * 80)
    print(f"Monitoring: {log_file}")
    print(f"Press Ctrl+C to stop")
    print("=" * 80)
    print()
    
    monitor = LogMonitor(log_file)
    
    # Show initial stats
    stats = monitor.get_log_stats()
    print(f"Log file exists: {stats['exists']}")
    if stats['exists']:
        print(f"Total errors: {stats['error_count']}")
        print(f"File size: {stats['file_size']} bytes")
        print(f"Last modified: {stats['last_modified']}")
    print()
    
    def on_new_error(errors):
        """Callback when new errors are detected."""
        print(f"\n{'='*80}")
        print(f"⚠️  NEW ERROR(S) DETECTED - {len(errors)} error(s)")
        print(f"{'='*80}")
        for i, error in enumerate(errors, 1):
            print(f"\n[{i}] {error}")
        print(f"{'='*80}\n")
    
    # Start monitoring
    try:
        monitor.watch(interval=0.5, callback=on_new_error)
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped by user.")
        sys.exit(0)

if __name__ == '__main__':
    main()
