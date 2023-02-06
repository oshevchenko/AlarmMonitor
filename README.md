# Alarm monitor class

```
class AlarmMonitor(StateMachine):
	ALARM_TIMEOUT = 5
...
	def __init__(self, name, alarm_on_timeout=True, auto_ack=False, auto_ack_delay=0):
```
## Parameters
1. `alarm_on_timeout` - if `True` go from **running** to **alarm** state after `ALARM_TIMEOUT` seconds.
2. `auto_ack` - Go from **alarm** to **running** state after `auto_ack_delay` seconds.


![Monitor alarms state machine](https://github.com/oshevchenko/AlarmMonitor/blob/master/AlarmMonMachine_initial.png?raw=true)


## States
**idle** - Initial state. No actions until `ev_start` is received.


**running** - Normal operation. Timer is decremented on `ev_tick`. Switch to **alarm**
state occures after timer is expired (if `alarm_on_timeout` is `True`). Go to **idle** on `ev_stop`.


**alarm** - Alarm state. Timer is decremented on `ev_tick`. Go to **running** on timeout 
after `auto_ack_delay` seconds if `auto_ack` is `True`.
Go to **running** on `ev_clear`. Go to **idle** on `ev_stop`.

## Events
1. `ev_start` - Start monitoring.
2. `ev_stop` - Stop monitoring, go to **idle** state.
3. `ev_reset` - Reset the `timer`, prevent switching to **alarm** state on timeout (if `alarm_on_timeout` is `True`).
4. `ev_tick` - Event from timer (once per second).
5. `ev_alarm` - Go to **alarm** state from **running** state.
6. `ev_clear` - Go to **running** state from **alarm** state.




