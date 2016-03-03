# -*- coding: utf-8 -*-

# Curlew - Easy to use multimedia converter
#
# Copyright (C) 2012-2016 Fayssal Chamekh <chamfay@gmail.com>
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
# http://www.ojuba.org/wiki/doku.php/waqf/license


import gi
gi.require_version('Gtk', '3.0')

from gi.repository import Gtk
from subprocess import Popen, PIPE

def show_message(parent,
                 message,
                 message_type,
                 button_type=Gtk.ButtonsType.CLOSE):
    ''' Show custom message dialog'''
    mess_dlg = Gtk.MessageDialog(parent,
                             Gtk.DialogFlags.MODAL,
                             message_type,
                             button_type)
    mess_dlg.set_markup(message)
    if not parent:
        mess_dlg.set_keep_above(True)
    resp = mess_dlg.run()
    mess_dlg.destroy()
    return resp

def get_format_size(size):
    ''' formating file size '''
    size_str = ''
    if 0 <= size <= 1024:
        size_str = '{:.2f}'.format(size) + _(' KB')
    elif 1024 <= size < 1024 * 1024:
        e_size = size / 1024.0
        size_str = '{:.2f}'.format(e_size) + _(' MB')
    elif size >= 1024 * 1024:
        e_size = size / 1048576.0
        size_str = '{:.2f}'.format(e_size) + _(' GB')
    return size_str


def duration_to_time(duration):
    ''' Convert duration (sec) to time 0:00:00 '''
    if duration < 0: duration = 0
    return '{:.0f}:{:02.0f}:{:02.0f}'.format(
                                             duration/3600,
                                             (duration%3600)/60,
                                             (duration%3600)%60
                                             )

def time_to_duration(time):
    ''' Convert time like 0:00:00.00 to duration (sec)'''
    times = time.split(':')
    return int(times[0])*3600 + int(times[1])*60 + float(times[2])

def get_available_codecs(encoder):
    proc = Popen('{} -encoders'.format(encoder), shell=True,
               stdout=PIPE, stderr=PIPE, universal_newlines=True, bufsize=-1)
    codecs = proc.stdout.read()
    return codecs

def check_codec(encoder, codec):
    new_codec = ' {} '.format(codec)
    codecs = get_available_codecs(encoder)
    if new_codec in codecs:
        return True
    return False


