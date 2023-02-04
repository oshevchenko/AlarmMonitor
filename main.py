# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

from statemachine import StateMachine, State
from statemachine.contrib.diagram import DotGraphMachine


class AlarmMonitor(StateMachine):
    """Monitor Alarms state machine"""
    ALARM_TIMEOUT = 5
    timer = ALARM_TIMEOUT
    idle = State("Idle", initial=True)
    running = State("Running")
    alarm = State("Alarm")

    ev_stop = running.to(idle) | alarm.to(idle)
    ev_start = idle.to(running)
    ev_reset = running.to.itself()
    ev_tick = running.to(alarm, cond="timer_expired") | \
              alarm.to(running, cond=["timer_expired", "ack"])
    ev_alarm = running.to(alarm)

    def __init__(self, name, ack, ack_timeout):
        self.name = name
        self.ack = ack
        self.ack_timeout = ack_timeout
        self.calls = []
        super().__init__()

    def before_ev_start(self, event: str, source: State, target: State, message: str = ""):
        message = ". " + message if message else ""
        return f"Running {event} from {source.id} to {target.id}{message}"

    def before_ev_tick(self, event: str, source: State, target: State, message: str = ""):
        message = ". " + message if message else ""
        if source.id == "alarm" and target.id == "running":
            print("Send Alarm Clear message")
        return f"Running {event} from {source.id} to {target.id}{message}"

    def on_enter_running(self):
        self.timer = self.ALARM_TIMEOUT

    def on_enter_alarm(self):
        self.timer = self.ack_timeout
        print("Send Alarm message")

    def ack(self):
        return self.ack
    def timer_expired(self):
        ret = False
        if self.timer != 0:
            self.timer -= 1
        if self.timer == 0:
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


def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press Ctrl+F8 to toggle the breakpoint.


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print_hi('PyCharm')
    traffic_light = TrafficLightMachine()
    graph = DotGraphMachine(TrafficLightMachine)
    dot = graph()
    dot.write_png("TrafficLightMachine_initial.png")
    print(dot.to_string())
    traffic_light.cycle()
    print(traffic_light.cycle())
    traffic_light.current_state

    uart_alarm_monitor = AlarmMonitor("uart", True, 5)
    print(uart_alarm_monitor.ev_start())

    for i in range(15):
        try:
            if i == 3:
                print(uart_alarm_monitor.ev_reset())

            print(uart_alarm_monitor.timer)
            print(uart_alarm_monitor.ev_tick())


        except Exception:
            pass

    graph = DotGraphMachine(AlarmMonitor)
    dot = graph()
    dot.write_png("AlarmMonMachine_initial.png")
# See PyCharm help at https://www.jetbrains.com/help/pycharm/
