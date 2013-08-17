from argparse import ArgumentParser
from subprocess import call
import functools
import logging
import os
import os.path
import platform
import shlex
import signal
import threading
import time

from s3 import s3

signal.signal(signal.SIGINT, signal.SIG_DFL)

FORMAT = '%(asctime)-15s %(message)s'
logging.basicConfig(format=FORMAT)
logging.getLogger().setLevel(logging.INFO)


SYNC_DELAY = 0.1

BASE_PATH = "/Users/eric/Documents/work/vapordrive/"


def _ensure_trailing_slash_present(path_spec):
    path_spec = os.path.normpath(path_spec)

    if path_spec[-1] != os.sep:
        path_spec += os.sep
    return path_spec


class Syncer(threading.Thread):

    def __init__(self, options):
        super(Syncer, self).__init__()

        self.source = _ensure_trailing_slash_present(source)
        # self.remote_spec = _ensure_trailing_slash_present(
        #     self.options.remote_spec)

        self.lock = threading.Lock()
        self.last_event = 0
        self.path = None

    def add_event(self, path):
        with self.lock:
            self.last_event = time.time()
            if self.path is None:
                self.path = path
            else:
                self.path = os.path.commonprefix([self.path, path])

    def write_remote_file(self, path):
        file_md5 = s3.md5_file(path)
        file_obj = open("%s%s" % (path, ".remote"), "w")
        file_obj.write(file_md5)
        file_obj.close()

    def watch_complete(self):
        self.path = None

    def walk_and_sync(self, path):
        for root, dirs, files in os.walk(path):
            for filename in files:
                s3_key = os.path.join(root, filename)

                ext = os.path.splitext(filename)[-1]

                print "EXTENSION IS:", ext

                if not ext == ".remote":
                    s3.upload(s3_key)
                    self.write_remote_file(s3_key)
                    os.remove(s3_key)

    def sync_cb(self):
        with self.lock:
            if not self.path or time.time() - self.last_event < SYNC_DELAY:
                return

            normalized_path = os.path.normpath(self.path)
            if os.path.isdir(normalized_path):
                normalized_path += os.sep

            common_path = os.path.commonprefix([normalized_path, BASE_PATH])
            s3_path = normalized_path[len(common_path):]
            self.walk_and_sync(s3_path)

            self.watch_complete()

    def run(self):
        while True:
            self.sync_cb()
            time.sleep(SYNC_DELAY / 2)


def file_changed(add_event, subpath, mask):
    add_event(subpath)


if __name__ == '__main__':

    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler

    source = "/Users/eric/Documents/work/vapordrive/vapor"

    syncer = Syncer(source)
    syncer.start()

    class FileChangedHandler(FileSystemEventHandler):
        """Logs all the events captured."""

        def __init__(self, syncer):
            self.syncer = syncer

        def on_any_event(self, event):
            super(FileChangedHandler, self).on_any_event(event)
            self.syncer.add_event(event.src_path)

    observer = Observer()
    observer.schedule(
        FileChangedHandler(syncer),
        path=source,
        recursive=True
    )
    observer.start()
