from unittest import TestCase
from main_sm import MainStateMachine, MainStateMachineData, EventName, EventLostPriority, StateName, StatePriority
import mock
from statemachine.exceptions import TransitionNotAllowed
from typing import Dict, Any
import json

# Launching unittests with arguments
# python -m unittest tests.test_main_sm.TestMainStateMachine
# in C:\Users\shevc\PycharmProjects\AlarmMonitor

g_call_sequence = []

class PtpManager(object):
    def _start_ts2phc(self) -> str:
        g_call_sequence.append("_start_ts2phc")
        return 'ok'

    def _stop_ts2phc(self) -> str:
        g_call_sequence.append("_stop_ts2phc")
        return 'ok'

    def _restart_ptp4l_free_running(self, free_running: bool = False) -> str:
        g_call_sequence.append("_restart_ptp4l_free_running "+str(free_running))
        return 'ok'

    def _start_phc2sys(self) -> str:
        g_call_sequence.append("_start_phc2sys")
        return 'ok'

    def _stop_phc2sys(self) -> str:
        g_call_sequence.append("_stop_phc2sys")
        return 'ok'

    def _add_ptp_chrony_sources(self) -> str:
        g_call_sequence.append("_add_ptp_chrony_sources")
        return 'ok'

    def _remove_ptp_chrony_sources(self) -> str:
        g_call_sequence.append("_remove_ptp_chrony_sources")
        return 'ok'

    def _stop_chronyd(self) -> str:
        g_call_sequence.append("_stop_chronyd")
        return 'ok'

    def _set_chrony_local(self) -> str:
        g_call_sequence.append("_set_chrony_local")
        return 'ok'

    def ptp_manager_set_config(self, config: Dict[str, Any]) -> None:
        g_call_sequence.append("ptp_manager_set_config "+json.dumps(config))


class AlarmManager(object):
    def trigger(self, alarm_id: str) -> None:
        g_call_sequence.append("alarm trigger "+alarm_id)

    def start(self, alarm_id: str) -> None:
        g_call_sequence.append("alarm start "+alarm_id)

    def stop(self, alarm_id: str) -> None:
        g_call_sequence.append("alarm stop "+alarm_id)

    def reset(self, alarm_id: str) -> None:
        g_call_sequence.append("alarm reset "+alarm_id)


class TestMainStateMachine(TestCase):
    def setUp(self):
        self.ptp_manager = PtpManager()
        self.alarm_manager = AlarmManager()
        self.sm_data = MainStateMachineData(self.ptp_manager, self.alarm_manager)
        pass

    def test_on_enter_idle(self):
        sm_main = MainStateMachine(self.sm_data)
        config = {'priority_list': ['PTP', 'NTP', 'GNSS', 'Ext. Osc.']}
        self.sm_data.mq_set_config(config)
        sm_main.ev_config_update()
        self.assertTrue(sm_main.st_idle.is_active)

    @mock.patch.object(MainStateMachine, 'on_enter_st_idle')
    @mock.patch.object(MainStateMachine, 'on_enter_st_prio_1_trans')
    def test_on_enter_st_prio_1_trans(self, mock_on_enter_st_prio_1_trans,
                                      mock_on_enter_st_idle):
        # with mock.patch.object(MainStateMachine, 'on_enter_st_prio_1_trans') as mock_method:
        sm_main = MainStateMachine(self.sm_data)
        config = {'priority_list': ['PTP', 'NTP', 'GNSS', 'Ext. Osc.']}
        self.sm_data.mq_set_config(config)
        sm_main.ev_config_update()
        self.assertTrue(mock_on_enter_st_idle.called)
        sm_main.ev_prio_1_found()
        self.assertTrue(sm_main.st_prio_1_trans.is_active)
        self.assertTrue(mock_on_enter_st_prio_1_trans.called)

    @mock.patch.object(MainStateMachine, 'on_enter_st_prio_2_trans')
    def test_on_enter_st_prio_2_trans(self, mock_on_enter_prio_2_trans):
        sm_main = MainStateMachine(self.sm_data)
        config = {'priority_list': ['PTP', 'NTP', 'GNSS', 'Ext. Osc.']}
        self.sm_data.mq_set_config(config)
        sm_main.ev_config_update()
        sm_main.ev_prio_2_found()
        sm_main.ev_timeout()
        self.assertTrue(mock_on_enter_prio_2_trans.called)
        self.assertTrue(sm_main.st_prio_2_trans.is_active)
        # Currently error transaction is only made from stable states
        try:
            sm_main.ev_error()
            self.fail()
        except TransitionNotAllowed:
            pass

    @mock.patch.object(MainStateMachine, 'on_enter_st_prio_3_trans')
    def test_on_enter_st_prio_3_trans(self, mock_on_enter_prio_3_trans):
        sm_main = MainStateMachine(self.sm_data)
        config = {'priority_list': ['PTP', 'NTP', 'GNSS', 'Ext. Osc.']}
        self.sm_data.mq_set_config(config)
        sm_main.ev_config_update()
        sm_main.ev_prio_3_found()
        sm_main.ev_timeout()
        self.assertTrue(mock_on_enter_prio_3_trans.called)
        self.assertTrue(sm_main.st_prio_3_trans.is_active)
        # Currently error transaction is only made from stable states
        try:
            sm_main.ev_error()
            self.fail()
        except TransitionNotAllowed:
            pass
        sm_main.ev_timeout()
        self.assertTrue(sm_main.st_prio_3.is_active)
        sm_main.ev_error()
        self.assertTrue(sm_main.st_alarm.is_active)

    @mock.patch.object(MainStateMachine, 'ext_osc_in_sync', return_value=False)
    @mock.patch.object(MainStateMachine, 'on_enter_st_manual_trans')
    def test_on_enter_st_manual_trans(self, mock_on_enter_st_manual_trans, mock_ext_osc_in_sync):
        sm_main = MainStateMachine(self.sm_data)
        config = {'priority_list': ['PTP', 'NTP', 'GNSS', 'Ext. Osc.']}
        self.sm_data.mq_set_config(config)
        sm_main.ev_config_update()
        sm_main.ev_timeout()
        self.assertTrue(mock_ext_osc_in_sync.called)
        self.assertTrue(mock_on_enter_st_manual_trans.called)
        self.assertTrue(sm_main.st_manual_trans.is_active)
        sm_main.ev_timeout()
        self.assertTrue(sm_main.st_manual.is_active)

    @mock.patch.object(MainStateMachine, 'ext_osc_in_sync', return_value=True)
    @mock.patch.object(MainStateMachine, 'on_enter_st_manual_ext_osc_trans')
    def test_on_enter_st_manual_trans(self, mock_on_enter_st_manual_ext_osc_trans, mock_ext_osc_in_sync):
        sm_main = MainStateMachine(self.sm_data)
        config = {'priority_list': ['PTP', 'NTP', 'GNSS', 'Ext. Osc.']}
        self.sm_data.mq_set_config(config)
        sm_main.ev_config_update()
        sm_main.ev_timeout()
        self.assertTrue(mock_ext_osc_in_sync.called)
        self.assertTrue(mock_on_enter_st_manual_ext_osc_trans.called)
        self.assertTrue(sm_main.st_manual_ext_osc_trans.is_active)
        sm_main.ev_timeout()
        self.assertTrue(sm_main.st_manual_ext_osc.is_active)


    def test_main_sm_data_get_ev_prio_x_lost(self):
        ptp_manager = PtpManager()
        alarm_manager = AlarmManager()
        sm_main = MainStateMachineData(ptp_manager, alarm_manager)
        sm_main.set_priorities(['PTP', 'NTP', 'GNSS', 'Ext. Osc.'])
        ev_prio_x_lost = sm_main.get_ev_prio_x_lost(EventName.gnss_lost)
        self.assertTrue(ev_prio_x_lost.name == 'ev_prio_3_lost')
        ev_prio_x_found = sm_main.get_ev_prio_x_found(EventName.gnss_found)
        self.assertTrue(ev_prio_x_found.name == 'ev_prio_3_found')
        sm_main.set_priorities(['PTP', 'NTP', 'Ext. Osc.'])
        ev_prio_x_lost = sm_main.get_ev_prio_x_lost(EventName.gnss_lost)
        self.assertTrue(ev_prio_x_lost == None)
        ev_prio_x_lost = sm_main.get_ev_prio_x_lost(EventName.ntp_lost)
        self.assertTrue(ev_prio_x_lost.name == 'ev_prio_2_lost')
        ev_prio_x_found = sm_main.get_ev_prio_x_found(EventName.ntp_found)
        self.assertTrue(ev_prio_x_found.name == 'ev_prio_2_found')


    def test_sm_set_state_by_priority(self):
        g_call_sequence.clear()
        config = {'priority_list': ['PTP', 'NTP', 'GNSS', 'Ext. Osc.']}
        self.sm_data.mq_set_config(config)
        self.sm_data.sm_set_state_by_priority(StatePriority.prio_3)
        self.assertTrue(json.dumps(g_call_sequence).encode() == b'["_start_ts2phc", "_restart_ptp4l_free_running True", "_stop_phc2sys", "_add_ptp_chrony_sources"]')
        pass



    def test_sm_reset_services_states(self):
        g_call_sequence.clear()
        ptp_manager = PtpManager()
        alarm_manager = AlarmManager()
        config = {'priority_list': ['PTP', 'NTP', 'GNSS', 'Ext. Osc.']}
        sm_main = MainStateMachine(self.sm_data)
        self.sm_data.mq_set_config(config)
        sm_main.ev_config_update()
        self.assertTrue(json.dumps(g_call_sequence).encode() == \
         b'["alarm start ptpmanager_alarm", "ptp_manager_set_config {\\"priority_list\\": [\\"PTP\\", \\"NTP\\", \\"GNSS\\", \\"Ext. Osc.\\"]}"]')


    @mock.patch.object(MainStateMachineData, '_set_next_state')
    def test1_on_enter_st_prio_1_trans(self, mock_set_next_state):
        # with mock.patch.object(MainStateMachine, 'on_enter_st_prio_1_trans') as mock_method:
        sm_main = MainStateMachine(self.sm_data)
        config = {'priority_list': ['PTP', 'NTP', 'GNSS', 'Ext. Osc.']}
        self.sm_data.mq_set_config(config)
        sm_main.ev_config_update()
        sm_main.ev_prio_1_found()
        param_d = mock_set_next_state.call_args.args[0]
        self.assertTrue(param_d['name'] == StateName.ptp)




