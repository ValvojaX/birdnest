from threading import Thread, Event
from typing import Callable, Any, Iterable, Mapping


class DelayedTask(Thread):
    def __init__(self, task: Callable[[Any], Any], delay: float, *args, **kwargs):
        Thread.__init__(self)
        self.task: Callable[[Any], Any] = task
        self.delay: float = delay
        self.event: Event = Event()
        self.args: Iterable[Any] = args
        self.kwargs: Mapping[str, Any] = kwargs

    def run(self):
        self.event.wait(self.delay)
        self.task(*self.args, **self.kwargs)
