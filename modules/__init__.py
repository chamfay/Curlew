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

from gi.repository import GLib

from modules.consts import CONF_FILE, USR_FFILE, CONF_PATH
from os.path import exists
import os

# Create ".curlew" folder if not exist
if not exists(CONF_PATH): os.mkdir(CONF_PATH)

# Create empty config file (curlew.cfg).
if not exists(CONF_FILE):
    conf = GLib.KeyFile()
    conf.set_string('configs', 'formats_file', USR_FFILE)
    conf.save_to_file(CONF_FILE)
    conf.unref()

