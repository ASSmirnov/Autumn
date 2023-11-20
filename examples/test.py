
def decorator(func):
    print("wwww", func.__qualname__)
    return func

class Foo:

    class Bar:
        @decorator
        def foo(self):
            pass
