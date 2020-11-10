"""
信封封装的消息体messages.
actor 其中有一条规则, actor可以修改自身属性和方法调用.
"""

from dataclasses import dataclass

from typing import Any, Sequence, Tuple, Dict


@dataclass
class _ActorStop:
    pass


@dataclass
class ProxyCall:
    """
    call a method on an actor.
    消息体: actor 去调到这个带有参数的方法获得值
    """
    # the path from the actor to the method
    # nested method
    attr_path: Sequence[str]  # 元组类型.
    args: Tuple[Any]
    kwargs: Dict[str, Any]


@dataclass
class ProxyGetAttr:
    """
     让actor返回属性值
    """
    attr_path: Sequence[str]


@dataclass
class ProxySetAttr:
    """
    让actor修改属性
    actor自身修改自身的属性值
    """
    attr_path: Sequence[str]
    value: Any


def _upgrade_internal_message(message):
    """Filter that upgrades dict-based internal messages to the new format.

    This is needed for a transitional period because Mopidy < 3 uses
    the old internal message format directly, and maybe others.
    """

    if not isinstance(message, dict):
        return message
    if not message.get('command', '').startswith('pykka_'):
        return message

