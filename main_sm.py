from statemachine import StateMachine, State
from statemachine.exceptions import TransitionNotAllowed
from statemachine.contrib.diagram import DotGraphMachine
from enum import Enum
from copy import deepcopy
from typing import Protocol, List, Dict, Any
import logging
import time

TRANS_TIMEOUT=5
IDLE_TIMEOUT = 10

class ServiceStatus(Enum):
    free_running = 7
    running = 6
    stopped = 5
    ptp_source = 4
    no_ptp_source = 3
    local = 2
    undefined = 1

class StateName(Enum):
    gnss_master = 1
    gnss_alarm = 2
    ptp = 3
    ext_osc_run = 4
    ext_osc_alarm = 5
    ntp = 6
    initial = 7
    transient = 8
    alarm = 9
    manual = 10
    undefined = 11

class EventName(Enum):
    tick = 1
    gnss_found = 2
    ptp_found = 3
    ntp_found = 4
    ext_osc_found = 5
    gnss_lost = 6
    ptp_lost = 7
    ntp_lost = 8
    ext_osc_lost = 9
    ptp_slave = 10
    ptp_non_slave = 11

class StatePriority(Enum):
    prio_1 = 0
    prio_2 = 1
    prio_3 = 2
    prio_4 = 3
    prio_undefined = 4

class EventLostPriority(Enum):
    ev_prio_1_lost = 0
    ev_prio_2_lost = 1
    ev_prio_3_lost = 2
    ev_prio_4_lost = 3

class EventFoundPriority(Enum):
    ev_prio_1_found = 0
    ev_prio_2_found = 1
    ev_prio_3_found = 2
    ev_prio_4_found = 3



g_manual_state = {
        'name': StateName.manual,
        'ts2phc_service': ServiceStatus.stopped,
        'ptp4l_service': ServiceStatus.free_running,
        'phc2sys_service': ServiceStatus.running,
        'ptp_chronyd_service': ServiceStatus.local,
}
g_manual_ext_osc_state = {
        'name': StateName.ext_osc_run,
        'ts2phc_service': ServiceStatus.stopped,
        'ptp4l_service': ServiceStatus.free_running,
        'phc2sys_service': ServiceStatus.stopped,
        'ptp_chronyd_service': ServiceStatus.ptp_source,
}
g_gnss_master_state = {
        'name': StateName.gnss_master,
        'ts2phc_service': ServiceStatus.running,
        'ptp4l_service': ServiceStatus.free_running,
        'phc2sys_service': ServiceStatus.stopped,
        'ptp_chronyd_service': ServiceStatus.ptp_source,
}
g_gnss_alarm_state = {
        'name': StateName.gnss_alarm,
        'ts2phc_service': ServiceStatus.stopped,
        'ptp4l_service': ServiceStatus.free_running,
        'phc2sys_service': ServiceStatus.stopped,
        'ptp_chronyd_service': ServiceStatus.no_ptp_source,
}
g_ptp_state = {
        'name': StateName.ptp,
        'ts2phc_service': ServiceStatus.stopped,
        'ptp4l_service': ServiceStatus.running,
        'phc2sys_service': ServiceStatus.stopped,
        'ptp_chronyd_service': ServiceStatus.ptp_source,
}
g_ext_osc_alarm_state = {
        'name': StateName.ext_osc_alarm,
        'ts2phc_service': ServiceStatus.stopped,
        'ptp4l_service': ServiceStatus.free_running,
        'phc2sys_service': ServiceStatus.stopped,
        'ptp_chronyd_service': ServiceStatus.no_ptp_source,
}
g_ntp_state = {
        'name': StateName.ntp,
        'ts2phc_service': ServiceStatus.stopped,
        'ptp4l_service': ServiceStatus.free_running,
        'phc2sys_service': ServiceStatus.running,
        'ptp_chronyd_service': ServiceStatus.no_ptp_source,
}
g_idle_state = {
        'name': StateName.initial,
        'ts2phc_service': ServiceStatus.undefined,
        'ptp4l_service': ServiceStatus.undefined,
        'phc2sys_service': ServiceStatus.undefined,
        'ptp_chronyd_service': ServiceStatus.undefined,
}
g_alarm_state = {
        'name': StateName.alarm,
        'ts2phc_service': ServiceStatus.undefined,
        'ptp4l_service': ServiceStatus.undefined,
        'phc2sys_service': ServiceStatus.undefined,
        'ptp_chronyd_service': ServiceStatus.undefined,
}



class LogObserver(object):
    def __init__(self, name):
        self.name = name

    def after_transition(self, event, source, target):
        print(f"{self.name} after: {source.id}--({event})-->{target.id}")

    def on_enter_state(self, target, event):
        print(f"{self.name} enter: {target.id} from {event}")

class PtpManager(Protocol):
    def _start_ts2phc(self) -> str:
        ...

    def _stop_ts2phc(self) -> str:
        ...

    def _restart_ptp4l_free_running(self, free_running: bool = False) -> str:
        ...

    def _start_phc2sys(self) -> str:
        ...

    def _stop_phc2sys(self) -> str:
        ...

    def _add_ptp_chrony_sources(self) -> str:
        ...

    def _remove_ptp_chrony_sources(self) -> str:
        ...

    def _stop_chronyd(self) -> str:
        ...

    def _set_chrony_local(self) -> str:
        ...

    def ptp_manager_set_config(self, config: Dict[str, Any]) -> None:
        ...


class AlarmManager(Protocol):
    def trigger(self, alarm_id: str) -> None:
        ...

    def start(self, alarm_id: str) -> None:
        ...

    def stop(self, alarm_id: str) -> None:
        ...

    def reset(self, alarm_id: str) -> None:
        ...



class MainStateMachineData(object):

    _overall_status_dict_def =  {
        'current_reference': 'None',
        'sync_status': 'Starting',
        'ref_status': {
            "GNSS": 'undefined',
            "PTP":  'undefined',
            "NTP":  'undefined',
            "Ext. Osc.": 'ok',
        },
        'event_status': {
            "GNSS": {
                "lost": 3600,
                "ok": 3600,
            },
            "PTP":  {
                "lost": 3600,
                "ok": 3600,
            },
            "NTP":  {
                "lost": 3600,
                "ok": 3600,
            },
            "Ext. Osc.": {
                "lost": 3600,
                "ok": 3600,
            }
        },
        'services': {
            'ts2phc': 'undefined',
            'chronyd': 'undefined',
            'ptp4l': 'undefined',
            'phc2sys_local': 'undefined',
        },
        'priorities': [
        ],
    }
    _def_priorities = ['GNSS', 'PTP', 'NTP', 'Ext. Osc.']
    _async_priorities = ['GNSS', 'PTP', 'NTP', 'Ext. Osc.']
    _overall_status_dict = deepcopy(_overall_status_dict_def)

    def __init__(self, ptp_manager: PtpManager, alarm_manager: AlarmManager):
        self._current_state = g_idle_state
        self._ptp_manager = ptp_manager
        self._alarm_manager = alarm_manager
        self._manual_time = None
        self._manual_trigger_time = None
        self._config = None

    def set_priorities(self, prio):
        self._overall_status_dict['priorities'] = prio

    def get_ev_prio_x_lost(self, event):
        ev_prio_x_lost = None
        source_lost = {
                EventName.gnss_lost:    "GNSS",
                EventName.ptp_lost:     "PTP",
                EventName.ntp_lost:     "NTP",
                EventName.ext_osc_lost: "Ext. Osc."
            }.get(event, None)

        if source_lost and source_lost in self._overall_status_dict['priorities']:
            self._overall_status_dict['event_status'][source_lost]['lost'] = 0
            self._overall_status_dict['ref_status'][source_lost] = 'lost'
            ev_prio_x_lost = EventLostPriority(self._overall_status_dict['priorities'].index(source_lost))
        return ev_prio_x_lost

    def get_ev_prio_x_found(self, event):
        ev_prio_x_found = None
        source_found = {
                EventName.gnss_found:    "GNSS",
                EventName.ptp_found:     "PTP",
                EventName.ntp_found:     "NTP",
                EventName.ext_osc_found: "Ext. Osc."
            }.get(event, None)

        if source_found and source_found in self._overall_status_dict['priorities']:
            self._overall_status_dict['event_status'][source_found]['ok'] = 0
            self._overall_status_dict['ref_status'][source_found] = 'ok'
            ev_prio_x_found = EventFoundPriority(self._overall_status_dict['priorities'].index(source_found))
        return ev_prio_x_found

    def _set_next_state(self, next_state: Dict[str, Any]):
        if next_state['ts2phc_service'] != self._current_state['ts2phc_service']:
            ret = {
                'running': self._ptp_manager._start_ts2phc,
                'stopped': self._ptp_manager._stop_ts2phc,
            }.get(next_state['ts2phc_service'].name)()
            self._overall_status_dict['services']['ts2phc'] = ret

        if next_state['ptp4l_service'] != self._current_state['ptp4l_service']:
            ret = self._ptp_manager._restart_ptp4l_free_running(\
            {
                'running': False,
                'free_running': True,
            }.get(next_state['ptp4l_service'].name))
            self._overall_status_dict['services']['ptp4l'] = ret

        if next_state['phc2sys_service'] != self._current_state['phc2sys_service']:
            ret = {
                'running': self._ptp_manager._start_phc2sys,
                'stopped': self._ptp_manager._stop_phc2sys,
            }.get(next_state['phc2sys_service'].name)()
            self._overall_status_dict['services']['phc2sys_local'] = ret

        if next_state['ptp_chronyd_service'] != self._current_state['ptp_chronyd_service']:
            ret = {
                'ptp_source': self._ptp_manager._add_ptp_chrony_sources,
                'no_ptp_source': self._ptp_manager._remove_ptp_chrony_sources,
                'stopped': self._ptp_manager._stop_chronyd,
                'local': self._ptp_manager._set_chrony_local
            }.get(next_state['ptp_chronyd_service'].name)()
            self._overall_status_dict['services']['chronyd'] = ret

        self._current_state = next_state

    def sm_set_state_by_priority(self, prio: StatePriority):
        """To be called from Main State Machine on enter prio_x_trans."""
        # print("prio {} dict {}".format(prio, self._overall_status_dict['priorities']))
        if len(self._overall_status_dict['priorities']) > prio.value:
            sync_ref = self._overall_status_dict['priorities'][prio.value]
            next_state = {
                    "GNSS":      g_gnss_master_state,
                    "PTP":       g_ptp_state,
                    "NTP":       g_ntp_state,
                }.get(sync_ref)
            self._set_next_state(next_state)

    def set_state_manual(self):
        self._set_next_state(g_manual_state)

    def set_state_manual_ext_osc(self):
        self._set_next_state(g_manual_ext_osc_state)

    def mq_set_config(self, config: Dict[str, Any]):
        self._config = config

    def sm_reset_services_states(self):
        if self._config == None:
            logging.error("Config is not set!")
            return
        priorities = self._config.get('priority_list', self._def_priorities)
        logging.info("Setting priorities: {}".format(priorities))
        if (len(priorities) == 0):
            new_priorities = self._def_priorities
        else:
            # self._overall_status_dict['priorities'] = priorities
            new_priorities = priorities
        if len(priorities) > 1:
            # Start if we have something except 'Ext. Osc.'
            self._alarm_manager.start('ptpmanager_alarm')
        else:
            # Stop if we only have 'Ext. Osc.' enabled.
            self._alarm_manager.stop('ptpmanager_alarm')
        self._overall_status_dict['priorities'] = new_priorities
        self._ptp_manager.ptp_manager_set_config(self._config)
        self._current_state = g_idle_state

    def add_manual_time(self, manual_time: int):
        self._manual_time = manual_time
        self._manual_trigger_time = time.time()

    def set_manual_time(self):
        if self._manual_time:
            self._ptp_manager.set_manual_time(self._manual_time, self._manual_trigger_time)

    def sm_start_timer_1(self, timeout: int = TRANS_TIMEOUT):
        self._timer_1 = timeout

    def mq_check_expired_timer_1(self):
        ret = False
        if self._timer_1 != 0:
            self._timer_1 -= 1
        if self._timer_1 == 0:
            ret = True
        return ret


class MainStateMachine(StateMachine):
    """Monitor Alarms state machine"""
    stable_states = ['st_init',\
                     'st_alarm',\
                     'st_prio_1',\
                     'st_prio_2',\
                     'st_prio_3',\
                     'st_manual',\
                     'st_manual_ext_osc']
    st_init = State("init", initial=True)
    st_alarm = State("alarm")
    st_idle = State("idle")

    st_prio_3_idle = State("prio_3_idle")
    st_prio_2_idle = State("prio_2_idle")

    st_manual_trans = State("manual_trans")
    st_manual_ext_osc_trans = State("manual_ext_osc_trans")

    st_manual = State("manual")
    st_manual_ext_osc = State("manual_ext_osc")

    st_prio_3 = State("prio_3")
    st_prio_2 = State("prio_2")
    st_prio_1 = State("prio_1")

    st_prio_3_trans = State("prio_3_trans")
    st_prio_2_trans = State("prio_2_trans")
    st_prio_1_trans = State("prio_1_trans")

    ev_error = st_alarm.from_(st_prio_1, st_prio_2, st_prio_3, st_manual, st_manual_ext_osc)
    ev_set_time = st_manual.to(st_manual) | st_manual_ext_osc.to(st_manual_trans)

    ev_timeout = st_prio_1_trans.to(st_prio_1) | \
              st_prio_2_trans.to(st_prio_2) | \
              st_prio_3_trans.to(st_prio_3) | \
              st_prio_2_idle.to(st_prio_2_trans) | \
              st_prio_3_idle.to(st_prio_3_trans) | \
              st_idle.to(st_manual_trans, unless='ext_osc_in_sync') | \
              st_idle.to(st_manual_ext_osc_trans, cond='ext_osc_in_sync') | \
              st_manual_trans.to(st_manual) | \
              st_manual_ext_osc_trans.to(st_manual_ext_osc)

    ev_config_update = st_idle.from_(st_init, st_alarm,\
                                     st_prio_1, st_prio_2, st_prio_3,\
                                     st_manual, st_manual_ext_osc)
    ev_prio_1_lost = st_prio_1.to(st_idle)
    ev_prio_2_lost = st_prio_2.to(st_idle)
    ev_prio_3_lost = st_prio_3.to(st_idle)

    ev_prio_3_found = st_manual.to(st_prio_3_trans) |\
                      st_manual_ext_osc.to(st_prio_3_trans) |\
                      st_idle.to(st_prio_3_idle)

    ev_prio_2_found = st_manual.to(st_prio_2_trans) |\
                      st_manual_ext_osc.to(st_prio_2_trans) |\
                      st_prio_3.to(st_prio_2_trans) |\
                      st_idle.to(st_prio_2_idle) |\
                      st_prio_3_idle.to(st_prio_2_idle)

    ev_prio_1_found = st_prio_1_trans.from_(st_manual, st_manual_ext_osc,\
                                            st_prio_2, st_prio_3,\
                                            st_idle, st_prio_2_idle, st_prio_3_idle)

    def __init__(self, sm_data: MainStateMachineData) -> None:
        super().__init__()
        self.timer = None
        self._sm_data = sm_data

    def on_enter_st_idle(self):
        self._sm_data.sm_start_timer_1(IDLE_TIMEOUT)
        pass

    def on_enter_st_prio_1_trans(self):
        """Start timer, set prio1 state configuration."""
        self._sm_data.sm_start_timer_1(TRANS_TIMEOUT)
        self._sm_data.sm_set_state_by_priority(StatePriority.prio_1)
        pass

    def on_enter_st_prio_2_trans(self):
        """Start timer, set prio2 state configuration."""
        self._sm_data.sm_start_timer_1(TRANS_TIMEOUT)
        self._sm_data.sm_set_state_by_priority(StatePriority.prio_2)
        pass

    def on_enter_st_prio_3_trans(self):
        """Start timer, set prio3 state configuration."""
        self._sm_data.sm_start_timer_1(TRANS_TIMEOUT)
        self._sm_data.sm_set_state_by_priority(StatePriority.prio_3)
        pass

    def on_enter_st_manual_trans(self):
        """Set manual state configuration."""
        print("TODO: Set manual state configuration.")
        pass

    def on_enter_st_manual_ext_osc_trans(self):
        """Set manual state configuration."""
        print("TODO: Set manual ext. osc. state configuration.")
        pass

    def ext_osc_in_sync(self):
        """Return True if external oscillator is synchronized beforehand."""
        print("TODO: Return True if external oscillator was synchronized beforehand.")
        pass

    def on_ev_config_update(self, event: str, source: State, target: State, message: str = ""):
        message = ". " + message if message else ""
        self._sm_data.sm_reset_services_states()

        # if source.id is in self.stable_states and target.id == "st_idle":
        print("TODO: Set all PTP4L services states to UNDEFINED. >>>")


# Press the green button in the gutter to run the script.
if __name__ == '__main__':

    graph = DotGraphMachine(MainStateMachine)
    dot = graph()
    dot.write_png("MainStateMachine_initial.png")

    sm_main = MainStateMachine("uart")
    sm_main.add_observer(LogObserver("uart"))
    # sm_main.ev_start()

    # for i in range(15):
    #     try:
    #         if i == 3:
    #             sm_main.ev_reset()

    #         print(sm_main.timer)
    #         sm_main.ev_tick()

    #     except TransitionNotAllowed:
    #         pass

