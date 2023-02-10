from pynput import mouse
import time
from datetime import datetime, timedelta
from sys import stderr
import argparse
import re
from decimal import Decimal

# === Constants ===
CLICK_INTERVAL_MINUTES = 5

_click_interval_seconds = CLICK_INTERVAL_MINUTES * 60
_eod = datetime.today().replace(hour=17, minute=0, second=0, microsecond=0)

# === Strings =====
INVALID_DELAY_REGEX = "Delay must be in [#h][#m][#s][#ms] format."
INVALID_TIME_REGEX = "Time must be in hh[:mm][p]p format."
INVALID_POSITION_REGEX = "Enter a Position in 'x,y' format"
POSITION_INFO_FORMATTING = " at {0}"


# ==================

# ======= Position Listener ==========
class PositionReader:
    def __init__(self):
        self.position = None

    def acquire_position(self):
        listener = mouse.Listener(
            on_click=self.on_click
        )

        listener.start()

    def on_click(self, x, y, button, pressed):
        if pressed:
            print('Selected position: {0}'.format((x, y)))
            self.position = (x, y)
            # stop listener
            return False


# ============================

class Duration:
    def __init__(self, d):
        self.h = 0 if 'h' not in d.keys() else d['h']
        self.m = 0 if 'm' not in d.keys() else d['m']
        self.s = 0 if 's' not in d.keys() else d['s']
        self.ms = 0 if 'ms' not in d.keys() else d['ms']

    def asSeconds(self):
        return self.h * 3600 + self.m * 60 + self.s + (self.ms / 1000)


def error(msg):
    print(msg, file=stderr)
    exit(1)


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--end', type=str, nargs='?', const=_eod, required=False)
    parser.add_argument('--start', type=str, required=False)
    parser.add_argument('--delay', type=str, required=False)
    parser.add_argument('--position', type=str, nargs='?', const='', required=False)
    parser.add_argument('--verbose', action='store_true', required=False)

    return parser.parse_args()


def click(mMouse, position=None):
    # Move to desired position (default to current position)
    curr_pos = mMouse.position
    if position is None:
        position = curr_pos
    mMouse.position = position

    # execute click
    mMouse.press(mouse.Button.left)
    mMouse.release(mouse.Button.left)

    # return to previous (d: current) position
    mMouse.position = curr_pos


def _time_parse_helper(s):
    # s is '1h', '3ms', '4m' etc
    patt = re.compile(r'^(\d+)([hms]{1,2})$')
    m = patt.match(s)
    return m.groups()


def _isPM(s):
    return s.lower() in ['p', 'pm']


def _isTomorrow(dt):
    return dt < datetime.today()


def _interactive_mode():
    reader = PositionReader()

    print("Click the position to be used...")
    reader.acquire_position()

    while (res := reader.position) is None:
        pass

    return res


def parse_delay(delay_string):
    if delay_string is None:
        return None

    patt = re.compile(r'^(\d+h){0,1}(\d+m){0,1}(\d+s){0,1}(\d+ms){0,1}$')
    if ((m := patt.match(delay_string)) is None):
        error(INVALID_DELAY_REGEX)

    comp_dict = dict()

    for g in m.groups():
        if g is not None:
            comp = _time_parse_helper(g)
            comp_dict[comp[1]] = int(comp[0])

    return Duration(comp_dict).asSeconds()


def parse_time(time_string):
    if time_string is None:
        return None

    patt = re.compile(r'^(\d{1,2}):{0,1}([0-5][0-9]){0,1}([ap]|[ap]m)$')
    if ((m := patt.match(time_string)) is None):
        error(INVALID_TIME_REGEX)

    # option one: [hour, minutes, meridian]
    # option two: [hour, NONE, meridian]
    gs = m.groups()
    hour = int(gs[0].replace("12", "00")) % 12
    minute = int("00" if gs[1] is None else gs[1])
    meri = gs[2]

    if _isPM(meri):
        hour = int(hour) + 12

    dt = datetime.today().replace(hour=hour, minute=minute, second=0, microsecond=0)
    # if time specified is in past, set to tomorrow.
    # dt += timedelta(days=int(dt < datetime.today()))

    return dt


def parse_position(position_string):
    if position_string is None:
        return None

    if not position_string:
        return _interactive_mode()

    patt = re.compile(r'[\(\)\[\]{}]*')
    sani_ps = patt.sub('', position_string)

    patt2 = re.compile(r'^([\d.])+,([\d.]+)$')
    if ((m := patt2.match(sani_ps)) is None):
        error(INVALID_POSITION_REGEX)

    xs, ys = m.groups()
    return Decimal(xs), Decimal(ys)


def execute_click_loop(mMouse, start, end, position, interval, verbose):
    while True:
        # skip click before start time
        if start is not None and datetime.now() < start:
            continue

        # trip at end time
        if end is not None and datetime.now() > end:
            if verbose:
                print(f"{datetime.now()} is later than {end}, exiting.")
            exit(0)

        if verbose:
            position_info = POSITION_INFO_FORMATTING.format(position) if position is not None else ''
            print(f"{datetime.now()} is not later than {end}, clicking{position_info}.")

        click(mMouse, position)

        time.sleep(interval)


def main():
    # -- Setup and arg parsing --
    mMouse = mouse.Controller()
    stop_at_eod = False

    args = get_args()
    delay = parse_delay(args.delay)
    start_time = parse_time(args.start)
    end_time = parse_time(args.end)
    position = parse_position(args.position)
    verbose = args.verbose

    # -- Update globals --
    click_interval = delay if delay is not None else _click_interval_seconds

    if verbose:
        print(f"Verbose set to {verbose}.")
        print(f"Using a delay of {delay} seconds.")
        print(f"Using a start time of {str(start_time)}.")
        print(f"Using an end time of {str(end_time)}.")
        print(f"Using position {position} for click.")

    # -- Main loop --
    execute_click_loop(mMouse, start_time, end_time, position, click_interval, verbose)


if __name__ == "__main__":
    main()

# Ideas
#	X -p = position mode, or default position
#		- return mouse to original position after click
#	X -t = delay mode (user specifies click delay)
#		- -t and default value 5m
#   X -d better eod mode (user specifies eod)
#		- -d and default value 5p
#	X argparse
# 	- logging
# 	X verbose mode