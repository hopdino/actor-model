"""
定义了信封特殊的数据结构体
信封: 信封里面装有消息体.
"""


class Envelope:
    """
    actor 接收的信件.
    :param message: the message to send
    :type message: any
    :param reply_to: the future to reply to if there is a response
    :type reply_to: :class:`pykka.Future`
    """

    __slots__ = ['message', 'reply_to']

    def __init__(self, message, reply_to=None):
        self.message = message
        # 把获得消息传递future（统一处理接收的信息）
        self.reply_to = reply_to

    def __repr__(self):
        return f"Envelope(message={self.message!r}, reply_to={self.reply_to!r})"
