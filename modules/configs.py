# -*- coding: utf-8 -*-

# Curlew - Easy to use multimedia converter
#
# Copyright (C) 2012-2018 Fayssal Chamekh <chamfay@gmail.com>
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
from modules.consts import CONF_FILE

GROUP = 'configs'

def set_b_config(key, value):
    conf = GLib.KeyFile()
    conf.load_from_file(CONF_FILE, GLib.KeyFileFlags.NONE)
    conf.set_boolean(GROUP, key, value)
    conf.save_to_file(CONF_FILE)

def get_b_config(key):
    bool_value = True
    try:
        conf = GLib.KeyFile()
        conf.load_from_file(CONF_FILE, GLib.KeyFileFlags.NONE)
        bool_value = conf.get_boolean(GROUP, key)
    except:
        pass
    return bool_value

def set_s_config(key, value):
    conf = GLib.KeyFile()
    conf.load_from_file(CONF_FILE, GLib.KeyFileFlags.NONE)
    conf.set_string(GROUP, key, value)
    conf.save_to_file(CONF_FILE)

def get_s_config(key):
    str_value = ''
    try:
        conf = GLib.KeyFile()
        conf.load_from_file(CONF_FILE, GLib.KeyFileFlags.NONE)
        str_value = conf.get_string(GROUP, key)
    except:
        pass
    return str_value








