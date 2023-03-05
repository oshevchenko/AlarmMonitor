import threading
import time
import logging
import traceback
from abc import ABC, abstractmethod


class MonitorWatchdog:
    _wd_thr = None
    _wd_thr_running = False
    _wd_mutex = threading.RLock()
    _wd_watchdogs = []

    @classmethod
    def _cls_work(cls):
        while cls._wd_thr_running:
            callbacks = []
            with cls._wd_mutex:
                for wd in cls._wd_watchdogs:
                    cb = wd.timer_tick()
                    if cb:
                        callbacks.append(cb)
            for cb in callbacks:
                cb()
            time.sleep(1)
        pass

    @classmethod
    def start(cls):
        if not cls._wd_thr_running:
            cls._wd_thr_running = True
            cls._wd_thr = threading.Thread(target=cls._cls_work())
            cls._wd_thr.start()

    @classmethod
    def stop(cls):
        if cls._wd_thr_running:
            cls._wd_thr_running = False
            cls._wd_thr.join()

    def __init__(self, name, wd_timeout, wd_callback):
        self._name = name
        self._mutex = threading.RLock()
        self._timeout = wd_timeout
        self._timer = -1
        self._callback = wd_callback
        cls = self.__class__
        with cls._wd_mutex:
            cls._wd_watchdogs.append(self)

    def reset_timer(self):
        with self._mutex:
            self._timer = self._timeout

    def stop_timer(self):
        with self._mutex:
            self._timer = -1

    def timer_tick(self):
        ret = None
        with self._mutex:
            if self._timer > 0:
                self._timer -= 1
            if self._timer == 0:
                self._timer = -1
                ret = self._callback
        return ret


class BaseMonitor(ABC):
    def __init__(self, name=None, wd_timeout=60):
        self._thr_running = False
        self._thr = None
        if not name:
            name = self.__class__.__name__
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
        while self._thr_running:
            print('in progress')
            time.sleep(1)

    def _wd_callback(self):
        print('wd_callback')
        self.reset_wd_monitor()


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    def wd_timeout0():
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
    _wd_monitor = MonitorWatchdog(name="wd_name", wd_timeout=10, wd_callback=wd_timeout0)
    _wd_monitor.reset_timer()
    _wd_monitor1 = MonitorWatchdog(name="wd_name1", wd_timeout=15, wd_callback=wd_timeout1)
    _wd_monitor1.reset_timer()
    test = SaplingPTP4LMonitor('test1', 5)
    test.start()
    MonitorWatchdog.start()
    while True:
        print(_wd_monitor._wd_timeouts)
        time.sleep(1)
