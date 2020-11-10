import asyncio

import pytest
from pykka import ThreadingFuture

from .future import Future, get_all

pytest.fixture(scope='module')


@pytest.fixture
def future():
    return ThreadingFuture()


@pytest.fixture
def futures():
    return [ThreadingFuture() for _ in range(3)]


def test_base_future_get_is_not_implemented():
    future = Future()

    with pytest.raises(NotImplementedError):
        future.get()


def test_base_future_set_is_not_implemented():
    future = Future()

    with pytest.raises(NotImplementedError):
        future.set(None)


def test_set_multiple_times_fails(future):
    future.set(0)
    # maxsize=1 queue.Full
    with pytest.raises(Exception):
        future.set(0)


def test_get_all_blocks_until_all_futures_are_available(futures):
    futures[0].set(0)
    futures[1].set(1)
    futures[2].set(2)

    result = get_all(futures)
    assert result == [0, 1, 2]


def test_get_all_can_be_called_multiple_times(futures):
    futures[0].set(0)
    futures[1].set(1)
    futures[2].set(2)
    result1 = get_all(futures)
    result2 = get_all(futures)

    assert result1 == result2


def test_future_nested_future(future):
    inner_future = ThreadingFuture()
    inner_future.set("foo")
    outer_future = ThreadingFuture()
    outer_future.set(inner_future)
    assert outer_future.get().get() == "foo"


# 协程 python3.6
def run_async(coroutine):
    loop = asyncio.get_event_loop()
    f = asyncio.ensure_future(coroutine, loop=loop)
    return loop.run_until_complete(f)


def test_future_supports_yield_from_syntax(future):
    def get_value():
        val = yield from future
        return val

    future.set(1)
    assert run_async(get_value()) == 1


def test_filter_excludes_items_not_matching(future):
    filtered = future.filter(lambda x: x > 10)
    future.set([1, 3, 5, 7, 9, 11, 13, 15, 17, 19])
    assert filtered.get() == [11, 13, 15, 17, 19]


def test_filter_object_is_not_iterable(future):
    filtered = future.filter(lambda x: x > 10)
    future.set(3)  # int 3 is not iterable object.

    with pytest.raises(TypeError):
        filtered.get(timeout=0)


def test_filter_reuses_result_if_called_multiple_times(future, mocker):
    raise_on_reuse_func = mocker.Mock(side_effect=[False, True, Exception])
    filtered = future.filter(raise_on_reuse_func)
    future.set([1, 2])
    assert filtered.get(timeout=0) == [2]
    assert filtered.get(timeout=0) == [2]  # First result is reused
    assert filtered.get(timeout=0) == [2]  # First result is reused


def test_join_multiple_futures(futures):
    joined = futures[0].join(futures[1], futures[2])
    futures[0].set(0)
    futures[1].set(1)
    futures[2].set(2)

    assert joined.get(timeout=0) == [0, 1, 2]


def test_map_returns_future_which_passes_result_through_func(future):
    mapped = future.map(lambda x: x + 10)
    future.set(30)

    assert mapped.get(timeout=0) == 40


def test_map_works_on_dict(future):
    # twice call get
    mapped = future.map(lambda x: x['foo'])
    future.set({"foo": "bar"})
    assert mapped.get(timeout=1) == 'bar'
