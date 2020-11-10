import functools

"""
actor.ask()
future 期望(将来的值)
Typically returned by calls to actor methods or accesses to actor fields.
调到actor方法或属性访问
"""


def await_dunder_future(self):
    yield
    value = self.get()
    return value


class Future:
    """
    `Future` is a handle to a value which is available or will be
    available in the future.
    """

    def __init__(self):
        # todo ? why super
        super(Future, self).__init__()
        self._get_hook = None
        self._get_hook_result = None

    def get(self, timeout=None):
        if self._get_hook is not None:
            """
            ref _stop_result_converter 就是一个钩子函数
            # 调用传进来的hook 函数.
            """
            self._get_hook_result = self._get_hook(timeout)

            return self._get_hook_result

        raise NotImplementedError

    def set(self, value=None):
        raise NotImplementedError

    def set_exception(self, exc_info=None):
        raise NotImplementedError

    def set_exception(self, exc_info=None):
        raise NotImplementedError

    def set_get_hook(self, func):
        """
        .get 调用func func 有个默认参数timeout
        :param func:
        :return:
        """
        self._get_hook = func

    def filter(self, func):
        future = self.__class__()
        future.set_get_hook(
            lambda timeout: list(filter(func, self.get(timeout)))
        )
        return future

    def join(self, *futures):
        future = self.__class__()
        future.set_get_hook(
            lambda timeout: [f.get(timeout) for f in [self] + list(futures)]
        )
        return future

    def map(self, func):
        #  实例化类
        future = self.__class__()
        future.set_get_hook(lambda timeout: func(self.get(timeout)))
        return future

    def reduce(self, func, *args):
        future = self.__class__()
        future.set_get_hook(
            lambda timeout: functools.reduce(func, self.get(timeout), *args)
        )
        return future

    __await__ = await_dunder_future
    __iter__ = __await__


def get_all(futures, timeout=None):
    return [future.get(timeout=timeout) for future in futures]
