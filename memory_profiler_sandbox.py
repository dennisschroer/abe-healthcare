from memory_profiler import profile, memory_usage


class Test(object):
    def __init__(self):
        self.a = None

    def my_func(self):
        a = [1] * (2 * 10 ** 7)
        return a

    @profile
    def profiled_method(self):
        self.a = self.my_func()

    def run(self):
        u = memory_usage((self.profiled_method, [], {}))
        print(max(u) - min(u), len(u))


if __name__ == '__main__':
    t = Test()
    t.run()