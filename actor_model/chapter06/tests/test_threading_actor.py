import threading

import pytest

from ..threading import ThreadingActor


class RegularActor(ThreadingActor):
    pass


class DaemonActor(ThreadingActor):
    # 守护进程
    use_daemon_thread = True


@pytest.fixture
def regular_actor_ref():
    ref = RegularActor.start()
    yield ref
    ref.stop()


@pytest.fixture
def daemon_actor_ref():
    ref = DaemonActor.start()
    yield ref
    ref.stop()


def test_actor_thread_is_named(regular_actor_ref):
    alive_threads = threading.enumerate()

    alive_thread_names = [t.name for t in alive_threads]
    named_correctly = [
        name.startswith(RegularActor.__name__) for name in alive_thread_names
    ]
    # [False, True]
    assert any(named_correctly)


def test_actor_thread_is_not_damon_by_default(regular_actor_ref):
    alive_threads = threading.enumerate()
    actor_threads = [
        t for t in alive_threads if t.name.startswith("RegularActor")
    ]
    assert len(actor_threads) == 1
    assert not actor_threads[0].daemon


def test_actor_thread_is_daemonic_if_use_daemon_thread_flag_is_set(daemon_actor_ref):
    alive_threads = threading.enumerate()
    actor_threads = [
        t for t in alive_threads if t.name.startswith("DaemonActor")
    ]

    assert len(actor_threads) == 1
    assert actor_threads[0].daemon
