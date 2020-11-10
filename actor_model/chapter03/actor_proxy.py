"""
"""
from typing import Dict
from collections.abc import Callable, Iterable
from pykka import ActorDeadError
from . import messages


class ActorProxy:
    actor_ref = None

    def __init__(self, actor_ref, attr_path=None):
        if not actor_ref.is_alive():
            raise ActorDeadError('{} not found'.format(actor_ref))

        self.actor_ref = actor_ref
        self._actor = actor_ref._actor
        self._attr_path = attr_path or tuple()  # tuple type
        self._known_attrs = self._introspect_attributes()  # 自省
        self._actor_proxies = {}
        self._callable_proxies = {}  # 可调用

    def _is_exposable_attribute(self, attr_name):
        """
        Returns true for any attribute name that may be exposed through
        :class:`ActorProxy`.
        """

        return not attr_name.startswith('_')

    def _is_self_proxy(self, attr):
        return attr == self

    def _is_callable_attribute(self, attr):
        """Returns true for any attribute that is callable."""
        return isinstance(attr, Callable)

    def _introspect_attributes(self) -> Dict:
        """
        初始化先获得自省的属性信息
        attr_info: 属性信息{(foo,):{'callable': False, 'traversable':False }}
        :return: dict
        """
        result = {}

        attr_paths_to_visit = [[attr_name] for attr_name in dir(self._actor)]
        while attr_paths_to_visit:
            # 1 私有属性排除
            attr_path = attr_paths_to_visit[0]
            # todo attr_path type ? list or tuple
            if not self._is_exposable_attribute(attr_path[-1]):
                continue
            # 如果是actor属性
            attr = self._actor._introspect_attribute_from_path(attr_path)

            if self._is_self_proxy(attr):
                continue
            traversable = self._is_traversable_attribute(attr)
            # 属性考虑到callable 和可遍历.
            result[tuple(attr_path)] = {
                'callable': self._is_callable_attribute(attr),
                'traversable': traversable,
            }

            if traversable:
                for attr_name in dir(attr):
                    attr_paths_to_visit.append(attr_path + [attr_name])

            return result

    def __getattr__(self, name):
        """
        属性访问
        :param name:
        :return:
        """
        # tuple
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
            # 又一个代理
            if attr_path not in self._actor_proxies:
                self._actor_proxies[attr_path] = ActorProxy(
                    self.actor_ref, attr_path
                )
            return self._actor_proxies[attr_path]

        else:
            message = messages.ProxyGetAttr(attr_path=attr_path)
            return self.actor_ref.ask(message, block=False)

    def __setattr__(self, name, value):
        if name == 'actor_ref' or name.startswith('_'):
            return super(ActorProxy, self).__setattr__(name, value)

        attr_path = self._attr_path + (name,)
        message = messages.ProxySetAttr(attr_path=attr_path, value=value)
        return self.actor_ref.ask(message)


class CallableProxy:
    """
    Proxy to a single method.
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
        message = messages.ProxyCall(attr_path=self._attr_path,
                                     args=args,
                                     kwargs=kwargs)

        return self.actor_ref.tell(message)


def traversable(obj):
    if hasattr(obj, '__slots__'):
        raise Exception(
            'pykka.traversable() cannot be used to mark '
            'an object using slots as traversable.'
        )

    obj._pykka_traversable = True
    return obj
