"""
显示简单地 创建和使用actor.

"""
from actor_model.chapter06.threading import ThreadingActor
# Notes: The Sentinel Object Pattern
# https://python-patterns.guide/python/sentinel-object/
GetMessages = object()  # 哨兵flag


class PlainActor(ThreadingActor):
    def __init__(self):
        super().__init__()
        self.stored_messages = []

    def on_receive(self, message):
        """
        发送的消息存起来
        """
        if message is GetMessages:
            return self.stored_messages
        else:
            self.stored_messages.append(message)


if __name__ == "__main__":

    actor_ref = PlainActor.start()
    actor_ref.tell({'no': 'Norway', 'se': 'Sweden'})
    actor_ref.tell({'a': 3, 'b': 4, 'c': 5})
    print(actor_ref.ask(GetMessages))
    actor_ref.stop()

    # todo 为什么不考虑使用 with __exit__ stop()
    # 见下个例子