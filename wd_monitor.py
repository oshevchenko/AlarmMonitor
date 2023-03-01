import threading
import time
import logging
import traceback
from abc import ABC, abstractmethod

class MonitorWatchdog():
    _wd_timeouts = {}
    _wd_callbacks = {}
    _wd_thr = None
    _mutex = threading.RLock()

    def __init__(self, name, wd_timeout, wd_callback):
        self._name = name
        self._wd_timeout = wd_timeout
        with MonitorWatchdog._mutex:
            MonitorWatchdog._wd_timeouts[name] = -1
            MonitorWatchdog._wd_callbacks[name] = wd_callback
        print('self._wd_thr--- {}'.format(MonitorWatchdog._wd_thr))
        if MonitorWatchdog._wd_thr is None:
            MonitorWatchdog._wd_thr = threading.Thread(target=self._wd_work)
            print('self._wd_thr {}'.format(self._wd_thr))
            MonitorWatchdog._wd_thr.start()
            print('start thread')
        pass

    def _wd_work(self):
        while True:
            callbacks = []
            with MonitorWatchdog._mutex:
                for name in MonitorWatchdog._wd_timeouts.keys():
                    timeout = MonitorWatchdog._wd_timeouts[name]
                    if timeout > 0:
                        timeout -= 1
                    if timeout == 0:
                        timeout = -1
                        callbacks.append(MonitorWatchdog._wd_callbacks.get(name, None))
                    MonitorWatchdog._wd_timeouts[name] = timeout
            for callback in callbacks:
                if callback:
                    callback()
            time.sleep(1)
        pass

    def reset_timer(self):
        with MonitorWatchdog._mutex:
            MonitorWatchdog._wd_timeouts[self._name] = self._wd_timeout

    def stop_timer(self):
        with MonitorWatchdog._mutex:
            MonitorWatchdog._wd_timeouts[self._name] = -1


class BaseMonitor(ABC):
    def __init__(self, name, wd_timeout = 60):
        self._thr_running = False
        self._thr = None
        self._wd_monitor = MonitorWatchdog(name, wd_timeout, self._wd_callback)

    def start(self):
        self._thr_running = True
        self._thr = threading.Thread(target=self._process)
        self._thr.start()
        self._wd_monitor.reset_timer()

    def stop(self):
        if (self._thr_running == False) or (self._thr is None):
            return
        self._wd_monitor.stop_timer()
        self._thr_running = False
        try:
            self._thr.join()
        except Exception as e:
            logging.error(e)
            logging.error(traceback.format_exc())
            pass
        self._thr = None

    def reset_wd_monitor(self):
        self._wd_monitor.reset_timer()

    @abstractmethod 
    def _process(self):
        pass

    @abstractmethod
    def _wd_callback(self):
        pass

class SaplingPTP4LMonitor(BaseMonitor):

    def _process(self):
        while self._thr_running == True:
            print('in progress')
            time.sleep(1)


    def _wd_callback(self):
        print('wd_callback')


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    def wd_timeout():
        print('wd_timeout')
        pass
    def wd_timeout1():
        print('wd_timeout1')
        pass
    def _process():
        while True:
            time.sleep(1)
        pass
    _thr_running = True
    _thr = threading.Thread(target=_process)
    _thr.start()
    _wd_monitor = MonitorWatchdog(name="wd_name", wd_timeout=10, wd_callback=wd_timeout)
    _wd_monitor.reset_timer()
    _wd_monitor1 = MonitorWatchdog(name="wd_name1", wd_timeout=15, wd_callback=wd_timeout1)
    _wd_monitor1.reset_timer()
    test = SaplingPTP4LMonitor('test1', 60)
    test.start()

    while True:
        print(_wd_monitor._wd_timeouts)
        time.sleep(1)
