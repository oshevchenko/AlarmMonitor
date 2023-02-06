# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

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


class AlarmMonitor(StateMachine):
    """Monitor Alarms state machine"""

    alarm_timer = 0
    idle = State("Idle", initial=True)
    running = State("Running")
    alarm = State("Alarm")

    ev_stop = running.to(idle) | alarm.to(idle)
    ev_start = idle.to(running)
    ev_reset = running.to.itself()
    ev_tick = running.to(alarm, cond=["timer_expired", "alarm_on_timeout"]) | \
              alarm.to(running, cond=["alarm_timer_expired", "auto_ack"])
    ev_alarm = running.to(alarm)
    ev_clear = alarm.to(running)

    def __init__(self, name, alarm_on_timeout=True, alarm_timeout=5, auto_ack=False, auto_ack_delay=0):
        self.name = name
        self.alarm_timeout = alarm_timeout
        self.timer = alarm_timeout
        self.auto_ack = auto_ack
        self.alarm_on_timeout = alarm_on_timeout
        self.auto_ack_delay = auto_ack_delay
        self.calls = []
        super().__init__()

    def on_ev_tick(self, event: str, source: State, target: State, message: str = ""):
        message = ". " + message if message else ""
        if source.id == "alarm" and target.id == "running":
            print("TODO: Send Alarm Clear message")
        return f"Running {event} from {source.id} to {target.id}{message}"

    def on_enter_running(self):
        self.timer = self.alarm_timeout

    def on_enter_alarm(self):
        self.alarm_timer = self.auto_ack_delay
        print("TODO: Send Alarm message")

    def auto_ack(self):
        return self.auto_ack

    def alarm_on_timeout(self):
        return self.alarm_on_timeout

    def timer_expired(self):
        ret = False
        if self.timer != 0:
            self.timer -= 1
        if self.timer == 0:
            ret = True
        return ret

    def alarm_timer_expired(self):
        ret = False
        if self.alarm_timer != 0:
            self.alarm_timer -= 1
        if self.alarm_timer == 0:
            ret = True
        return ret

class TrafficLightMachine(StateMachine):
    """A traffic light machine"""
    green = State("Green", initial=True)
    yellow = State("Yellow")
    red = State("Red")

    cycle = green.to(yellow) | yellow.to(red) | red.to(green)

    slowdown = green.to(yellow)
    stop = yellow.to(red)
    go = red.to(green)

    def before_cycle(self, event: str, source: State, target: State, message: str = ""):
        message = ". " + message if message else ""
        return f"Running {event} from {source.id} to {target.id}{message}"

    def on_enter_red(self):
        print("Don't move.")

    def on_exit_red(self):
        print("Go ahead!")



# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    # print_hi('PyCharm')
    # traffic_light = TrafficLightMachine()
    # graph = DotGraphMachine(TrafficLightMachine)
    # dot = graph()
    # dot.write_png("TrafficLightMachine_initial.png")
    # print(dot.to_string())
    # traffic_light.cycle()
    # print(traffic_light.cycle())
    # traffic_light.current_state

    uart_alarm_monitor = AlarmMonitor("uart", auto_ack=True, auto_ack_delay=5)
    uart_alarm_monitor.add_observer(LogObserver("uart"))
    uart_alarm_monitor.ev_start()

    for i in range(15):
        try:
            if i == 3:
                uart_alarm_monitor.ev_reset()

            print(uart_alarm_monitor.timer)
            uart_alarm_monitor.ev_tick()

        except TransitionNotAllowed:
            pass

    graph = DotGraphMachine(AlarmMonitor)
    dot = graph()
    dot.write_png("AlarmMonMachine_initial.png")
    # See PyCharm help at https://www.jetbrains.com/help/pycharm/
