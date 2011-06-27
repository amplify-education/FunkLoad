# (C) 2011 Nuxeo SAS <http://nuxeo.com>
# Author: Krzysztof A. Adamski
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
import pkg_resources, re, pickle
import sys
from utils import render_template

ENTRYPOINT = 'funkload.plugins.monitor'

gd_colors=[['red', 0xff0000],
           ['green', 0x00ff00],
           ['blue', 0x0000ff],
           ['yellow', 0xffff00],
           ['purple', 0x7f007f],
          ] 

class MonitorPlugins():
    MONITORS = {}
    def __init__(self, conf=None):
        self.conf = conf
        self.enabled=None
        self.disabled=None
        if conf==None or not conf.has_section('plugins'):
            return
        if conf.has_option('plugins', 'monitors_enabled'):
            self.enabled=re.split(r'\s+', conf.get('plugins', 'monitors_enabled'))
        if conf.has_option('plugins', 'monitors_disabled'):
            self.disabled=re.split(r'\s+', conf.get('plugins', 'monitors_disabled'))

    def registerPlugins(self):
        for entrypoint in pkg_resources.iter_entry_points(ENTRYPOINT):
            p = entrypoint.load()(self.conf)
            if self.enabled!=None:
                if p.name in self.enabled:
                    self.MONITORS[p.name] = p
            elif self.disabled!=None:
                if p.name not in self.disabled:
                    self.MONITORS[p.name] = p
            else:
                self.MONITORS[p.name] = p

    def configure(self, config):
        for plugin in self.MONITORS.values():
            if config.has_key(plugin.name):
                plugin.setConfig(config[plugin.name])

class Plot:
    def __init__(self, plots, title="", ylabel="", unit="", **kwargs):
        self.plots=plots
        self.title=title
        self.ylabel=ylabel
        self.unit=unit
        for key in kwargs:
            setattr(self, key, kwargs[key])

    @property
    def ordered_plots(self):
        """
        Return the plots as (key, line_type, title) tuples

        Handle both dicts (the old style), and lists of tuples (the new style)
        """
        if isinstance(self.plots, dict):
            return [(k, l, t) for (k, (l, t)) in self.plots.items()]
        else:
            return self.plots
            

class MonitorPlugin(object):
    def __init__(self, conf=None):
        if not hasattr(self, 'name') or self.name == None:
            self.name=self.__class__.__name__
        if not hasattr(self, 'plots'):
            self.plots=[]
        self._conf = conf

    def _checkKernelRev(self):
        """Check the linux kernel revision."""
        version = open("/proc/version").readline()
        kernel_rev = float(re.search(r'version (\d+\.\d+)\.\d+',
                                     version).group(1))
        if (kernel_rev > 2.6) or (kernel_rev < 2.4):
            sys.stderr.write(
                "Sorry, kernel v%0.1f is not supported\n" % kernel_rev)
            sys.exit(-1)
        return kernel_rev

    def gnuplot(self, times, host, image_prefix, data_prefix, gplot_path, chart_size, stats):
        parsed=self.parseStats(stats)
        if parsed==None:
            return None

        image_path="%s.png" % image_prefix
        data_path="%s.data" % data_prefix

        data = [times]
        labels = ["TIME"]
        plot_descriptors = []
        for plot in self.plots:
            if len(plot.plots)==0:
                continue

            li=[]
            for p, line, title in plot.ordered_plots:
                data.append(parsed[p])
                labels.append(p)
                li.append((len(data), title, line))
            plot_descriptors.append((plot.title, plot.ylabel, plot.unit, li))
        
        with open(gplot_path, 'w') as gplot_file:
            gplot_file.write(render_template('gnuplot/monitor.mako',
                image_path=image_path,
                width=chart_size[0],
                height=chart_size[1],
                number_of_plots=len(plot_descriptors),
                plots=plot_descriptors,
                data_path=data_path,
            ))

        data = zip(*data)
        with open(data_path, 'w') as data_file:
            data_file.write(render_template('gnuplot/data.mako',
                labels=labels,
                data=([str(item) for item in line] for line in data),
            ))

        return [(self.name, image_path)]

    def getConfig(self):
        return pickle.dumps(self.plots).replace("\n", "\\n")

    def setConfig(self, config):
        config = str(config.replace("\\n", "\n"))
        self.plots = pickle.loads(config)

    def getStat(self):
        """ Read stats from system """
        pass
  
    def parseStats(self, stats):
        """ Parse MonitorInfo object list """
        pass
