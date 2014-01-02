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

class StatusIcon(Gtk.StatusIcon):
    def __init__(self, window):
        Gtk.StatusIcon.__init__(self)
        
        self._window = window
        
        self.set_from_icon_name('curlew')
        self.set_tooltip_text(_('Curlew'))
    
        #---- Build menu
        self.menu = Gtk.Menu()
        
        # Show main window
        self.show_item = Gtk.MenuItem(_('Hide'))
        self.show_item.connect("activate", self.show_hide)
        
        # Stop conversion
        stop_item = Gtk.MenuItem(_('Stop Conversion'))
        stop_item.connect("activate", self.stop)
        
        # Quit application
        quit_item = Gtk.MenuItem(_('Quit application'))
        quit_item.connect("activate", self.quit)
        
        # Append menu items and show all
        self.menu.append(self.show_item)
        self.menu.append(stop_item)
        self.menu.append(quit_item)

        # Make connection
        self.connect('popup-menu', self.on_popup_menu, stop_item)
        self.connect('activate', self.show_hide)

        self.set_visible(False)
    
    
    def on_popup_menu(self, icon, button, time, stop_item):
        
        # stop_item sensitivity
        stop_item.set_sensitive(self._window.is_converting)
        
        # show/hide
        if self._window.get_visible():
            self.show_item.set_label(_('Hide'))
        else:
            self.show_item.set_label(_('Show'))
        
        self.menu.show_all()
        self.menu.popup(None, None, Gtk.StatusIcon.position_menu, 
                        icon, button, time)
    
    
    def show_hide(self, *agrs):
        if self._window.get_visible():
            self._window.hide()
        else:
            self._window.present()
        
    def stop(self, stop_item):
        if self._window.tb_stop_cb():
            self._window.present()
        
    def quit(self, *args):
        self._window.quit_cb()



