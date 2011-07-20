import os
import time
from contextlib import contextmanager
from xml.sax.saxutils import XMLGenerator
from funkload.utils import get_version
from datetime import datetime

loggers = {}

def get_results_logger(path):
    global loggers
    if path in loggers:
        return loggers[path]
    else:
        return loggers.setdefault(path, ResultsLogger(path))

def get_stats_logger(path):
    global loggers
    if path in loggers:
        return loggers[path]
    else:
        return loggers.setdefault(path, StatsLogger(path))

load_time = int(time.time())


class XmlLogger(object):
    
    def __init__(self, path):
        if os.access(path, os.F_OK):
            os.rename(path, path + '.bak-' + str(load_time))
        self.output = open(path, 'w')
        self.xml_gen = XMLGenerator(self.output, 'utf-8')

    def start_log(self, tag, attributes):
        self.doc_tag = tag
        self.xml_gen.startDocument()
        self.xml_gen.startElement(tag, attributes)

    def end_log(self):
        self.xml_gen.endElement(self.doc_tag)
        self.xml_gen.endDocument()

    @contextmanager
    def element(self, name, attrs={}):
        attrs = dict((key, str(value)) for key, value in attrs.items())
        self.text('\n')
        self.xml_gen.startElement(name, attrs)
        yield
        self.xml_gen.endElement(name)

    def text(self, text):
        self.xml_gen.characters(str(text))

class ResultsLogger(object):
    def __init__(self, path):
        self.xml_logger = XmlLogger(path)

    def start_log(self):
        self.xml_logger.start_log('funkload', {
            'version': get_version(),
            'time': datetime.now().isoformat()
        })

    def config(self, key, value, ns=None):
        if ns is not None:
            key = ':'.join((ns, key))

        with self.xml_logger.element('config', {'key': key, 'value': value}):
            pass

    def record(self, attributes, subitems, aggregates):
        with self.xml_logger.element('record', attributes):
            for key, value in subitems.items():
                with self.xml_logger.element(key):
                    self.xml_logger.text(value)

            for key, value in aggregates.items():
                with self.xml_logger.element('aggregate', {'name': key}):
                    self.xml_logger.text(value)

    def end_log(self):
        self.xml_logger.end_log()


class StatsLogger(object):
    def __init__(self, path):
        self.xml_logger = XmlLogger(path)

    def start_log(self):
        self.xml_logger.start_log('funkload', {
            'version': get_version(),
            'time': datetime.now().isoformat()
        })

    def config(self, key, value, ns=None):
        if ns is not None:
            key = ':'.join((ns, key))

        with self.xml_logger.element('config', {'key': key, 'value': value}):
            pass

    def monitor_config(self, host, key, value):
        with self.xml_logger.element('monitorconfig',
                {'host': host, 'key': key, 'value': value}):
            pass

    def monitor(self, **data):
        with self.xml_logger.element('monitor', data):
            pass

    def end_log(self):
        self.xml_logger.end_log()
