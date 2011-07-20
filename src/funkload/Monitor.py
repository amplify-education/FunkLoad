# (C) Copyright 2005-2011 Nuxeo SAS <http://nuxeo.com>
# Author: bdelbosc@nuxeo.com
# Contributors: 
#   Krzysztof A. Adamski
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as published
# by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA
# 02111-1307, USA.
#
"""
A Linux monitor server/controller.
"""
import sys
from time import time, sleep

from XmlRpcBase import XmlRpcBaseServer, XmlRpcBaseController
from MonitorPlugins import MonitorPlugins


# ------------------------------------------------------------
# Server
#
class MonitorServer(XmlRpcBaseServer):
    """The XML RPC monitor server."""
    server_name = "monitor"
    method_names = XmlRpcBaseServer.method_names + ['getRecord', 'getMonitorsConfig']

    def __init__(self, argv=None):
        XmlRpcBaseServer.__init__(self, argv)
        self.plugins=MonitorPlugins(self._conf)
        self.plugins.registerPlugins()

    def _init_cb(self, conf, options):
        """init procedure intend to be implemented by subclasses.

        This method is called before to switch in daemon mode.
        conf is a ConfigParser object."""
        self._conf = conf

    def getMonitorsConfig(self):
        ret = {}
        for plugin in (self.plugins.MONITORS.values()):
            conf = plugin.getConfig()
            if conf:
                ret[plugin.name] = conf
        return ret

    def getRecord(self):
        """ Returns the Monitor info at this point in time """
        ret = {}
        ret['time'] = time()
        ret['host'] = self.host
        for plugin in (self.plugins.MONITORS.values()):
            for key, value in plugin.getStat().items():
                ret[key] = str(value)
        return ret

# ------------------------------------------------------------
# Controller
#
class MonitorController(XmlRpcBaseController):
    """Monitor controller."""
    server_class = MonitorServer

    def test(self):
        """Testing monitor server."""
        server = self.server
        key = 'internal_test_monitor'
        server.startRecord(key)
        sleep(2)
        server.stopRecord(key)
        self.log(server.getXmlResult(key))
        return 0


def main():
    """Control monitord server."""
    ctl = MonitorController()
    sys.exit(ctl())


def test():
    """Test wihtout rpc server."""
    mon = MonitorServer()
    mon.test()

if __name__ == '__main__':
    main()
