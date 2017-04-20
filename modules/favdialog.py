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

import gi
gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, Gdk
import pickle

class Favorite(Gtk.Dialog):
    def __init__(self, prnt, fav_list, headerbar):
        Gtk.Dialog.__init__(self, parent=prnt, use_header_bar=headerbar)
        self.set_title(_('Favorite list'))
        self.set_icon_name('curlew')
        self.set_border_width(4)
        self.set_size_request(450, 400)
        self.store = Gtk.ListStore(str)
        self.list_view = Gtk.TreeView(self.store)
        self.list_view.connect("key-press-event", self.on_key_press)
        
        if headerbar:
            header = self.get_header_bar()
        else:
            header = Gtk.HeaderBar()
            self.vbox.add(header)
        
        cell = Gtk.CellRendererText()
        col = Gtk.TreeViewColumn(_("Format"), cell, text=0)
        self.list_view.append_column(col)
        
        g_vbox = Gtk.Box(spacing=6, orientation=Gtk.Orientation.VERTICAL)
        
        scroll = Gtk.ScrolledWindow()
        scroll.set_shadow_type(Gtk.ShadowType.IN)
        scroll.add(self.list_view)
        
        g_vbox.pack_start(scroll, True, True, 0)
        
        box_up_down = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        Gtk.StyleContext.add_class(box_up_down.get_style_context(), "linked")        
        header.pack_end(box_up_down)
        
        btn_up = Gtk.Button()
        btn_up.set_tooltip_text(_('Up'))
        btn_up.set_image(Gtk.Image.new_from_icon_name('go-up-symbolic', Gtk.IconSize.MENU))
        btn_up.connect('clicked', self.go_up)
        box_up_down.pack_start(btn_up, False, False, 0)
        
        btn_down = Gtk.Button()
        btn_down.set_tooltip_text(_('Down'))
        btn_down.set_image(Gtk.Image.new_from_icon_name('go-down-symbolic', Gtk.IconSize.MENU))
        btn_down.connect('clicked', self.go_down)
        box_up_down.pack_start(btn_down, False, False, 0)
        
        btn_delete = Gtk.Button()
        btn_delete.set_tooltip_text(_('Remove'))
        btn_delete.set_image(Gtk.Image.new_from_icon_name('list-remove-symbolic', Gtk.IconSize.MENU))
        btn_delete.connect('clicked', self.delete_item)
        
        header.pack_end(btn_delete)
        
        self.vbox.pack_start(g_vbox, True, True, 0)
        
        # load
        for fformat in fav_list:
            self.store.append((fformat,))
        
        self.show_all()
    
    # Delete Item
    def delete_item(self, *args):
        sele = self.get_selected_iter()
        if sele:
            self.store.remove(sele)
    
    def go_up(self, widget):
        sel_iter = self.get_selected_iter()
        if sel_iter:
            self.store.move_before(sel_iter, self.store.iter_previous(sel_iter))
    
    def go_down(self, widget):
        sel_iter = self.get_selected_iter()
        if sel_iter:
            self.store.move_after(sel_iter, self.store.iter_next(sel_iter))
    
    def get_selected_iter(self):
        return self.list_view.get_selection().get_selected()[1]
    
    def save(self, file_name):
        fav_list = []
        for row in self.store:
            fav_list.append(row[0])
        favfile = open(file_name, "wb")
        pickle.dump(fav_list, favfile)
        favfile.close()
    
    def on_key_press(self, widget, event):
        if event.keyval == Gdk.KEY_Delete:
            self.delete_item()
    
