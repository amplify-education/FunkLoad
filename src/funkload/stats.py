import os.path
import threading
from Queue import Queue, Empty
from xmlrpclib import ServerProxy
from utils import trace
from xmlrpclib import Fault
from socket import error as SocketError
from funkload.log import get_stats_logger


stats_queue = Queue()


class StatsWriterThread(threading.Thread):

    def __init__(self, output_filename, config={}):
        threading.Thread.__init__(self)
        self.logger = get_stats_logger(output_filename)
        self.shutdown_event = threading.Event()
        self._config = config

    def shutdown(self):
        self.shutdown_event.set()

    def run(self):
        self.logger.start_log()
        for key, value in self._config.items():
            self.logger.config(key, value)

        is_shutting_down = False
        try:
            while 1:
                if self.shutdown_event.isSet():
                    is_shutting_down = True
                    break

                # Get the record from the queue...
                try:
                    fn, args, kwargs = stats_queue.get(timeout=2.0)
                except Empty:
                    continue

                # Write it out the stats file
                getattr(self.logger, fn)(*args, **kwargs)

                # Its always important to let the queue know we finished a task!
                stats_queue.task_done()
        finally:
            self.logger.end_log()
            if is_shutting_down:
                self.logger.xml_logger.output.flush()


class StatsCollectionThread(threading.Thread):

    def __init__(self, host, port, interval):
        threading.Thread.__init__(self)
        self.interval = interval
        self.server = ServerProxy("http://%s:%s" % (host, port))
        self.shutdown_event = threading.Event()
        self.host = host
        self.port = port

        try:
            trace("* Getting monitoring config from %s: ..." % self.host)
            config = self.server.getMonitorsConfig()

            for key, value in config.items():
                stats_queue.put(('monitor_config', [self.host, key, value], {}))
        except Fault:
            trace(' not supported.\n')
        except SocketError:
            trace(' failed, server is down.\n')
            raise
        else:
            trace(' done.\n')

    def shutdown(self):
        self.shutdown_event.set()

    def run(self):
        while 1:
            if self.shutdown_event.isSet():
                return

            # Get the record from the monitored server
            record = self.server.getRecord()

            # The deque is threadsafe, so append away
            stats_queue.put(('monitor', [], record))

            # Use the sleep event to wait on an interval
            self.shutdown_event.wait(self.interval)


class StatsCollector(object):

    def __init__(self, monitor_hosts, output_dir=".", config={}, interval=0.5):
        self.monitor_threads = []
        for (host, port, desc) in monitor_hosts:
            try:
                self.monitor_threads.append(
                    StatsCollectionThread(host, port, interval))
            except SocketError:
                pass

        output_file_path = os.path.join(output_dir, "stats.xml")
        self.stats_writer_thread = StatsWriterThread(output_file_path, config)

    def __enter__(self):
        # First, get the writer started
        self.stats_writer_thread.start()

        # Start the monitor threads...
        [t.start() for t in self.monitor_threads]

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Stop the monitor threads first
        [t.shutdown() for t in self.monitor_threads]
        [t.join() for t in self.monitor_threads]

        # For the output, we'll first wait for the stats_queue to finish up.
        # This is because we want to make sure all recorded stats get written!
        stats_queue.join()

        # Then, shut down the Writer thread
        self.stats_writer_thread.shutdown()
        self.stats_writer_thread.join()
