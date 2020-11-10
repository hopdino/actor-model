"""
actor include future(result from queue or set value of the queue)

future --- > actor
|               |
|               |
ThreadingFuture -->ThreadingActor
"""
import queue
import threading
from dataclasses import dataclass
from typing import Any, Optional

from pykka import Timeout, Actor
from sn8.future import Future


@dataclass
class ThreadingFutureResult:
    values: Optional[Any] = None


class ThreadingFuture(Future):
    def __init__(self):
        super().__init__()
        self._queue = queue.Queue(maxsize=1)
        self._result = None

    def get(self, timeout=None) -> ThreadingFutureResult:
        try:
            return super().get(timeout=timeout)

        except NotImplementedError:
            pass

        # 处理特殊情况.
        try:
            if self._result is None:
                self._result = self._queue.get(True, timeout)
            # remove some exc_trace_info
            else:
                return self._result.value

        except queue.Empty:
            raise Timeout(f"{timeout} seconds")

    def set(self, value=None):
        self._queue.put(ThreadingFutureResult(value=value), block=False)


# Threading Actor
class ThreadingActor(Actor):
    # 非守护进程
    use_daemon_thread = False

    @staticmethod
    def _create_actor_inbox():
        return queue.Queue()

    @staticmethod
    def _create_future():
        return ThreadingFuture()

    def _start_actor_loop(self):
        thread = threading.Thread(target=self._actor_loop)
        thread.name = thread.name.replace('Thread', self.__class__.__name__)
        thread.daemon = self.use_daemon_thread
        thread.start()

