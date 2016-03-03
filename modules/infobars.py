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

class InfoBar(Gtk.InfoBar):
    def __init__(self):
        Gtk.InfoBar.__init__(self)
        self.set_show_close_button(True)
        self.set_no_show_all(True)
        self.connect('response', self.on_response)
        
        self.lbl_bar = Gtk.Label()
        self.lbl_bar.set_use_markup(True)
        self.lbl_bar.show()
        self.get_content_area().add(self.lbl_bar)
    
    def show_message(self, msg, message_type=Gtk.MessageType.INFO):
        self.lbl_bar.set_label('<b>{}</b>'.format(msg))
        self.set_message_type(message_type)
        self.show()
    
    def on_response(self, info_bar, response_id):
        info_bar.hide()



