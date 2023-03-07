import json
from abc import ABC, ABCMeta
from threading import RLock

# class MetaObserver(type):
#     def __new__(metacls, name, bases, namespace, **kwargs):
#         print('11111111111111111')
#         namespace['_observers'] = []
#         namespace['_mutex'] = RLock()
#         return super().__new__(metacls, name, bases, namespace)


# class MetaObserverAbc(MetaObserver, ABCMeta):
#     pass

# class Observer(ABC, metaclass=MetaObserverAbc):
#     def __init__(self):
#         with self._mutex:
#             self._observers.append(self)
#         self._observables = {}

#     def observe(self, event_name, callback):
#         self._observables[event_name] = callback

class ObserverM(ABC):
    def __init_subclass__(cls):
        super().__init_subclass__()
        cls._observers = []
        cls._mutex = RLock()

    def __init__(self):
        with self._mutex:
            self._observers.append(self)
        self._observables = {}

    def observe(self, event_name, callback):
        self._observables[event_name] = callback

class ObserverEventM(ABC):
    def __init_subclass__(cls, observer_class):
        super().__init_subclass__()
        cls._observer_class = observer_class

    def __init__(self, name, data, autofire=True):
        self.name = name
        self.data = data
        if autofire:
            self.fire()

    def fire(self):
        with self._observer_class._mutex:
            observers = self._observer_class._observers.copy()
        for observer in observers:
            if self.name in observer._observables:
                observer._observables[self.name](self.data)

class GpsObserver(ObserverM):
    pass

class GpsObserverEvent(ObserverEventM, observer_class=GpsObserver):
    pass

class RelayObserver(ObserverM):
    pass

class RelayObserverEvent(ObserverEventM, observer_class=RelayObserver):
    pass

class gps_manager(object):
    def __init__(self):
        self.observer = GpsObserver()
        self.observer.observe('gps_attached', self.gps_attached)
        self.observer.observe('tty_attached', self.tty_attached)
        self.observer2 = GpsObserver()

    def gps_attached(self, who):
        print(who + " gps attached!")

    def tty_attached(self, who):
        print(who + " gps_manager tty_attached!")


class relay_manager(object):
    def __init__(self):
        self.observer = RelayObserver()
        self.observer.observe('relay_attached', self.relay_attached)
        self.observer.observe('tty_attached', self.tty_attached)
        self.observer.observe('test_callable', self.test_callable)

    def relay_attached(self, who):
        print(who + " relay attached!")

    def tty_attached(self, who):
        print(who + " relay_manager tty_attached")

    def test_callable(self, callback):
        callback()


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    def TestCallable():
        print('Hello from TestCallable!')


    gps_mngr = gps_manager()
    relay_mngr = relay_manager()
    print('gps_manager id {}'.format(id(GpsObserver._observers)))
    print('gps_manager id {}'.format(id(gps_mngr.observer._observers)))
    print('gps_manager id {}'.format(id(gps_mngr.observer2._observers)))
    print('relay_manager id {}'.format(id(relay_mngr.observer._observers)))
    GpsObserverEvent('gps_attached', 'tty1')
    RelayObserverEvent('relay_attached', 'tty1')
    GpsObserverEvent('relay_attached', 'tty1')
    GpsObserverEvent('gps_attached', 'tty2')
    GpsObserverEvent('tty_attached', 'tty3')
    RelayObserverEvent('xxx', 'tty4')
    RelayObserverEvent('tty_attached', 'tty5')
    RelayObserverEvent('test_callable', TestCallable)

    # graph = DotGraphMachine(AlarmMonitor)
    # dot = graph()
    # dot.write_png("AlarmMonMachine_initial.png")
