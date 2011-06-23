import os.path
import threading
from Queue import Queue, Empty
from xmlrpclib import ServerProxy
from utils import get_version
import time


stats_queue = Queue()


class StatsWriterThread(threading.Thread):

    def __init__(self, output_filename, config={}):
        threading.Thread.__init__(self)
        self.output_fd = open(output_filename, "w+")
        self.shutdown_event = threading.Event()
        self._config = config

    def write_header(self, config):
        header = '<funkload version="{version}" time="{time}">\n'.format(
                            version=get_version(), time=time.time())
        self.output_fd.write(header)
        for key, value in config.items():
            stat = '<config key="{key}" value="{value}"/>\n'.format(key=key,
                                                                    value=value)
            self.output_fd.write(stat)

    def write_footer(self):
        self.output_fd.write("</funkload>\n")

    def shutdown(self):
        self.shutdown_event.set()

    def run(self):
        self.write_header(self._config)
        while 1:
            if self.shutdown_event.isSet():
                break

            # Get the record from the queue...
            try:
                record = stats_queue.get(timeout=2.0)
            except Empty:
                continue

            record += "\n"

            # Write it out the stats file
            self.output_fd.write(record)

            # Its always important to let the queue know we finished a task!
            stats_queue.task_done()

        self.write_footer()
        self.output_fd.close()


class StatsCollectionThread(threading.Thread):

    def __init__(self, host, port, interval, monitor_key=None):
        threading.Thread.__init__(self)
        self.interval = interval
        self.server = ServerProxy("http://%s:%s" % (host, port))
        self.shutdown_event = threading.Event()
        self.monitor_key = monitor_key

    def set_monitor_key(self, key):
        self.monitor_key = key

    def shutdown(self):
        self.shutdown_event.set()

    def run(self):
        while 1:
            if self.shutdown_event.isSet():
                return

            # Get the record from the monitored server
            record = self.server.getRecord()

            if self.monitor_key:
                # Add the monitor key to what we get back from the monitor server
                record = record.replace('/>', 'key="%s"/>' % self.monitor_key)

            # The deque is threadsafe, so append away
            stats_queue.put(record)

            # Use the sleep event to wait on an interval
            self.shutdown_event.wait(self.interval)


class StatsCollector(object):

    def __init__(self, monitor_hosts, output_dir=".", config={}, interval=0.5, monitor_key=None):
        self.monitor_threads = []
        for (host, port, desc) in monitor_hosts:
            self.monitor_threads.append(
                StatsCollectionThread(host, port, interval, monitor_key))

        output_file_path = os.path.join(output_dir, "stats.xml")
        self.stats_writer_thread = StatsWriterThread(output_file_path, config)

    def set_monitor_key(self, key):
        for t in self.monitor_threads:
            t.set_monitor_key(key)

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
