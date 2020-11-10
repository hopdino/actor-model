"""
"""
from typing import Dict
from collections.abc import Callable
from . import messages
from .exceptions import ActorDeadError


class ActorProxy:
    actor_ref = None

    def __init__(self, actor_ref, attr_path=None):
        if not actor_ref.is_alive():
            raise ActorDeadError('{} not found'.format(actor_ref))
        self.actor_ref = actor_ref
        self._actor = actor_ref._actor
        self._attr_path = attr_path or tuple()  # tuple type
        self._known_attrs = self._introspect_attributes()  # 自声3
        self._actor_proxies = {}
        self._callable_proxies = {}  # 可 调用

    def _introspect_attributes(self):
        """Introspects the actor's attributes."""
        result = {}
        attr_paths_to_visit = [[attr_name] for attr_name in dir(self._actor)]

        while attr_paths_to_visit:
            # 1 私有属性排除
            attr_path = attr_paths_to_visit.pop(0)
            # todo attr_path  tuple
            if not self._is_exposable_attribute(attr_path[-1]):
                continue

            # 如果是actor属性
            attr = self._actor._introspect_attribute_from_path(attr_path)
            if self._is_self_proxy(attr):
                continue
            # 属性考虑到callable 和可遍历.
            traversable = self._is_traversable_attribute(attr)
            result[tuple(attr_path)] = {
                'callable': self._is_callable_attribute(attr),
                'traversable': traversable,
            }

            if traversable:
                for attr_name in dir(attr):
                    attr_paths_to_visit.append(attr_path + [attr_name])

        return result

    def _is_exposable_attribute(self, attr_name):
        """
        Returns true for any attribute name that may be exposed through
        :class:`ActorProxy`.
        """
        return not attr_name.startswith('_')

    def _is_self_proxy(self, attr):
        """Returns true if attribute is an equivalent actor proxy."""
        return attr == self

    def _is_callable_attribute(self, attr):
        """Returns true for any attribute that is callable."""
        return isinstance(attr, Callable)

    def _is_traversable_attribute(self, attr):
        """
        Returns true for any attribute that may be traversed from another
        actor through a proxy.
        """
        return (
                getattr(attr, '_pykka_traversable', False) is True
                or getattr(attr, 'pykka_traversable', False) is True
        )

    def __eq__(self, other):
        if not isinstance(other, ActorProxy):
            return False
        if self._actor != other._actor:
            return False
        if self._attr_path != other._attr_path:
            return False
        return True

    def __hash__(self):
        return hash((self._actor, self._attr_path))

    def __repr__(self):
        return '<ActorProxy for {}, attr_path={!r}>'.format(
            self.actor_ref, self._attr_path
        )

    def __dir__(self):
        result = ['__class__']
        result += list(self.__class__.__dict__.keys())
        result += list(self.__dict__.keys())
        result += [attr_path[0] for attr_path in list(self._known_attrs.keys())]
        return sorted(result)

    def __getattr__(self, name):
        """Get a field or callable from the actor.
        Notes: 访问属性 返回的是future对象.
        :return future of ThreadingFuture
        """

        attr_path = self._attr_path + (name,)

        if attr_path not in self._known_attrs:
            self._known_attrs = self._introspect_attributes()

        attr_info = self._known_attrs.get(attr_path)
        if attr_info is None:
            raise AttributeError('{} has no attribute {!r}'.format(self, name))

        if attr_info['callable']:
            if attr_path not in self._callable_proxies:
                self._callable_proxies[attr_path] = CallableProxy(
                    self.actor_ref, attr_path
                )
            return self._callable_proxies[attr_path]
        elif attr_info['traversable']:
            if attr_path not in self._actor_proxies:
                self._actor_proxies[attr_path] = ActorProxy(
                    self.actor_ref, attr_path
                )
            return self._actor_proxies[attr_path]
        else:
            message = messages.ProxyGetAttr(attr_path=attr_path)
            return self.actor_ref.ask(message, block=False)

    def __setattr__(self, name, value):
        """
        Set a field on the actor.

        Blocks until the field is set to check if any exceptions was raised.
        :return future of ThreadingFuture
        """
        if name == 'actor_ref' or name.startswith('_'):
            return super(ActorProxy, self).__setattr__(name, value)
        attr_path = self._attr_path + (name,)
        message = messages.ProxySetAttr(attr_path=attr_path, value=value)
        return self.actor_ref.ask(message)


class CallableProxy:
    """Proxy to a single method.
    留意 .ask .tell 的返回类型.
    Example::

        proxy = AnActor.start().proxy()
        future = proxy.do_work()
    """

    def __init__(self, actor_ref, attr_path):
        self.actor_ref = actor_ref
        self._attr_path = attr_path

    def __call__(self, *args, **kwargs):
        message = messages.ProxyCall(
            attr_path=self._attr_path, args=args, kwargs=kwargs
        )
        return self.actor_ref.ask(message, block=False)

    def defer(self, *args, **kwargs):
        message = messages.ProxyCall(
            attr_path=self._attr_path, args=args, kwargs=kwargs
        )
        return self.actor_ref.tell(message)


def traversable(obj):
    if hasattr(obj, '__slots__'):
        raise Exception(
            'pykka.traversable() cannot be used to mark '
            'an object using slots as traversable.'
        )
    obj._pykka_traversable = True
    return obj
