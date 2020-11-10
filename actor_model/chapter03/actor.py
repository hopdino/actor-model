"""
--------------------
|Actor --> ActorRef |->ActorProxy
--------------------
"""

import threading
import uuid

from .actor_ref import ActorRef
from . import messages
from . import ActorRegistry

__all__ = ["Actor"]


class Actor:
    """
    Actor base class
    ThreadingActor 继承此基类。
    """

    @classmethod
    def start(cls, *args, **kwargs):
        """
        启动actor和注册actor
        steps:
         step1 -- actor created.
         step2 -- registered actor.
         step3 -- receive loop by thread.
         step4 -- 返回 actor_ref 对象.

        test: test_actor_start_already_registered
        """

        obj = cls(*args, **kwargs)  # init()
        ActorRegistry.register(obj.actor_ref)
        # actor_ref for safely communicating with the actor.
        obj._start_actor_loop()
        return obj.actor_ref

    # 由继承的类来实现具体的方法
    @staticmethod
    def _create_actor_inbox():
        raise NotImplementedError

    @staticmethod
    def _create_future():
        raise NotImplementedError

    def _start_actor_loop(self):
        raise NotImplementedError

    #: The actor URN string is a universally unique identifier for the actor.
    #: It may be used for looking up a specific actor using
    #: :meth:`ActorRegistry.get_by_urn`.
    # actor唯一编号
    actor_urn = None

    #: The actor's inbox. Use :meth:`ActorRef.tell`, :meth:`ActorRef.ask`, and
    #: friends to put messages in the inbox.
    # 信箱(mesage->envelop-->inbox-->queue)
    actor_inbox = None

    #: The actor's :class:`ActorRef` instance.
    # 对actor的引用.
    actor_ref = None

    #: A :class:`threading.Event` representing whether or not the actor should
    #: continue processing messages. Use :meth:`stop` to change it.
    actor_stopped = None

    def __init__(self, *args, **kwargs):
        # Notes: 统一资源名称 https://zh.wikipedia.org/wiki/%E7%BB%9F%E4%B8%80%E8%B5%84%E6%BA%90%E5%90%8D%E7%A7%B0
        self.actor_urn = uuid.uuid4().urn
        self.actor_inbox = self._create_actor_inbox()
        self.actor_stopped = threading.Event()
        # access the actor in a safe manner
        # 更安全的访问actor
        self.actor_ref = ActorRef(self)

    def __str__(self):
        return "{} ({})".format(self.__class__.__name__, self.actor_urn)

    def stop(self):
        """
        Stop the actor.
        停止actor,可以call Actor.stop() or ActorRef.stop().
        """
        self.actor_ref.tell(messages._ActorStop())

    def _stop(self):
        """
        Stops the actor immediately without processing the rest of the inbox.
        """
        ActorRegistry.unregister(self.actor_ref)
        self.actor_stopped.set()  # 线程通知事件
        try:
            self.on_stop()
        except Exception:
            pass

    def _actor_loop(self):
        """
        The actor's event loop.
        1. 从信箱来出信件
        2. 判断信件的类型
        3. 获得消息 reply to future(对回复信箱的管理类)
        :return:
        """
        try:
            self.on_start()
        except Exception:
            pass
        # 线程等待阻塞等待
        while not self.actor_stopped.is_set():
            envelope = self.actor_inbox.get()
            try:
                response = self._handle_receive(envelope.message)
                if envelope.reply_to is not None:
                    # 把处理的message 聚类
                    # reply to future
                    envelope.reply_to.set(response)
            except Exception:
                pass
            except BaseException:
                self._stop()
                ActorRegistry.stop_all()

        # 信箱非空情况 坏死的邮件处理.
        while not self.actor_inbox.empty():
            envelope = self.actor_inbox.get()
            if envelope.reply_to is not None:
                if isinstance(envelope.message, messages._ActorStop):
                    envelope.reply_to.set(None)

    # on_ 一般表示事件, 当事件发生的时候来处理.
    def on_start(self):
        """启动事件: 在开始处理接收到信箱触发 类似有点回调函数的味道"""
        pass

    def on_stop(self):
        pass

    def on_receive(self, message):
        pass

    def _handle_receive(self, message):
        """Handles messages sent to the actor.
        三种不同类型的消息
        """
        # todo upgrade internal message implement
        message = messages._upgrade_internal_message(message)
        if isinstance(message, messages._ActorStop):
            return self._stop()

        if isinstance(message, messages.ProxyCall):
            callee = self._get_attribute_from_path(message.attr_path)
            return callee(*message.args, **message.kwargs)

        if isinstance(message, messages.ProxyGetAttr):
            attr = self._get_attribute_from_path(message.attr_path)
            return attr

        if isinstance(message, messages.ProxySetAttr):
            parent_attr = self._get_attribute_from_path(message.attr_path[:-1])
            attr_name = message.attr_path[-1]
            return setattr(parent_attr, attr_name, message.value)
        return self.on_receive(message)

    def _get_attribute_from_path(self, attr_path):
        """
        :param attr_path: tuple()
        :return:
        """
        attr = self
        for attr_name in attr_path:
            # 返回一个对象属性值, 如果是2个以上 就有继承关系了.
            attr = getattr(attr, attr_name)
        return attr

    def _introspect_attribute_from_path(self, attr_path):
        """
        自省
        Get attribute information from ``__dict__`` on the container.
        :param attr_path: tuple
        """
        if not attr_path:
            return self
        # 类中的属性还有子属性(a(a.foo))Notes see test suit code.
        parent = self._get_attribute_from_path(attr_path[:-1])
        parent_attrs = self._introspect_attributes(parent)
        attr_name = attr_path[-1]

        try:
            return parent_attrs[attr_name]
        except KeyError:
            pass

    def _introspect_attributes(self, obj):
        """收集当前和继承的所有类的__dict__
        Combine ``__dict__`` from ``obj`` and all its superclasses.
        :return dict
        """
        result = {}
        for cls in reversed(obj.__class__.mro()):
            result.update(cls.__dict__)
        if hasattr(obj, "__dict__"):
            result.update(obj.__dict__)
        return result
