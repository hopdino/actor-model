"""
这个模块比较牵涉注册和广播.
注册Register alive的actor
把所有的running actor 放到一个列表里

notes:
-----
register list
register and unregister 常使用list or dict 来保持注册的对象, 这里使用list.
以后根据场景选择适合业务的
"""

import threading

__all__ = ['ActorRegistry']


class ActorRegistry:
    """
    注册所有正在运行的actor.
    """
    # protected attribute
    # _member is protected
    # __member is private
    _actor_refs = []  # register  list, by the way , you can use dict instead.
    _actor_refs_lock = threading.RLock()

    @classmethod
    def broadcast(cls, message, target_class=None):
        """
        给所有注册的actor广播消息.
        """
        if isinstance(target_class, str):
            targets = cls.get_by_class_name(target_class)
        elif target_class is not None:
            targets = cls.get_by_class(target_class)

        else:
            # 广播给all actors.
            targets = cls.get_all()

        for ref in targets:
            ref.tell(message)

    @classmethod
    def get_by_class_name(cls, actor_class_name):
        """
        Get :class:`ActorRef` for all running actors of the given class
        name.
        :returns: list of :class:`pykka.ActorRef`
        """
        with cls._actor_refs_lock:
            return [
                ref for ref in cls._actor_refs
                if ref.actor_class.__name__ == actor_class_name
            ]

    @classmethod
    def get_by_class(cls, actor_class):
        """
        :param actor_class:
        :return:
        :type list
        """
        with cls._actor_refs_lock:
            return [
                ref for ref in cls._actor_refs
                if issubclass(ref.actor_class, actor_class)
            ]


    @classmethod
    def get_by_urn(cls, actor_urn):
        """
        Get an actor by its universally unique URN.
        :param actor_urn: actor URN
        :type actor_urn: string
        :returns: :class:`pykka.ActorRef` or :class:`None` if not found
        :type list
        test test_register_get_by_filter
        """
        with cls._actor_refs_lock:
            refs = [
                ref for ref in cls._actor_refs if ref.actor_urn == actor_urn
            ]
            if refs:
                return refs[0]

    @classmethod
    def get_all(cls):
        with cls._actor_refs_lock:
            return cls._actor_refs[:]

    @classmethod
    def register(cls, actor_ref):
        with cls._actor_refs_lock:
            cls._actor_refs.append(actor_ref)

    @classmethod
    def unregister(cls, actor_ref):
        """
        Remove an actor ref from the registry.

        :param actor_ref: reference to the actor to unregister
        :type actor_ref: :class:`pykka.ActorRef`
        """
        with cls._actor_refs_lock:
            if actor_ref in cls._actor_refs:
                cls._actor_refs.remove(actor_ref)

    @classmethod
    def stop_all(cls, block=True, timeout=True):
        """
         Stop all running actors.
        LIFO 队列. last started, first stopped.
        :param block:
        :param timeout:
        :return: [Ture, False]
        :type: list
        """
        return [ref.stop(block, timeout) for ref in reversed(cls.get_all())]
