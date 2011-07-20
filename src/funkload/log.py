import os
import time
from contextlib import contextmanager
from xml.sax.saxutils import XMLGenerator
from funkload.utils import get_version
from datetime import datetime

results_loggers = {}


def get_results_logger(path):
    global results_loggers
    if path in results_loggers:
        return results_loggers[path]
    else:
        return results_loggers.setdefault(path, ResultsLogger(path))


class XmlLogger(object):
    
    def __init__(self, path):
        if os.access(path, os.F_OK):
            os.rename(path, path + '.bak-' + str(int(time.time())))
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
