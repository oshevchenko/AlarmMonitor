class Observer():
    _observers = []
    def __init__(self):
        self._observers.append(self)
        self._observables = {}
    def observe(self, event_name, callback):
        self._observables[event_name] = callback


class Event():
    def __init__(self, name, data, autofire = True):
        self.name = name
        self.data = data
        if autofire:
            self.fire()
    def fire(self):
        for observer in Observer._observers:
            if self.name in observer._observables:
                observer._observables[self.name](self.data)


class gps_manager(object):
    def __init__(self):
        self.observer = Observer()
        self.observer.observe('gps_attached', self.gps_attached)
        self.observer.observe('tty_attached', self.tty_attached)
    def gps_attached(self, who):
        print(who + " gps attached!")
    def tty_attached(self, who):
        print(who + " check for gps!")

class relay_manager(object):
    def __init__(self):
        self.observer = Observer()
        self.observer.observe('relay_attached', self.relay_attached)
        self.observer.observe('tty_attached', self.tty_attached)
    def relay_attached(self, who):
        print(who + " relay attached!")
    def tty_attached(self, who):
        print(who + " check for relay!")


# Press the green button in the gutter to run the script.
if __name__ == '__main__':

    gps_mngr = gps_manager()
    relay_mngr = relay_manager()

    Event('relay_attached', 'tty1')
    Event('gps_attached', 'tty2')
    Event('tty_attached', 'tty3')
    Event('xxx', 'tty4')
    Event('tty_attached', 'tty5')

    # graph = DotGraphMachine(AlarmMonitor)
    # dot = graph()
    # dot.write_png("AlarmMonMachine_initial.png")