"""
actor include future(result from queue or set value of the queue)

future --- > actor
|               |
|               |
ThreadingFuture -->ThreadingActor
"""
import pykka
import queue
import sys
import threading
from dataclasses import dataclass
from typing import Any, Optional

from .exceptions import Timeout
from .future import Future
from .actor import Actor
from pykka import _compat


@dataclass
class ThreadingFutureResult:
    values: Optional[Any] = None


class ThreadingFuture(Future):
    def __init__(self):
        super(ThreadingFuture, self).__init__()
        self._queue = _compat.queue.Queue(maxsize=1)
        self._data = None

    def get(self, timeout=None):
        try:
            # get_hook 没有捆绑函数  Raise NotImplementedError
            return super(ThreadingFuture, self).get(timeout=timeout)
        except NotImplementedError:
            # 返回NotImplementedError错误的时候
            pass
        # 返回NotImplementedError错误的时候 会执行下列代码...
        try:
            if self._data is None:
                self._data = self._queue.get(True, timeout)
            if 'exc_info' in self._data:
                _compat.reraise(*self._data['exc_info'])
            else:
                return self._data['value']
        except _compat.queue.Empty:
            raise Timeout('{} seconds'.format(timeout))

    def set(self, value=None):
        self._queue.put({'value': value}, block=False)

    def set_exception(self, exc_info=None):
        assert exc_info is None or len(exc_info) == 3
        self._queue.put({'exc_info': exc_info or sys.exc_info()})


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

