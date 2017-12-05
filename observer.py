import abc


class Observer:
    __metaclass__ = abc.ABCMeta

    def __init__(self):
        self._observer_state = None

    @abc.abstractmethod
    def update(self, arg):
        pass
