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


class SpinsFrame(Gtk.Frame):
    '''4 SpinButton collection'''
    def __init__(self, title):
        Gtk.Frame.__init__(self)
        
        self._top = 0
        self._bottom = 0
        self._left = 0
        self._right = 0
        self._sum = 0
        
        hbox = Gtk.Box(sensitive=False, spacing=4, border_width=4)
        self.add(hbox)
        
        self.check_btn = Gtk.CheckButton(title)
        self.set_label_widget(self.check_btn)
        
        # Adjustments
        adj_top    = Gtk.Adjustment(0, 0, 10000, 1)
        adj_bottom = Gtk.Adjustment(0, 0, 10000, 1)
        adj_left   = Gtk.Adjustment(0, 0, 10000, 1)
        adj_right  = Gtk.Adjustment(0, 0, 10000, 1)
        
        # Top spin
        self.spin_top = Gtk.SpinButton(adjustment=adj_top)
        self.spin_top.set_numeric(True)
        hbox.pack_start(Gtk.Label(_('Top')), False, False, 0)
        hbox.pack_start(self.spin_top, False, False, 0)
        
        hbox.pack_start(Gtk.VSeparator(), False, False, 8)
        
        # bottom spin
        self.spin_bottom = Gtk.SpinButton(adjustment=adj_bottom)
        self.spin_bottom.set_numeric(True)
        hbox.pack_start(Gtk.Label(_('Bottom')), False, False, 0)
        hbox.pack_start(self.spin_bottom, False, False, 0)
        
        hbox.pack_start(Gtk.VSeparator(), False, False, 8)
        
        # Left Spin
        self.spin_left = Gtk.SpinButton(adjustment=adj_left)
        self.spin_left.set_numeric(True)
        hbox.pack_start(Gtk.Label(_('Left')), False, False, 0)
        hbox.pack_start(self.spin_left, False, False, 0)
        
        hbox.pack_start(Gtk.VSeparator(), False, False, 8)
        
        # Right spin
        self.spin_right = Gtk.SpinButton(adjustment=adj_right)
        self.spin_right.set_numeric(True)
        hbox.pack_start(Gtk.Label(_('Right')), False, False, 0)
        hbox.pack_start(self.spin_right, False, False, 0)
        
        
        # Connection
        self.spin_top.connect('value-changed', self._on_spins_changed)
        self.spin_bottom.connect('value-changed', self._on_spins_changed)
        self.spin_left.connect('value-changed', self._on_spins_changed)
        self.spin_right.connect('value-changed', self._on_spins_changed)
        self.check_btn.connect('toggled', self._on_check_cb, hbox)
    
    def _on_check_cb(self, check_btn, hbox):
        hbox.set_sensitive(check_btn.get_active())
    
    def _on_spins_changed(self, spin):
        self._top = self.spin_top.get_value_as_int()
        self._bottom = self.spin_bottom.get_value_as_int()
        self._left = self.spin_left.get_value_as_int()
        self._right = self.spin_right.get_value_as_int()
        
        self._sum = self._top + self._bottom + self._left + self._right
    
    def get_active(self):
        return self.check_btn.get_active() and self._sum != 0
    
    def get_crop(self):
        return 'crop=iw-{}:ih-{}:{}:{}'.format(self._left+self._right,
                                               self._top+self._bottom,
                                               self._left, self._top)
    
    def get_pad(self):
        return 'pad=iw+{}:ih+{}:{}:{}'.format(self._left+self._right,
                                               self._top+self._bottom,
                                               self._left, self._top)
    
    
class HScale(Gtk.HScale):
    def __init__(self, container, def_value, min_value, max_value, step=1):
        Gtk.HScale.__init__(self)
        container.pack_start(self, True, True, 0)
        adj = Gtk.Adjustment.new(def_value, min_value, max_value, step, step, 0)
        self.set_adjustment(adj)
        self.set_value_pos(Gtk.PositionType.RIGHT)
        self.set_digits(0)
        

class LabeledHBox(Gtk.Box):
    ''' hbox with label'''
    def __init__(self, label, container=None):
        Gtk.Box.__init__(self, spacing=4)
        _label = Gtk.Label(label, use_markup=True)
        _label.set_alignment(0, 0.5)
        self.pack_start(_label, False, False, 0)
        if container != None:
            container.pack_start(self, False, False, 0)


class LabeledGrid(Gtk.Grid):
    def __init__(self, container=None):
        Gtk.Grid.__init__(self)
        self.set_column_spacing(2)
        self.set_row_spacing(4)
        self.set_row_homogeneous(False)
        self._n_childs = 0
        if container:
            container.pack_start(self, False, False, 0)
        
    def append_row(self, label, widget, expanded=False):
        _label = Gtk.Label(label, use_markup=True)
        _label.set_alignment(0.0, 0.5)
        _hbox = Gtk.Box()
        _hbox.set_hexpand(True)
        _hbox.pack_start(widget, expanded, expanded, 0)
        self.attach(_label, 0, self._n_childs, 1, 1)
        self.attach(_hbox, 1, self._n_childs, 1, 1)
        self._n_childs += 1

    def append_title(self, label):
        _label = Gtk.Label('<b>{}</b>'.format(label), use_markup=True)
        _label.set_alignment(0, 0.5)
        self.attach(_label, 0, self._n_childs, 1, 1)
        self._n_childs += 1


class TimeLayout(Gtk.Box):
    def __init__(self, container, label):
        '''    Time widget    '''
        Gtk.Box.__init__(self)
        self._spin_h = Gtk.SpinButton().new_with_range(0, 5, 1)
        self._spin_m = Gtk.SpinButton().new_with_range(0, 59, 1)
        self._spin_s = Gtk.SpinButton().new_with_range(0, 59, 1)
        
        _label = Gtk.Label(label, use_markup=True)
        _label.set_alignment(0, 0.5)
        _label.set_width_chars(10)
        
        self.pack_start(_label, False, False, 0)
        
        self.pack_start(self._spin_h, False, False, 3)
        self.pack_start(Gtk.Label(label=_('hr')), False, False, 0)
        
        self.pack_start(Gtk.Label(6*' '), False, False, 0)
        
        self.pack_start(self._spin_m, False, False, 3)
        self.pack_start(Gtk.Label(label=_('min')), False, False, 0)
        
        self.pack_start(Gtk.Label(6*' '), False, False, 0)
        
        self.pack_start(self._spin_s, False, False, 3)
        self.pack_start(Gtk.Label(label=_('sec')), False, False, 0)
        
        container.pack_start(self, False, False, 0)
    
    def set_duration(self, duration):
        ''' Set duration in seconds '''
        self._spin_h.set_value(duration/3600)
        self._spin_m.set_value((duration%3600)/60)
        self._spin_s.set_value((duration%3600)%60)
    
    def get_duration(self):
        ''' Return duration in sec '''
        return self._spin_h.get_value()*3600 \
                       + self._spin_m.get_value()*60 \
                       + self._spin_s.get_value()
    
    def get_time_str(self):
        '''
        Return time str like 00:00:00
        '''
        return '{:02.0f}:{:02.0f}:{:02.0f}'.format(self._spin_h.get_value(), 
                                                   self._spin_m.get_value(), 
                                                   self._spin_s.get_value())


class ComboWithEntry(Gtk.ComboBoxText):
    '''
     Custom ComboBoxText with entry
    '''
    def __init__(self, with_entry=True):
        Gtk.ComboBoxText.__init__(self, has_entry=with_entry)
        self.connect('changed', self._on_combo_changed)
        self.set_entry_text_column(0)
    
    def set_list(self, list_of_elements):
        ''' Fill combobox with list directly [] '''
        self.remove_all()
        for i in list_of_elements: self.append_text(i)
        self.set_active(0)
    
    def get_text(self):
        return self.get_active_text()
    
    def set_text(self, text):
        ''' Set text to Entry '''
        entry = self.get_child()
        entry.set_text(text)
    
    def _on_combo_changed(self, *args):
        enabled = self.get_text() == 'default' and len(self.get_model()) < 2
        self.set_sensitive(not enabled)
    
    def is_not_default(self):
        return self.get_active_text() != 'default'
    
    def find_text(self, text_to_find):
        model = self.get_model()
        for row in model:
            if row[0] == text_to_find:
                return True
        return False

class ButtonWithIcon(Gtk.Button):
    def __init__(self, icon_name=None, icon_size=Gtk.IconSize.BUTTON):
        Gtk.Button.__init__(self)
        self.set_size_request(36, 36)
        if icon_name:
            img = Gtk.Image.new_from_icon_name(icon_name, icon_size)
            self.set_image(img)

class ToggleBtnWithIcon(Gtk.ToggleButton):
    def __init__(self, icon_name=None, icon_size=Gtk.IconSize.BUTTON):
        Gtk.Button.__init__(self)
        self.set_size_request(36, 36)
        if icon_name:
            img = Gtk.Image.new_from_icon_name(icon_name, icon_size)
            self.set_image(img)



