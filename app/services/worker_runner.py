"""Simple single-worker helper for background tasks."""

from dataclasses import dataclass
from threading import Thread


@dataclass
class WorkerJob:
    """Describe the currently running background job."""

    kind: str = ""
    thread: Thread | None = None
    result: object | None = None


class WorkerRunner:
    """Run one background job at a time and store its final result."""

    def __init__(self):
        """Initialize an empty worker slot."""

        self.job = WorkerJob()

    def start(self, kind, target, *args):
        """Start a new worker thread and reset the previous result."""

        self.job.kind = kind
        self.job.result = None
        self.job.thread = Thread(target=target, args=args, daemon=True)
        self.job.thread.start()

    def is_running(self):
        """Return `True` while the current worker thread is alive."""

        return self.job.thread is not None and self.job.thread.is_alive()

    def finish(self):
        """Return the finished job data and reset the runner state."""

        finished_kind = self.job.kind
        finished_result = self.job.result
        self.job = WorkerJob()
        return finished_kind, finished_result
