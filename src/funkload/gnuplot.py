import os
import sys
from commands import getstatusoutput

def gnuplot(script_path):
    """Execute a gnuplot script."""
    path = os.path.dirname(os.path.abspath(script_path))
    if sys.platform.lower().startswith('win'):
        # commands module doesn't work on win and gnuplot is named
        # wgnuplot
        ret = os.system('cd "' + path + '" && wgnuplot "' +
                        os.path.abspath(script_path) + '"')
        if ret != 0:
            raise RuntimeError("Failed to run wgnuplot cmd on " +
                               os.path.abspath(script_path))

    else:
        cmd = 'cd ' + path + '; gnuplot ' + os.path.abspath(script_path)
        ret, output = getstatusoutput(cmd)
        if ret != 0:
            raise RuntimeError("Failed to run gnuplot cmd: " + cmd +
                               "\n" + str(output))

def gnuplot_scriptpath(base, filename):
    """Return a file path string from the join of base and file name for use
    inside a gnuplot script.

    Backslashes (the win os separator) are replaced with forward
    slashes. This is done because gnuplot scripts interpret backslashes
    specially even in path elements.
    """
    return os.path.join(base, filename).replace("\\", "/")

def strictly_monotonic(sequence):
    """
    Return whether the sequence is strictly monotonic increasing with
    length greater than 1

    If true, then the sequence can safely be used as a gnuplot x axis,
    otherwise use xticlabels
    """
    if len(sequence) <= 1:
        return False

    for fst, snd in zip(sequence, sequence[1:]):
        if snd <= fst:
            return False

    return True
