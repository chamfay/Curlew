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
# http://waqf.ojuba.org/license


import gi
gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, Pango

class LogDialog(Gtk.Dialog):
    def __init__(self, prnt, log_file, headerbar):
        self._log_file = log_file
        Gtk.Dialog.__init__(self, parent=prnt, use_header_bar=headerbar)
        self.set_size_request(550, 450)
        self.set_border_width(6)
        self.set_title(_('Errors detail'))
        scroll = Gtk.ScrolledWindow()
        scroll.set_shadow_type(Gtk.ShadowType.IN)
        text_log = Gtk.TextView()
        text_log.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        text_log.set_border_width(6)
        text_log.set_editable(False)
        text_log.set_cursor_visible(False)
        
        font_desc = Pango.FontDescription('Monospace')
        text_log.override_font(font_desc)
        
        text_buffer = Gtk.TextBuffer()
        text_log.set_buffer(text_buffer)
        
        scroll.add(text_log)
        self.vbox.set_spacing(4)
        self.vbox.pack_start(scroll, True, True, 0)
        
        button = self.add_button(_('_Close'), Gtk.ResponseType.CLOSE)
        self.set_default(button)
        
        with open(log_file, 'r') as log:
            text_buffer.set_text(log.read())
        
        
    def show_dialog(self):
        self.show_all()
        self.run()
        self.destroy()
        
        
        
        
        