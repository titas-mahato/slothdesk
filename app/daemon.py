"""
Sloth-mode background file watcher daemon.
Implements patient debounce logic so file downloads and writes finish completely
before invoking local classification and organization.
"""

import argparse
import os
import sys
import time
from typing import Dict
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from app.janitor import SlothJanitorService


class SlothDebouncedEventHandler(FileSystemEventHandler):
    """
    Handles new file events with sloth-like patience.
    Debounces file creation to prevent moving partially downloaded files (.crdownload, .part, .tmp).
    """

    def __init__(self, target_dir: str, debounce_seconds: int = 5, dry_run: bool = False):
        super().__init__()
        self.target_dir = os.path.abspath(target_dir)
        self.debounce_seconds = debounce_seconds
        self.dry_run = dry_run
        self.pending_files: Dict[str, float] = {}
        self.janitor = SlothJanitorService()

    def on_created(self, event):
        if not event.is_directory:
            self._register_activity(event.src_path)

    def on_modified(self, event):
        if not event.is_directory:
            self._register_activity(event.src_path)

    def _register_activity(self, path: str):
        fname = os.path.basename(path)
        # Skip temporary download files
        if fname.endswith((".crdownload", ".part", ".tmp", ".download", ".aria2")):
            return
        if fname.startswith("."):
            return
        self.pending_files[path] = time.time()

    def tick(self):
        """Processes files that have settled with no new modifications."""
        now = time.time()
        ready_files = []

        for path, last_seen in list(self.pending_files.items()):
            if now - last_seen >= self.debounce_seconds:
                if os.path.exists(path):
                    ready_files.append(path)
                del self.pending_files[path]

        if ready_files:
            print(f"[SlothDesk Daemon] Sloth woke up: organizing {len(ready_files)} settled files...")
            try:
                res = self.janitor.organize_real_directory(self.target_dir, dry_run=self.dry_run)
                print(f"[SlothDesk Daemon] Done! Organized into drawers (DryRun={self.dry_run}). Going back to sleep.")
            except Exception as e:
                print(f"[SlothDesk Daemon] Error organizing directory: {e}", file=sys.stderr)


def run_daemon(target_dir: str, debounce: int = 5, dry_run: bool = False):
    """Starts the background watcher."""
    print("=" * 60)
    print(" 🦥 SlothDesk Autonomous Janitor Daemon")
    print(f" Watching: {os.path.abspath(target_dir)}")
    print(f" Sloth Debounce: {debounce}s (waits for downloads to complete)")
    print(f" Mode: {'DRY RUN (Preview Only)' if dry_run else 'ACTIVE (Real moves)'}")
    print("=" * 60)

    handler = SlothDebouncedEventHandler(target_dir, debounce_seconds=debounce, dry_run=dry_run)
    observer = Observer()
    observer.schedule(handler, path=target_dir, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
            handler.tick()
    except KeyboardInterrupt:
        print("\n[SlothDesk] Sloth went back to sleep. Exiting.")
        observer.stop()
    observer.join()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SlothDesk background watcher")
    parser.add_argument("--path", default=".", help="Target directory to watch (e.g. ~/Downloads)")
    parser.add_argument("--debounce", type=int, default=5, help="Debounce duration in seconds")
    parser.add_argument("--dry-run", action="store_true", help="Preview moves without moving files")
    args = parser.parse_args()

    run_daemon(target_dir=args.path, debounce=args.debounce, dry_run=args.dry_run)
