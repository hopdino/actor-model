"""
有关属性的代理访问.
"""
import pytest
from ..threading import ThreadingActor


@pytest.fixture
def actor_class():
    class ActorWithProperties(ThreadingActor):
        an_attr = "an_attr"
        _private_attr = "secret"

        @property
        def a_ro_property(self):
            return "a_ro_property"

        # a_rw_property
        # todo ?
        _a_rw_property = "a_rw_property"

        @property
        def a_rw_property(self):
            return self._a_rw_property

        @a_rw_property.setter
        def a_rw_property(self, value):
            self._a_rw_property = value

    return ActorWithProperties


@pytest.fixture
def proxy(actor_class):
    proxy = actor_class.start().proxy()
    yield proxy
    proxy.stop()


def test_attr_can_be_read_using_get_postfix(proxy):
    assert proxy.an_attr.get() == "an_attr_value"
    proxy.stop()


def test_attr_can_be_set_using_assignment(proxy):
    assert proxy.an_attr.get() == "an_attr"
    # will call __set__
    proxy.an_attr = "an_attr_2"
    assert proxy.an_attr.get() == "an_attr_2"


def test_private_attr_access_raises_exception(proxy):

    # _is_exposable_attribute method exclude startswith('_')
    with pytest.raises(AttributeError) as exc_info:
        proxy._private_attr.get()

    assert "has no attribute '_private_attr'" in str(exc_info.value)


def test_missing_attr_access_raise_exception(proxy):
    """
    知识点: 如何处理不存在的属性访问.
    Notes : Using the Python defaultdict Type for Handling Missing Keys
    https://realpython.com/python-defaultdict/
    :param proxy:
    :return:
    """
    with pytest.raises(AttributeError) as exc_info:
        proxy.missing_attr.get()

    assert "has no attribute 'missing_attr'" in str(exc_info.value)


# 属性访问测试
def test_property_can_be_read_using_get_postfix(proxy):
    assert proxy.a_ro_property.get() == "a_ro_property"
    assert proxy.a_rw_property.get() == "a_rw_property"


# property setter method,
def test_property_can_be_set_using_assignment(proxy):
    proxy.a_rw_property = "a_rw_property_2"

    assert proxy.a_rw_property.get() == "a_rw_property_2"


# 属性没有定义set,不应许给属性赋值.
def test_read_only_property_cannot_be_set(proxy):
    """
    property has no setter decorator.
    :param proxy:
    :return:
    """
    with pytest.raises(AttributeError):
        proxy.a_ro_property = "a_ro_property_2"


# 创建代理的时候属性并不访问.
def test_property_is_not_accessed_when_creating_proxy():

    class ExpensiveSideEffectActor(ThreadingActor):
        @property
        def a_property(self):
            # 如果读取会触发异常.
            raise Exception("Proxy creation accessed property")

    actor_ref = ExpensiveSideEffectActor.start()
    try:
        actor_ref.proxy()
    finally:
        actor_ref.stop()




