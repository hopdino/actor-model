import uuid

import pytest
from pykka import ActorDeadError
from ..actor import Actor
from ..actor_register import ActorRegistry
from ..threading import ThreadingActor


@pytest.fixture(scope="module")
def actor_class():
    class ActorA(ThreadingActor):
        def __init__(self, events):
            super().__init__()
            self.events = events

        def on_start(self):
            self.events.on_start_was_called.set()
            if ActorRegistry.get_by_urn(self.actor_urn) is not None:
                self.events.actor_registered_before_on_start_was_called.set()

        def on_stop(self):
            self.events.on_stop_was_called.set()

        def on_failure(self, *args):
            self.events.on_failure_was_called.set()

        def on_receive(self, message):
            if message.get("command") == "raise exception":
                raise Exception("foo")
            elif message.get("command") == "raise base exception":
                raise BaseException()
            elif message.get("command") == "stop twice":
                self.stop()
                self.stop()
            elif message.get("command") == "message self then stop":
                self.actor_ref.tell({"command": "greetings"})
                self.stop()
            elif message.get("command") == "greetings":
                self.events.greetings_was_received.set()
            elif message.get("command") == "callback":
                message["callback"]()
            else:
                super().on_receive(message)

    return ActorA


@pytest.fixture(scope='session')
def custom_actor_class():
    class ActorB(ThreadingActor):
        pass

    return ActorB


@pytest.fixture
def actor_ref(actor_class, events):
    ref = actor_class.start(events)
    yield ref
    ref.stop()


# teardown

@pytest.fixture
def actor_ref_B(custom_actor_class):
    """
    Pytest 使用 yield 关键词将固件分为两部分，yield 之前的代码属于预处理，会在测试前执行；yield 之后的代码属于后处理，将在测试完成后执行。

    并且全部用例执行完之后，yield呼唤teardown操作,即
    在测试完成后呼叫相应的代码 会执行yield 后面的代码
    pytest 内部有个方法: _teardown_yield_fixture
    # Notes: https://learning-pytest.readthedocs.io/zh/latest/doc/fixture/setup-and-teardown.html
    :param custom_actor_class:

    :return:
    """
    ref = custom_actor_class.start()
    # todo https://www.cnblogs.com/yoyoketang/p/9401554.html
    yield ref
    ref.stop()


# 测试是否为uuid version 4.
def test_actor_has_an_uuid4_based_urn(actor_ref_B):
    assert uuid.UUID(actor_ref_B.actor_urn).version == 4
    # fixme 开启会产生问题.
    # ActorRegistry.stop_all()


# 测试
def test_actor_not_implemented_actor_baseclass():
    with pytest.raises(NotImplementedError):
        actor_ref = Actor().start()
        actor_ref.stop()


# 测试unique 唯一性
def test_actor_has_unique_urn(custom_actor_class):
    actor_refs = [custom_actor_class.start() for _ in range(3)]
    assert actor_refs[0].actor_urn != actor_refs[1].actor_urn
    assert actor_refs[1].actor_urn != actor_refs[2].actor_urn
    assert actor_refs[2].actor_urn != actor_refs[0].actor_urn
    ActorRegistry.stop_all()


def test_str_on_raw_actor_contains_actor_class_name(custom_actor_class):
    assert custom_actor_class().__class__.__name__ in str(custom_actor_class)
    ActorRegistry.stop_all()


# 参数初始化测试
def test_init_can_be_called_with_some_arguments(custom_actor_class):
    custom_actor_class.start(1, 2, 3, foo='bar')



# see code on_start & actor loop
def test_on_start_is_called_before_message_is_processed(actor_ref, events):
    # 阻塞5s
    events.on_start_was_called.wait(2)
    # 如果被调用 set()被调用 flag= true
    assert events.on_start_was_called.is_set()


@pytest.fixture(scope="module")
def early_stopping_actor_class(runtime):
    class EarlyStoppingActor(runtime.actor_class):
        def __init__(self, events):
            super().__init__()
            self.events = events

        def on_start(self):
            # actor_loop 在开始前处理信箱 发生停止
            # Stop the actor.
            self.stop()
            # tell -_actorStop

        def on_stop(self):
            # _stop[_handle receive] will call on_stop method
            #  *before* the actor stops.
            # is_set() 阻塞拦截的地方可以通行.
            self.events.on_stop_was_called.set()

    return EarlyStoppingActor


# actor_ref 是否 alive.
def test_on_start_can_stop_actor(early_stopping_actor_class, events):
    actor_ref = early_stopping_actor_class.start(events)
    # 使執行緒組塞，直到flag值為True
    # 此时阻塞，直达flag=true 或则timeout.
    events.on_stop_was_called.wait(2)  # 短暂的sleep. blocking in here 2s.
    assert events.on_stop_was_called.is_set()
    assert not actor_ref.is_alive()

# fixme
def test_messages_left_in_queue_after_stop_actor_receive_an_error(runtime, actor_ref):
    """
    消息还处在handle_receive 阶段有个wait 阻塞.
    :param runtime:
    :param actor_ref:
    :return:
    """

    event = runtime.event_class()
    # put envelop in inbox.
    actor_ref.tell({"command": "callback", "callback": event.wait})
    # 消息还在handle_receive 等待呢.
    # stop actor. stopped before handling the message
    actor_ref.stop(block=False)  # stop actor instance
    response = actor_ref.ask({"command": "irrelevant"}, block=False)
    event.set()
    # eror: stopped before handling the message
    with pytest.raises(ActorDeadError):
        response.get(timeout=5)


# fixme
def test_stop_requests_left_in_queue_after_actor_stops_are_handled(runtime, actor_ref):
    """
    如果停止, 处理被阻塞在路上的消息.
    """
    event = runtime.event_class()
    actor_ref.tell({"command": "callback", "callback": event.wait})
    response = actor_ref.stop(block=False)
    ActorRegistry.stop_all()
    event.set()
    # assert response.get(timeout=1)


# 这几个还是比较简单理解的.
def test_on_start_is_called_before_first_message_is_processed(actor_ref, events):
    """
    on_start 被调用 custom on_hook()
    :param actor_ref:
    :param events:
    :return:
    """
    events.on_start_was_called.wait(10)
    assert events.on_start_was_called.is_set()

# 测试注册后调用 on_start callback
def test_on_start_is_called_after_the_actor_is_registered(actor_ref, events):
    events.on_start_was_called.wait(5)
    assert events.on_start_was_called.is_set()

    # equivalent to sleep(0.5)
    events.actor_registered_before_on_start_was_called.wait(1)
    assert events.actor_registered_before_on_start_was_called.is_set()


def test_on_start_can_stop_actor_before_receive_loop_is_started(
        early_stopping_actor_class, events
):
    actor_ref = early_stopping_actor_class.start(events)

    events.on_stop_was_called.wait(1)
    assert events.on_stop_was_called.is_set()
    assert not actor_ref.is_alive()


# 在处理消息前失败, actor应该主动去关闭 stop actor.
def test_on_start_failure_causes_actor_to_stop(early_stopping_actor_class, events):
    # Actor should not be alive if on_start fails.
    # start 失败的时候, 应该stop actor。
    actor_ref = early_stopping_actor_class.start(events)
    events.on_stop_was_called.wait(2)
    actor_ref.actor_stopped.wait(2)
    assert not actor_ref.is_alive()  # dead
