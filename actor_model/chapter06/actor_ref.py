"""
safe manner
Proxy pattern: 代理可以为这个实体提供一个替代者，来控制它的访问权限和访问内容。
"""

from pykka import ActorDeadError

from .actor_proxy import ActorProxy
from .envelope import Envelope
from .messages import _ActorStop


class ActorRef:
    """
    对 正在running actor的引用(running state 才会有一些属性和方法)
    Reference to a running actor(可以理解对actor的包裹一层)
    :param actor: the actor to wrap
    """
    #: The class of the referenced actor.
    actor_class = None

    #: See :attr:`Actor.actor_urn`.
    actor_urn = None

    #: See :attr:`Actor.actor_inbox`.
    actor_inbox = None

    #: See :attr:`Actor.actor_stopped`.
    actor_stopped = None

    def __init__(self, actor):
        self._actor = actor
        self.actor_class = actor.__class__
        self.actor_urn = actor.actor_urn
        self.actor_inbox = actor.actor_inbox
        self.actor_stopped = actor.actor_stopped

    def __repr__(self):
        return f"<ActorRef for {self}>"

    def __str__(self):
        return f"{self.actor_class.__name__} ({self.actor_urn})"

    def is_alive(self):
        """
        check if actor is alive.
        stopped flat set() is_set()
        :return:
        """
        return not self.actor_stopped.is_set()

    # put letter into envelop
    def tell(self, message):
        """
         Send message to actor without waiting for any response.
         投递后 不需要等待是否有回复.
        :param message:
        :return:
        """
        if not self.is_alive():
            raise ActorDeadError(f"{self} not found")
        self.actor_inbox.put(Envelope(message))

    def ask(self, message, block=True, timeout=None):
        """
         Send message to actor and wait for the reply.
         一直等待消息回复.(显示符合future 特性 in the future. 异步)
        :param message:
        :param block:
        :param timeout:
        :return: it will immediately return a Future
        """

        future = self.actor_class._create_future()

        try:
            if not self.is_alive():
                raise ActorDeadError(f"{self} not found")
        except ActorDeadError:
            pass
        else:
            # todo reply_to  future.
            self.actor_inbox.put(Envelope(message, reply_to=future))

        if block:
            return future.get(timeout=timeout)
        else:
            return future

    def __enter__(self):
        """
        nothing.
        :return:
        """
        print("actor has started...")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        自动退出
        :return:
        """
        print("stop actor ....")
        self.stop(block=True, timeout=None)


    def stop(self, block=True, timeout=None):

        # 闭包 您可以使用内部函数来保护它们免受函数外部发生的一切影响，这意味着它们在全局范围内是隐藏的。
        # 最佳实践是 下划线开头 protected
        # Notes: https://realpython.com/inner-functions-what-are-they-good-for/
        # {scope}

        ask_future = self.ask(_ActorStop(), block=False)

        def _stop_result_converter(timeout):
            try:
                ask_future.get(timeout=timeout)
                return True
            except ActorDeadError:
                return False

        converted_future = ask_future.__class__()
        # Set a function to be executed
        converted_future.set_get_hook(_stop_result_converter)

        if block:
            return converted_future.get(timeout=timeout)
        else:
            return converted_future

    def proxy(self):
        """
        Wraps the :class:`ActorRef` in an :class:`ActorProxy
        代理对象actor 必须是alive && available（代理'活人'）
        :return: ActorProxy instance
        """
        return ActorProxy(self)
