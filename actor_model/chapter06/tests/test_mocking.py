from collections.abc import Callable

import pytest
from ..threading import ThreadingActor
from ..actor_register import ActorRegistry


@pytest.fixture
def actor_class():
    class ActorForMocking(ThreadingActor):
        _a_rw_property = "a_rw_property"

        @property
        def a_rw_property(self):
            return self._a_rw_property

        @a_rw_property.setter
        def a_rw_property(self, value):
            self._a_rw_property = value

        def a_method(self):
            raise Exception("This method should be mocked")

    return ActorForMocking


@pytest.fixture
def proxy(actor_class):
    proxy = actor_class.start().proxy()
    yield proxy
    proxy.stop()


@pytest.fixture
def stop_all():
    yield
    ActorRegistry.stop_all()


def test_actor_with_mocked_method_works(actor_class, stop_all, mocker):
    # return method
    mock = mocker.MagicMock(return_value="mocked method return")
    # # patch
    # # Notes: https://pypi.org/project/pytest-mock/
    mocker.patch.object(actor_class, "a_method", new=mock)
    # # actor -> ref -> proxy -> future.
    proxy = actor_class.start().proxy()
    assert proxy.a_method().get() == "mocked method return"
    assert mock.call_count == 1


def test_actor_with_callable_mock_property_does_not_work(actor_class, stop_all, mocker):
    # Notes: https://stackoverflow.com/questions/17181687/mock-vs-magicmock
    mock = mocker.Mock()
    mock.__get__ = mocker.Mock(return_value="mocked property value")

    assert isinstance(mock, Callable)

    actor_class.a_rw_property = mock
    proxy = actor_class.start().proxy()

    with pytest.raises(AttributeError) as exc_info:
        assert proxy.a_rw_property.get()
        assert "'CallableProxy' object has no attribute 'get'" in str(
            exc_info.value
        )
