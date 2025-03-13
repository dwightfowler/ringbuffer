import subprocess
import serial
import threading
import re
import queue
import signal
import sys
from abc import ABC, abstractmethod
from enum import Enum

class TestResult(Enum):
    ERROR = "error"
    CONTINUE = "continue"
    DONE = "done"


class AquanaTestFramework:
    def __init__(self):
        self.serial = SerialInterface()
        self.rtt = RTTInterface()
        self.build = BashBuild()  # Default implementation
        self.queue = SerialQueue()
        self.switch = CentralSwitch(self.queue)
        self.database = DatabaseManager()
        self.logger = LogManager()

    def run_test_suite(self, test_directory):
        """Discover and execute all test scripts in the given directory."""
        pass  # To be implemented


class BuildManager(ABC):
    @abstractmethod
    def execute(self):
        """Run the build process."""
        pass


class BashBuild(BuildManager):
    def execute(self):
        """Run the Bash script for build or firmware flashing with error handling, ensuring correct working directory."""
        build_dir = "/home/dev/aquana/SDK17/tools"

        try:
            process = subprocess.Popen(
                ["bash", "-c", ". build Test && up"],
                cwd=build_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Stream stdout line by line
            for line in process.stdout:
                print(line, end="")

            # Capture stderr at the end
            stderr_output = process.stderr.read()
            if stderr_output:
                print(f"Error Output:\n{stderr_output}")

            process.wait()

            if process.returncode != 0:
                raise subprocess.CalledProcessError(process.returncode, cmd="build/up", output=stderr_output)

            print("Build and firmware flash completed successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Build or flashing failed: {e}")
            print(f"Error Output:\n{e.stderr}")


class SerialInterface:
    def __init__(self):
        self.port = None
        self.baudrate = 115200
        self.timeout = 1
        self.thread = None
        self.queue = None
        self.show = threading.Event()
        self.show.clear()  # Start with output disabled

    def connect(self, port, queue):
        """Initialize and start reading from the serial CLI."""
        self.queue = queue
        self.port = serial.Serial(port, self.baudrate, timeout=self.timeout)
        self.thread = threading.Thread(target=self._read_serial, daemon=True)
        self.thread.start()

     def send_command(self, command):
        if self.port:
            self.port.write(f"{command}\n".encode())  # Send the command to the device
            print(f"Sent command: {command}")
        else:
            print("Serial port is not connected.")

   def _read_serial(self):
        """Continuously read serial data."""
        ansi_escape = re.compile(r'(?:[@-Z\-_]|\[[0-?]*[ -/]*[@-~])')
        self.show.wait()  # Block output until enabled
        while True:
            try:
                raw_line = self.port.readline().decode(errors='ignore')
                if self.show.is_set():
                    print(raw_line, end="")  # Preserve VT-102 formatting
                clean_line = ansi_escape.sub('', raw_line).strip()
                if clean_line:
                    self.queue.push(clean_line)
            except serial.SerialException:
                break


class SerialQueue:
    def __init__(self):
        self.queue = queue.Queue()

    def push(self, line):
        """Store a new serial log line."""
        self.queue.put(line)

    def pull(self):
        """Retrieve the next line for processing."""
        return self.queue.get()


class CentralSwitch:
    def __init__(self, queue):
        self.queue = queue
        self.tests = []
        self.active_test = None
        self.thread = threading.Thread(target=self._process_serial_queue, daemon=True)
        self.thread.start()

    def register_test(self, test):
        self.tests.append(test)

    def _process_serial_queue(self):
        """Pull serial lines and direct them to active tests."""
        while True:
            line = self.queue.pull()
            if self.active_test:
                result = self.active_test.process_line(line)
                if result == TestResult.DONE:
                    print(f"{self.active_test.__class__.__name__} completed successfully.")
                    self.active_test = None
                elif result == TestResult.ERROR:
                    print("Test failed. Stopping execution.")
                    break
            else:
                for test in self.tests:
                    if test.is_triggered(line):
                        test.reset()
                        self.active_test = test
                        print(f"Activated: \x1B[32m{test.__class__.__name__}\x1B[0m")
                        break


class BaseTest(ABC):
    def __init__(self):
        self.passed = False
        self.failed = False
        self.detected_markers = set()

    @abstractmethod
    def is_triggered(self, line):
        pass

    @abstractmethod
    def process_line(self, line):
        pass

    def reset(self):
        self.passed = False
        self.failed = False
        self.detected_markers.clear()

class BootupTest(BaseTest):
    def __init__(self):
        super().__init__()
        self.markers = [
            "Aquana SV Bootloader",  # Exact string match
            "AQSV Started",          # Exact string match
            "START_APPLICATION_EVT", # Exact string match
            "Calibrated temp:",      # Exact string match
        ]

    def is_triggered(self, line):
        return self.markers[0] in line

    def process_line(self, line):
        for marker in self.markers:
            if marker in line:
                self.detected_markers.add(marker)
                print(f"\x1B[32mDetected: {marker}\x1B[0m")

        if self.markers[-1] in self.detected_markers:
            print(f"{self.__class__.__name__} done")
            return TestResult.DONE
        return TestResult.CONTINUE


class CheckinTest(BaseTest):
    def __init__(self):
        super().__init__()
        self.trigger = "WAN_COMMS_TIMER_EVT"
        self.markers = [
            "WAN power supply enabled",
            "WAN power-up complete",
            "cellular_net_registration, Activated IP:",
            "POST OK",
            "Wan_Comms_Timeout_Timer_Stop"
        ]

    def is_triggered(self, line):
        return self.trigger in line

    def process_line(self, line):
        for marker in self.markers:
            if marker in line:
                self.detected_markers.add(marker)
                print(f"\x1B[32mDetected: {marker}\x1B[0m")
        if self.markers[-1] in self.detected_markers:
            print(f"{self.__class__.__name__} done")
            return TestResult.DONE
        return TestResult.CONTINUE


class RTTInterface:
    def __init__(self):
        self.process = None

    def connect(self):
        """Start JLinkRTTClient as a subprocess and capture output."""
        pass  # To be implemented

    def send_command(self, command):
        """Send a command through RTT."""
        pass  # To be implemented

    def read_response(self, timeout=5, stop_pattern=None):
        """Read RTT output until timeout or stop pattern (regex) is found."""
        pass  # To be implemented


class LogManager:
    def __init__(self):
        """Handles JSON logging and session tagging."""
        pass  # To be implemented

    def start_new_session(self):
        """Initialize a new test session log."""
        pass  # To be implemented

    def log_event(self, message, level="INFO"):
        """Log an event to JSON with timestamps."""
        pass  # To be implemented


class DatabaseManager:
    def __init__(self, db_type="sqlite"):
        self.db_type = db_type

    def initialize(self):
        """Set up the database schema for logging test results."""
        pass  # To be implemented

    def store_test_result(self, test_name, status, details):
        """Store a test result entry in the database."""
        pass  # To be implemented

    def query_results(self, filter_conditions):
        """Query stored test results with filtering conditions."""
        pass  # To be implemented


def signal_handler(sig, frame):
    print("\nGracefully shutting down...")
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)


def Main():
    framework = AquanaTestFramework()
    serial_port = "/dev/ttyUSB0"
    framework.serial.connect(serial_port, framework.queue)
    framework.switch.register_test(BootupTest())
    framework.switch.register_test(CheckinTest())

    try:
        print("Starting Aquana Test Framework...")
        framework.build.execute()
    except Exception as e:
        print(f"Build process failed: {e}")
        sys.exit(1)

    framework.serial.show.set()  # Re-enable serial output
    print("Build process completed. Press Ctrl+C to exit.")
    while True:
        signal.pause()  # Keep running to display device output


if __name__ == "__main__":
    Main()
