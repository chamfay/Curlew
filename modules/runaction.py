# -*- coding: utf-8 -*-

# Curlew - Easy to use multimedia converter
#
# Copyright (C) 2012-2017 Fayssal Chamekh <chamfay@gmail.com>
#
# Released under terms on waqf public license.
#
# Curlew is free software; you can redistribute it and/or modify it 
# under the terms of the latest version waqf public license as published by 
# ojuba.org.
#
# Curlew is distributed in the hope that it will be useful, but WITHOUT 
# ANY WARRANTY; without even the implied warranty 
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#        
# The latest version of the license can be found on:
# http://waqf.ojuba.org/license

from subprocess import Popen, PIPE
from gi.repository import GLib


# Error code
CODE_SUCCESS = 0
CODE_STOPPED = 9

class RunAction():
    def __init__(self, cmd):
        self._cmd = cmd
    
    def stop(self):
        try:
            self.fp.kill()
        except: pass
        
    def run(self, on_out_func, on_end_func):
        self.fp = Popen(self._cmd,
                        shell=False,
                        stdout=PIPE,
                        stderr=PIPE,
                        universal_newlines=True)
        GLib.io_add_watch(self.fp.stderr, GLib.IO_IN | GLib.IO_HUP,
                          self.on_output, on_out_func)
        GLib.child_watch_add(self.fp.pid, self.on_end, on_end_func)
    
    def on_output(self, src, cond, on_out_func):
        line = src.readline()
        if len(line) > 0:
            if line.find('time=') != -1:
                on_out_func(line.strip())
            return True
        return False
    
    def on_end(self, pid, code, on_end_func):
        on_end_func(code)




