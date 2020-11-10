"""
大家可以丰富with context的写法.
"""
from actor_model.chapter06.threading import ThreadingActor
# Notes: The Sentinel Object Pattern
# https://python-patterns.guide/python/sentinel-object/
GetMessages = object()  # 哨兵flag


class PlainActor(ThreadingActor):
    def __init__(self):
        super().__init__()
        self.stored_messages = []  # 是不是和注册的地方类似 注册==存储

    def on_receive(self, message):
        """
        """
        if message is GetMessages:
            return self.stored_messages
        else:
            self.stored_messages.append(message)


if __name__ == "__main__":

    with PlainActor.start() as actor:
        actor.tell({'no': 'Norway', 'se': 'Sweden'})
        actor.tell({'a': 3, 'b': 4, 'c': 5})
        print(actor.ask(GetMessages))
