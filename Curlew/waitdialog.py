# -*- coding: utf-8 -*-

# Curlew - Easy to use multimedia converter
#
# Copyright (C) 2012-2014 Fayssal Chamekh <chamfay@gmail.com>
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

from gi.repository import Gtk

class WaitDialog(Gtk.Dialog):
    def __init__(self, parent):
        
        self.skip = False
        
        Gtk.Dialog.__init__(self, parent=parent)
        self.set_size_request(650, 50)
        self.set_border_width(8)
        self.set_resizable(False)
        self.set_title(_('Adding files...'))
        
        self.text_file = Gtk.Label()
        self.text_file.set_alignment(0, 0.5)
        self.text_file.set_max_width_chars(50)
        self.vbox.pack_start(self.text_file, False, False, 6)
        
        self.prog_bar = Gtk.ProgressBar()
        self.prog_bar.set_show_text(True)
        self.vbox.pack_start(self.prog_bar, False, False, 6)
        
        btn_skip = self.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
        btn_skip.connect('clicked', self.__skip)
        
        self.show_all()
        self.connect('delete-event', self.__skip)
    
    
    def set_filename(self, filename):
        self.text_file.set_markup(_('<b>File:</b> ')+filename)
    
    def set_progress(self, value):
        self.prog_bar.set_fraction(value)
        self.prog_bar.set_text('{:.0f}%'.format(value*100))
    
    def __skip(self, *args):
        self.skip = True



