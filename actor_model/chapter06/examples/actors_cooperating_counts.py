"""
Multiple cooperating actors
本例子是展示多个actor之间的通信.
多个actor 一起数数.
"""
import threading

from actor_model.chapter06.actor_register import ActorRegistry
from actor_model.chapter06.threading import ThreadingActor


class Adder(ThreadingActor):
    """
    我负责统计
    """
    def add_one(self, i):
        print(f"{self} is increasing {i}::{threading.current_thread()}")
        return i + 1


class Bookkeeper(ThreadingActor):
    """
    我是图书统计员，具体统计给另一个人员Adder来做
    """
    def __init__(self, adder):
        super().__init__()
        self.adder = adder

    def count_to(self, target):
        i = 0
        while i < target:
            i = self.adder.add_one(i).get()  # 返回下一个值(i+1)
            print(f"{self} got {i} back {threading.current_thread()}")


if __name__ == "__main__":
    adder = Adder.start().proxy()
    bookkeeper = Bookkeeper.start(adder).proxy()
    bookkeeper.count_to(10).get()
    ActorRegistry.stop_all()
