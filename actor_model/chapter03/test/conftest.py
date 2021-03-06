from collections import namedtuple

import pytest
import time
import threading

# 先用库的类来测试.
from pykka import ThreadingActor, ThreadingFuture


Runtime = namedtuple(
    "Runtime",
    ["name", "actor_class", "event_class", "future_class", "sleep_func"],
)

RUNTIMES = {
    "threading": pytest.param(
        Runtime(
            name="threading",
            actor_class=ThreadingActor,
            event_class=threading.Event,
            future_class=ThreadingFuture,
            sleep_func=time.sleep,
        ),
        id="threading",
    )
}


# fixture的参数化
# 需要使用params参数进行参数化，然后通过request.param取出
@pytest.fixture(scope="session", params=RUNTIMES.values())
def runtime(request):
    return request.param


@pytest.fixture
def events(runtime):
    class Events:
        on_start_was_called = runtime.event_class()
        on_stop_was_called = runtime.event_class()
        on_failure_was_called = runtime.event_class()
        greetings_was_received = runtime.event_class()
        actor_registered_before_on_start_was_called = runtime.event_class()

    return Events()


@pytest.fixture(scope="module")
def early_stopping_actor_class(runtime):
    class EarlyStoppingActor(runtime.actor_class):
        def __init__(self, events):
            super().__init__()
            self.events = events

        def on_start(self):
            self.stop()

        def on_stop(self):
            self.events.on_stop_was_called.set()

    return EarlyStoppingActor


# 定义一个failure actor
@pytest.fixture(scope="module")
def failing_on_failure_actor_class(runtime):
    class FailingOnFailureActor(runtime.actor_class):
        def __init__(self, events):
            super().__init__()
            self.events = events

        def on_receive(self, message):
            if message.get("command") == "raise exception":
                raise Exception("on_receive failure")
            else:
                super().on_receive(message)

        def on_failure(self, *args):
            try:
                raise RuntimeError("on_failure failure")
            finally:
                self.events.on_failure_was_called.set()

    return FailingOnFailureActor



@pytest.fixture(scope="module")
def late_failing_actor_class(runtime):
    class LateFailingActor(runtime.actor_class):
        def __init__(self, events):
            super().__init__()
            self.events = events

        def on_start(self):
            self.stop()

        def on_stop(self):
            try:
                raise RuntimeError("on_stop failure")
            finally:
                self.events.on_stop_was_called.set()

    return LateFailingActor


# fixture的参数化, 通过request.param取出，多个参数测试。
# @pytest.fixture(params=['a', 'v', 'c', 'e3'])
# def fix(request):
#     return request.param
#
# def test_fixture_param(fix):
#     print(fix)
