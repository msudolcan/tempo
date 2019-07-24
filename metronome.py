import os
import platform
import psutil
import sys
import threading
import time
import winsound


# Boolean flag to handle debug output
DEBUG = False

MIN_BPM = 30
MAX_BPM = 300
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

        self.beat_length_ms = (60.0 / float(bpm)) / MILLISECOND

        # Load the audio file into memory to minimize latency
        self.beep = None
        with open('beep_main.wav', 'rb') as file:
            self.beep = file.read()

        self.ticks = list()

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
            self.ticks.append(prev)

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
            # First convert the list of timestamps to a list of differences.
            # We want to keep logic at a minimum during thread execution
            _differences = list()
            # Ignore last beat
            for index, tick in enumerate(self.ticks[:-1]):
                _differences.append(
                    abs(self.ticks[index + 1] - tick)
                )

            debug_print('*'*60)
            debug_print('Statistics: (First beat ignored)')
            _differences = _differences[1:]

            debug_print('All times in milliseconds')
            debug_print(f'Beat length: {self.beat_length_ms}')

            total = 0  # Used to compute average deviation
            max_deviation = 0

            for difference in _differences:
                deviation = abs(difference - self.beat_length_ms)
                total += deviation
                if deviation > max_deviation:
                    max_deviation = deviation

            debug_print(f'Total ticks: {len(self.ticks)}')
            debug_print(f'Average deviation: {total / len(_differences)}')
            debug_print(f'Maximum deviation: {max_deviation}')
            debug_print('*'*60)

    def _tick(self) -> float:
        """
        Handle the beat

            NOTE: There is a large (approximately 50 ms) delay between the
            first and second call to winsound.PlaySound. There doesn't appear
            to be anything we can do about it.

        :return: The time of the tick
        """
        time_ms = self._get_time_ms()

        winsound.PlaySound(self.beep, winsound.SND_MEMORY)
        # We're sending in the time including audio file delay for debug info
        self._handle_externals(self._get_time_ms())

        return time_ms

    def run(self) -> None:
        """
        This is the actual threaded function. It will run until self.do_stop
        is True.

        :return: None
        """

        # Let's perform platform specific operations
        if platform.system() == 'Windows':
            # If we're running on Windows, give this process a high priority
            debug_print('Elevating Windows priority')
            p = psutil.Process(os.getpid())
            p.nice(psutil.HIGH_PRIORITY_CLASS)

        # First things first. Let's tick.
        # tick_current = self._tick()
        # tick_next = tick_current + self.beat_length_ms
        tick_next = 0

        # Let's define the thread variables
        cushion = 10 * MILLISECOND

        while not self.do_stop:
            """
            Get close to the next beat. Debug information tells us that
            maximum deviation is somewhere between 1 and 2 milliseconds. Let's 
            sleep to within some cushion number of milliseconds to the next 
            beat before starting to busy wait.
            """

            # We want to get as close as possible, so let's busy wait
            while self._get_time_ms() < tick_next:
                pass

            # This is at the end of the loop so the actual condition checking
            # is incorporated into the wait time.
            tick_current = self._tick()
            tick_next = tick_current + self.beat_length_ms

            time.sleep(
                (tick_next - cushion - self._get_time_ms()) * MILLISECOND
            )

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
    if len(sys.argv) < 2:
        print('USAGE: metronome.py <bpm> [<bpm> ...]')
        print(f'{" ".join(sys.argv)} [len: {len(sys.argv)}]')
    else:
        # Passed the sanity test. Let's now verify the bpm
        for _tempo in sys.argv[1:]:
            _bpm = int(_tempo)
            if not (MIN_BPM <= _bpm <= MAX_BPM):
                print(f'bpm must be between {MIN_BPM} and {MAX_BPM}')
            else:
                main(_bpm)
