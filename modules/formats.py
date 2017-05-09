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

from gi.repository import Gtk
from modules.edition import FormatEditor
from modules.customwidgets import ButtonWithIcon

class Formats(Gtk.Popover):
    
    def on_select_format(self, *args):
        selected_iter = self.tree_sel.get_selected()[1]
        if selected_iter == None:
            self.lbl.set_markup(self.no_format)
            return
        self.selected_format = self.tree_filter[selected_iter][0]
        self.wind.btn_formats.set_label(self.selected_format)
        self.hide()
        self.wind.fill_options()
    
    
    def on_edit_format(self, widget):
        selected_iter = self.tree_sel.get_selected()[1]
        if selected_iter == None:
            self.lbl.set_markup(self.no_format)
            return
        self.selected_format = self.tree_filter[selected_iter][0]
        self.hide()
        dlg = FormatEditor(self.wind, self.selected_format, self.store)
        dlg.show_dialog()
    
    
    def on_closed(self, *args):
        self.lbl.set_markup('')
    
    
    def __init__(self, wind, formats_list, curr_format, store):
        self.wind = wind
        self.formats_list = formats_list
        self.selected_format = curr_format
        
        self.no_format = _('<i><span color="red">No format selected!</span></i>')
        
        Gtk.Popover.__init__(self)
        self.set_border_width(4)
        self.connect('closed', self.on_closed)
        
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.add(vbox)
        
        #
        self.e_search = Gtk.SearchEntry()
        self.e_search.set_activates_default(True)
        self.e_search.connect('changed', self.on_entry_search)
        self.e_search.set_direction(Gtk.TextDirection.LTR)
        vbox.pack_start(self.e_search, False, True, 2)
        
        
        #
        self.store = store # Gtk.ListStore(str)
        self.tree_filter = self.store.filter_new()
        self.tree_filter.set_visible_func(self.match_func)
        
        self.tree_formats = Gtk.TreeView(self.tree_filter)
        self.tree_formats.set_headers_visible(False)
        self.tree_formats.set_direction(Gtk.TextDirection.LTR)
        self.tree_formats.set_grid_lines(Gtk.TreeViewGridLines.HORIZONTAL)
        self.tree_formats.connect('row-activated', self.on_choosed_format)
        
        self.tree_sel = self.tree_formats.get_selection()
        
        # cell
        cell = Gtk.CellRendererText()
        col = Gtk.TreeViewColumn(None, cell, text=0)
        self.tree_formats.append_column(col)
        
        scroll = Gtk.ScrolledWindow()
        scroll.set_size_request(450, 220)
        scroll.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        scroll.add(self.tree_formats)
        vbox.pack_start(scroll, True, True, 0)
        
        # Load formats
        for fmt in self.formats_list:
            self.store.append([fmt])
        
        self.store.set_sort_column_id(0, Gtk.SortType.ASCENDING)
        
        # hbox btns
        hbox_btns = Gtk.Box()
        vbox.pack_start(hbox_btns, True, True, 0)
        
        # edit btn
        btn_edit = ButtonWithIcon('preferences-other-symbolic')
        btn_edit.set_tooltip_text(_('Edit'))
        btn_edit.connect('clicked', self.on_edit_format)
        hbox_btns.pack_start(btn_edit, False, True, 0)
        
        self.lbl = Gtk.Label()
        hbox_btns.pack_start(self.lbl, True, False, 0)        
        
        # select btn
        btn_select = Gtk.Button(_('Choose'))
        btn_select.set_size_request(80, 1)
        btn_select.set_tooltip_text(_('Choose'))
        btn_select.connect('clicked', self.on_select_format)
        hbox_btns.pack_end(btn_select, False, True, 0)
 
        # finally
        vbox.show_all()
        
    def on_entry_search(self, w):
        self.tree_filter.refilter()
    
    def match_func(self, model, tree_iter, data=None):
        txt = self.e_search.get_text()
        value = model.get_value(tree_iter, 0)
        
        if (txt == "") or (txt.lower() in value.lower()):
            return True
        self.tree_formats.set_cursor(0)
        return False
    
    def on_choosed_format(self, tree, path, col):
        model = tree.get_model()
        self.selected_format = model[path][0]
        self.wind.btn_formats.set_label(self.selected_format)
        self.hide()
        self.wind.fill_options()


