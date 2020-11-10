from ..envelope import Envelope
from ..messages import _ActorStop, ProxyCall, ProxyGetAttr, ProxySetAttr


def test_actor_stop():
    message = _ActorStop()

    assert isinstance(message, _ActorStop)


def test_proxy_call():
    """
    nested.method
    """
    message = ProxyCall(
        attr_path=["nested", "method"], args=[1, 2], kwargs={"agent": "model"}
    )

    assert isinstance(message, ProxyCall)
    assert message.attr_path == ["nested", "method"]
    assert message.args == [1, 2]
    assert message.kwargs == {"agent": "model"}


def test_proxy_get_attr():
    message = ProxyGetAttr(attr_path=["nested", "attr"])

    assert isinstance(message, ProxyGetAttr)
    assert message.attr_path == ["nested", "attr"]


def test_proxy_set_attr():
    message = ProxySetAttr(attr_path=["nested", "method"], value="val")

    assert isinstance(message, ProxySetAttr)
    assert message.attr_path == ["nested", "method"]
    assert message.value == "val"


def test_envelope_repr():
    envelope = Envelope("message", reply_to='future')

    assert repr(envelope) == "Envelope(message='message', reply_to='future')"


def test_envelope_payload_message():
    message = ProxyGetAttr(attr_path=["nested", "attr"])
    envelope = Envelope(message=message, reply_to="future")
    assert envelope.message.__class__.__name__ == 'ProxyGetAttr'
