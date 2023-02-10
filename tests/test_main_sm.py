from unittest import TestCase
from main_sm import MainStateMachine
import mock
from statemachine.exceptions import TransitionNotAllowed

# Launching unittests with arguments
# python -m unittest tests.test_main_sm.TestMainStateMachine
# in C:\Users\shevc\PycharmProjects\AlarmMonitor


class TestMainStateMachine(TestCase):
    def test_on_enter_idle(self):
        sm_main = MainStateMachine("main")
        sm_main.ev_config_update()
        self.assertTrue(sm_main.st_idle.is_active)

    @mock.patch.object(MainStateMachine, 'on_enter_st_idle')
    @mock.patch.object(MainStateMachine, 'on_enter_st_prio_1_trans')
    def test_on_enter_st_prio_1_trans(self, mock_on_enter_st_prio_1_trans,
                                      mock_on_enter_st_idle):
        # with mock.patch.object(MainStateMachine, 'on_enter_st_prio_1_trans') as mock_method:
        sm_main = MainStateMachine("main")
        sm_main.ev_config_update()
        self.assertTrue(mock_on_enter_st_idle.called)
        sm_main.ev_prio_1_found()
        self.assertTrue(sm_main.st_prio_1_trans.is_active)
        self.assertTrue(mock_on_enter_st_prio_1_trans.called)

    @mock.patch.object(MainStateMachine, 'on_enter_st_prio_2_trans')
    def test_on_enter_st_prio_2_trans(self, mock_on_enter_prio_2_trans):
        sm_main = MainStateMachine("main")
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
        sm_main = MainStateMachine("main")
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
        sm_main = MainStateMachine("main")
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
        sm_main = MainStateMachine("main")
        sm_main.ev_config_update()
        sm_main.ev_timeout()
        self.assertTrue(mock_ext_osc_in_sync.called)
        self.assertTrue(mock_on_enter_st_manual_ext_osc_trans.called)
        self.assertTrue(sm_main.st_manual_ext_osc_trans.is_active)
        sm_main.ev_timeout()
        self.assertTrue(sm_main.st_manual_ext_osc.is_active)

