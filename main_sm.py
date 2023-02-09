from statemachine import StateMachine, State
from statemachine.exceptions import TransitionNotAllowed
from statemachine.contrib.diagram import DotGraphMachine

class LogObserver(object):
    def __init__(self, name):
        self.name = name

    def after_transition(self, event, source, target):
        print(f"{self.name} after: {source.id}--({event})-->{target.id}")

    def on_enter_state(self, target, event):
        print(f"{self.name} enter: {target.id} from {event}")




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

    TRANS_TIMEOUT=5

    def __init__(self, name):
        super().__init__()

    def on_enter_idle(self):
        self.timer = self.TRANS_TIMEOUT
        print("TODO: Start timer")
        pass

    def on_enter_st_prio_1_trans(self):
        """Start timer, set prio1 state configuration."""
        self.timer = self.TRANS_TIMEOUT
        print("TODO: Start timer, set prio1 state configuration.")
        pass

    def on_enter_st_prio_2_trans(self):
        """Start timer, set prio2 state configuration."""
        self.timer = self.TRANS_TIMEOUT
        print("TODO: Start timer, set prio2 state configuration.")
        pass

    def on_enter_st_prio_3_trans(self):
        """Start timer, set prio3 state configuration."""
        self.timer = self.TRANS_TIMEOUT
        print("TODO: Start timer, set prio3 state configuration.")
        pass

    def on_enter_st_manual_trans(self):
        """Set manual state configuration."""
        print("TODO: Set manual state configuration.")
        pass

    def ext_osc_in_sync(self):
        """Return True if external oscillator is synchronized beforehand."""
        print("TODO: Return True if external oscillator was synchronized beforehand.")
        pass

    def on_ev_config_update(self, event: str, source: State, target: State, message: str = ""):
        message = ". " + message if message else ""

        # if source.id is in self.stable_states and target.id == "st_idle":
        print("TODO: Set all PTP4L services states to UNDEFINED.")

    def timer_expired(self):
        ret = False
        if self.timer != 0:
            self.timer -= 1
        if self.timer == 0:
            ret = True
        return ret


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

