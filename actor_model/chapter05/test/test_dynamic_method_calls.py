import pytest
from pykka import ThreadingActor, ActorRegistry


@pytest.fixture(scope="module")
def actor_class():
    class ActorA(ThreadingActor):
        def add_method(self, name):
            setattr(self, name, lambda: "returned by " + name)

        def use_foo_through_self_proxy(self):
            return self.actor_ref.proxy().foo()

    return ActorA


@pytest.fixture
def stop_all():
    yield
    ActorRegistry.stop_all()


@pytest.fixture
def proxy(actor_class):
    proxy = actor_class.start().proxy()
    yield proxy
    proxy.stop()


def test_can_call_method_that_was_added_at_runtime(proxy):
    """
    允许时添加属性方法.
    :param proxy:
    :return:
    """
    proxy.add_method("foo").get()

    assert proxy.foo().get() == "returned by foo"


def test_can_proxy_itself_add_use_attrs_added_at_runtime(proxy):

    proxy.add_method("foo")
    # self_proxy
    outer_future = proxy.use_foo_through_self_proxy()
    inner_future = outer_future.get(timeout=1)
    result = inner_future.get(timeout=1)
    assert result == "returned by foo"


