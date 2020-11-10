import threading

import pytest
from ..threading import ThreadingActor
from ..threading import ThreadingFuture


@pytest.fixture(scope="module")
def actor_class():
    class ActorA(ThreadingActor):
        cat = "dog"

        def __init__(self, events):
            super().__init__()
            self.events = events

        def on_stop(self):
            """
            停止callback
            :return:
            """
            self.events.on_stop_was_called.set()

        def on_failure(self, *args):
            self.events.on_failure_was_called.set()

        def functional_hello(self, s):
            return f"Hello, {s}!"

        def set_cat(self, s):
            self.cat = s

        def raise_exception(self):
            raise Exception("boom!")

        def talk_with_self(self):
            return self.actor_ref.proxy().functional_hello("from the future")

    return ActorA


@pytest.fixture
def events():
    class Events:
        on_start_was_called = threading.Event()
        on_stop_was_called = threading.Event()
        on_failure_was_called = threading.Event()
        greetings_was_received = threading.Event()
        actor_registered_before_on_start_was_called = threading.Event()

    return Events()


@pytest.fixture
def proxy(actor_class, events):
    proxy = actor_class.start(events).proxy()
    yield proxy
    proxy.stop()


def test_functional_method_call_returns_correct_value(proxy):
    assert proxy.functional_hello("world").get() == "Hello, world!"
    assert proxy.functional_hello("moon").get() == "Hello, moon!"


# 可观察
# fixme 访问方法 返回的future.
def test_side_effect_of_method_call_is_observable(proxy):
    assert proxy.cat.get() == "dog"
    # set cat {'callable': True, 'traversable': False}
    # ThreadingFuture; actor_ref.ask()
    future = proxy.set_cat("eagle")
    assert future.get() is None
    assert isinstance(proxy.cat, ThreadingFuture)
    assert proxy.cat.get() == "eagle"


def test_call_to_unknown_method_raises_attribute_error(proxy):
    """
    CallableProxy::defer
    :param proxy:
    :return:
    """
    # 触发代码片段.
    # if attr_info is None:
    #     raise AttributeError('{} has no attribute {!r}'.format(self, name))
    # will this snippet.
    with pytest.raises(AttributeError) as exc_info:
        proxy.unknown_method()
