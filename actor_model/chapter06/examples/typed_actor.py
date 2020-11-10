import threading
import time

from actor_model.chapter06.threading import ThreadingActor


class AnActor(ThreadingActor):
    field = "this is the value of AnActor.field"

    def proc(self):
        log("this was printed by AnActor.proc()")

    def func(self):
        time.sleep(2)  # Block a bit to make it realistic
        return "this was returned by AnActor.func() after a delay"


def log(msg):
    thread_name = threading.current_thread().name
    print(f"{thread_name}: {msg}")


if __name__ == "__main__":
    # 创建代理
    thread_name = threading.current_thread().name
    print(f"主线程开始...")

    actor = AnActor.start().proxy()
    for _ in range(3):
        # Notes: https://zh.wikipedia.org/wiki/%E5%89%AF%E4%BD%9C%E7%94%A8_(%E8%AE%A1%E7%AE%97%E6%9C%BA%E7%A7%91%E5%AD%A6)
        # Method with side effect
        log("调用AnActor.proc 方法 ...")
        actor.proc()

        # Method with return value
        log("调用 AnActor.func 方法...")
        result = actor.func()  # Does not block, returns a future
        log("printing result ... (blocking)")
        # 阻塞直到就绪.
        log(result.get())  # Blocks until ready

        # Field reading
        # 读取字段
        log("reading AnActor.field ...")
        result = actor.field  # Does not block, returns a future
        log("printing result ... (blocking)")
        # Blocks until ready
        log(result.get())  # Blocks until ready

        # Field writing
        # 设置字段值.
        log("writing AnActor.field ...")
        actor.field = "new value"  # Assignment does not block
        result = actor.field  # Does not block, returns a future
        log("printing new field value ... (blocking)会阻塞一会")
        log(result.get())  # Blocks until ready
        print('\n')
    actor.stop()
