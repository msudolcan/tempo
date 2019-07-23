import os
import platform
import psutil
import sys
import threading
import time

from playsound import playsound


# Boolean flag to handle debug output
DEBUG = False

MILLISECOND = .001


def debug_print(msg: str) -> None:
    """
    Print a debug message

    :param msg: The message to print
    :return: None
    """
    if DEBUG:
        print(msg)


class ClickTrack(threading.Thread):

    def __init__(self, bpm):
        """

        :param bpm: Beats per minute
        :return: An instance of ClickTrack
        """
        super().__init__()

        self.beat_length_ms = (60.0 / float(bpm)) * 1000
        self.ticks = list()

        debug_print('All times in milliseconds')
        debug_print(f'Beat length: {self.beat_length_ms}')

        self.do_stop = False
        self.frequency = 2500
        self.duration = 125

    def _handle_externals(self, prev: float) -> None:
        """
        Handle all things external to the actual time keeping. This could
        involve anything from collecting debug information to sending out
        MIDI control signals.

        :param prev: The time of the previous tick (used for debug info)
        :return: None
        """
        # This should stay first
        if DEBUG:
            self.ticks.append(self._get_time_ms() - prev)

    @staticmethod
    def _get_time_ms() -> float:
        """
        Get the current time in milliseconds

        :return: The current time in milliseconds
        """
        return time.time_ns() / 1000000

    def _print_statistics(self) -> None:
        """
        Print program statistics if in DEBUG mode

        :return: None
        """
        if DEBUG:
            debug_print('*'*60)
            debug_print('Statistics: ')

            total = 0  # Used to compute average deviation
            max_deviation = 0

            for tick in self.ticks:
                # debug_print(tick)
                deviation = tick - self.beat_length_ms
                total += deviation
                if abs(deviation) > max_deviation:
                    max_deviation = deviation

            debug_print(f'Total ticks: {len(self.ticks)}')
            debug_print(f'Average deviation: {total / len(self.ticks)}')
            debug_print(f'Maximum deviation: {max_deviation}')
            debug_print('*'*60)

    def run(self) -> None:
        """
        This is the actual threaded function. It will run until self.do_stop
        is True.

        :return: None
        """

        if platform.system() == 'Windows':
            # If we're running on Windows, give this process a high priority
            p = psutil.Process(os.getpid())
            p.nice(psutil.HIGH_PRIORITY_CLASS)

        while not self.do_stop:

            prev = self._get_time_ms()
            playsound('beep_main.wav')

            """
            Get close to the next beat. Debug information tells us that
            maximum deviation is around 1 millisecond. Let's sleep to within
            some milliseconds of the next beat before starting the busy wait.
            """
            cushion = 15
            time.sleep(
                (self.beat_length_ms - (self._get_time_ms() - prev) - cushion)
                * MILLISECOND
            )

            # Get very close
            while self._get_time_ms() < (prev + self.beat_length_ms):
                # We want to be as close as possible, so let's busy wait
                pass
            self._handle_externals(prev)

        self._print_statistics()


def main(bpm: int):
    """
    Create an instance of ClickTrack and run it

    :param bpm: The beats per minute
    :return: None
    """
    click_track = ClickTrack(bpm)
    click_track.start()

    input('Press enter to stop')
    click_track.do_stop = True


if __name__ == "__main__":
    if len(sys.argv) != 2 or not int(sys.argv[1]):
        print('USAGE: metronome.py <bpm>')
        print(f'{" ".join(sys.argv)} [len: {len(sys.argv)}]')
    else:
        main(sys.argv[1])
