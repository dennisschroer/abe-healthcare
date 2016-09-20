from memory_profiler import memory_usage


def my_func():
    a = [1] * (10 ** 6)
    b = [2] * (2 * 10 ** 7)
    del b
    return a


def my_func2():
    my_func()


if __name__ == '__main__':
    print(memory_usage((my_func2, [], {})))
