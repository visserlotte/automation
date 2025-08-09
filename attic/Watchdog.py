To create a comprehensive `Watchdog.py` script, we need to understand the key functionalities and objectives of a watchdog script. A typical watchdog can be used to monitor directories or files for changes and take specific actions when such changes are detected. One common implementation involves using the `watchdog` Python package to handle file system events.

Below is a complete and enhanced version of a `Watchdog.py` script, ready to be used or further improved based on additional specific requirements:

```python
import sys
import time
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

class WatchdogHandler(FileSystemEventHandler):
    """Logs all the events captured."""

    def on_modified(self, event):
        logging.info(f'Modified file: {event.src_path}')

    def on_created(self, event):
        logging.info(f'Created file: {event.src_path}')

    def on_deleted(self, event):
        logging.info(f'Deleted file: {event.src_path}')

    def on_moved(self, event):
        logging.info(f'Moved file: {event.src_path} to {event.dest_path}')

def monitor_directory(path):
    """Monitor a directory for file changes."""
    event_handler = WatchdogHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    logging.info(f'Started monitoring {path}')

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

def main():
    if len(sys.argv) != 2:
        logging.error('Usage: python Watchdog.py <path_to_watch>')
        sys.exit(1)

    path = sys.argv[1]
    logging.info(f'Initializing Watchdog for path: {path}')

    monitor_directory(path)

if __name__ == '__main__':
    main()
```

### Explanation:
1. **FileSystemEventHandler**: This custom handler (`WatchdogHandler`) processes and logs four types of file system events: modifications, creations, deletions, and moves.

2. **Logger**: It logs each event with a timestamp for easy tracking and debugging. The logging level is set to `INFO`, but this can be adjusted as needed.

3. **Observer**: Watches for changes in the specified directory and its subdirectories (`recursive=True`).

4. **Command-Line Arguments**: The script expects a single parameter which is the path to the directory being monitored. It exits with an error message if the parameter is missing.

5. **Graceful Shutdown**: A `try-except` block for capturing `KeyboardInterrupt` to gracefully stop the observer when requested.

Please ensure you have the `watchdog` package installed; you can install it using `pip install watchdog`. Adjustments can be made based on specific use cases or additional features as needed.