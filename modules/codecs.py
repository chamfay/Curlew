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
from modules.functions import get_available_codecs

class CodecsDialog(Gtk.Dialog):
    def __init__(self, prnt, encoder, title):
        Gtk.Dialog.__init__(self, parent=prnt, use_header_bar=True)
        self.set_title(title)
        self.set_size_request(700, 600)
        self.set_border_width(6)
        self.vbox.set_spacing(6)
        
        txt_info = Gtk.TextView()
        txt_info.set_editable(False)
        txt_info.set_cursor_visible(False)
        txt_info.set_border_width(8)
        
        scroll = Gtk.ScrolledWindow()
        scroll.set_shadow_type(Gtk.ShadowType.IN)
        scroll.add(txt_info)
        self.vbox.pack_start(scroll, True, True, 0)
        
        font_desc = Pango.FontDescription('Monospace')
        txt_info.override_font(font_desc)
        
        txt_buffer = Gtk.TextBuffer()
        txt_info.set_buffer(txt_buffer)
        
        # Show Codecs        
        buff = get_available_codecs(encoder)
        txt_buffer.set_text(buff)
        
    
    
    def show_dialog(self):
        self.show_all()
        self.run()
        self.destroy()
