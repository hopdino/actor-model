"""
对第二章test 文件的扩充测试方法
"""
import pytest
from ..actor_register import ActorRegistry


@pytest.fixture(scope="module")
def actor_class(runtime):
    # also, use ThreadingActor directly.
    class CustomThreadingActor(runtime.actor_class):
        pass

    return CustomThreadingActor


def test_actor_start_already_registered(actor_class):
    actor_ref = actor_class().start()
    assert len(ActorRegistry.get_all()) == 1
    assert actor_ref in ActorRegistry.get_all()
    ActorRegistry.stop_all()


def test_register_get_by_filter(actor_class):
    actor_ref = actor_class().start()
    # 已经完成注册啦了.
    # step1 测试 urn查询
    assert ActorRegistry.get_by_urn(actor_ref.actor_urn) == actor_ref
    # # step2 测试类名查询
    assert ActorRegistry.get_by_class(actor_ref.actor_class)[0] == actor_ref
    assert actor_ref in ActorRegistry.get_by_class_name('CustomThreadingActor')
    # # # step3 测试类名字符查询
    ActorRegistry.stop_all()


def test_register_stop_all(actor_class):
    """
    终止所有的actor
    :param actor_class:
    :return:
    """
    actor_class().start()
    assert ActorRegistry.stop_all()

