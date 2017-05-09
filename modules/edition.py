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

from configparser import ConfigParser, NoSectionError

import gi
gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, GLib

from modules.customwidgets import LabeledGrid, ButtonWithIcon
from modules.consts import CONF_FILE, ORG_FFILE
from modules.functions import show_message


class FormatEditor(Gtk.Dialog):

    # Save settings
    def on_btn_save(self, *args):
        # Confirm
        if show_message(self,
                        _('Are you sure you want to save settings?'),
                        Gtk.MessageType.QUESTION,
                        Gtk.ButtonsType.YES_NO) == Gtk.ResponseType.NO:
            return
        
        conf = ConfigParser()
        conf.read(self.ffile)
        
        section = self.entry_frmt.get_text()
        
        if not conf.has_section(section):
            conf.add_section(section)
            conf[section]['type'] = conf[self.format]['type']
            try:
                conf[section]['ff'] = conf[self.format]['ff']
            except: pass
            conf[section]['ext'] = conf[self.format]['ext']
            conf[section]['flag'] = 'custom'
        
        # audio
        if self.entry_ab.get_sensitive():
            ab = self.entry_ab.get_text()
            conf[section]['ab'] = ab
            lab = ab.split()
            conf[section]['def_ab'] = lab[self.spin_def_ab.get_value_as_int()-1]
        if self.entry_afreq.get_sensitive():
            conf[section]['afreq'] = self.entry_afreq.get_text()
        if self.entry_ach.get_sensitive():
            conf[section]['ach'] = self.entry_ach.get_text()
        if self.entry_acodec.get_sensitive():
            conf[section]['acodec'] = self.entry_acodec.get_text()
        
        # video
        if self.entry_vb.get_sensitive():
            vb = self.entry_vb.get_text()
            conf[section]['vb'] = vb
            lvb = vb.split()
            conf[section]['def_vb'] = lvb[self.spin_def_vb.get_value_as_int()-1]
        if self.entry_vfps.get_sensitive():
            conf[section]['vfps'] =  self.entry_vfps.get_text()
        if self.entry_vsize.get_sensitive():
            conf[section]['vsize'] =  self.entry_vsize.get_text()
        if self.entry_vcodec.get_sensitive():
            conf[section]['vcodec'] =  self.entry_vcodec.get_text()
        if self.entry_vratio.get_sensitive():
            conf[section]['vratio'] =  self.entry_vratio.get_text()
        
        if self.entry_extra.get_sensitive():
            conf[section]['extra'] =  self.entry_extra.get_text()
        
        with open(self.ffile, 'w') as configfile:
            conf.write(configfile)
        
        if section != self.format:
            self.store.append([section])
        
        # close dialog        
        self.close()
    
    def on_btn_def(self, *args):
        
        section = self.format
        
        conf_src = ConfigParser()
        conf_src.read(ORG_FFILE)
        conf_dest = ConfigParser()
        conf_dest.read(self.ffile)
        
        try:
            opts = conf_src.options(section)
        except NoSectionError:
            show_message(self,
                         _('You can\'t restore a custom format to defaults.'),
                         Gtk.MessageType.WARNING)
            return
        
        for opt in opts:
            conf_dest[section][opt] = conf_src[section][opt]
        
        with open(self.ffile, 'w') as configfile:
            conf_dest.write(configfile)
        
        self.load_settings()
    
    
    def get_formats_file(self):
        conf = GLib.KeyFile()        
        conf.load_from_file(CONF_FILE, GLib.KeyFileFlags.NONE)
        frmts_file = conf.get_string('configs', 'formats_file')
        conf.unref()
        return frmts_file
    

    def set_sensitivity(self, media_type):
        sens = {
                 'audio':   [True, True, True, True, False, False, False, False, False],
                 'video':   [True, True, True, True, True, True, True, True, True],
                 'presets': [False, False, False, False, False, False, False, False, False],
                 'copy': [False, False, False, False, False, False, False, False, False]
                }
         
        self.entry_ab.set_sensitive(sens[media_type][0])
        self.spin_def_ab.set_sensitive(sens[media_type][0])
        self.entry_afreq.set_sensitive(sens[media_type][1])
        self.entry_ach.set_sensitive(sens[media_type][2])
        self.entry_acodec.set_sensitive(sens[media_type][3])
        
        self.entry_vb.set_sensitive(sens[media_type][4])
        self.spin_def_vb.set_sensitive(sens[media_type][4])
        self.entry_vfps.set_sensitive(sens[media_type][5])
        self.entry_vsize.set_sensitive(sens[media_type][6])
        self.entry_vcodec.set_sensitive(sens[media_type][7])
        self.entry_vratio.set_sensitive(sens[media_type][8])
    
    
    def load_settings(self):
        conf = ConfigParser()
        conf.read(self.ffile)
        section = self.format
        
        self.btn_remove.set_sensitive(conf.has_option(section, 'flag'))
        
        self.set_sensitivity(conf[section]['type'])
        self.entry_frmt.set_text(section)
        
        # audio
        if conf.has_option(section, 'ab'):
            abitrate = conf[section]['ab']
            self.entry_ab.set_text(abitrate)
            abitrates = abitrate.split()
            if conf.has_option(section, 'def_ab'):
                self.spin_def_ab.set_value(abitrates.index(conf[section]['def_ab'])+1)
        if conf.has_option(section, 'afreq'):
            self.entry_afreq.set_text(conf[section]['afreq'])
        if conf.has_option(section, 'ach'):
            self.entry_ach.set_text(conf[section]['ach'])
        if conf.has_option(section, 'acodec'):
            self.entry_acodec.set_text(conf[section]['acodec'])
        
        # video
        if conf.has_option(section, 'vb'):
            vbitrate = conf[section]['vb']
            self.entry_vb.set_text(vbitrate)
            vbitrates = vbitrate.split()
            if conf.has_option(section, 'def_vb'):
                self.spin_def_vb.set_value(vbitrates.index(conf[section]['def_vb'])+1)
        if conf.has_option(section, 'vfps'):
            self.entry_vfps.set_text(conf[section]['vfps'])
        if conf.has_option(section, 'vsize'):
            self.entry_vsize.set_text(conf[section]['vsize'])
        if conf.has_option(section, 'vcodec'):
            self.entry_vcodec.set_text(conf[section]['vcodec'])
        if conf.has_option(section, 'vratio'):
            self.entry_vratio.set_text(conf[section]['vratio'])
        
        if conf.has_option(section, 'extra'):
            self.entry_extra.set_text(conf[section]['extra'])
    

    def on_bitrate_changed(self, w, spin):
        list_len = len(w.get_text().split())
        spin.set_range(1, list_len)    
    

    def remove_format(self, *args):
        # Confirm
        if show_message(self,
                        _('Are you sure you want to remove this format?'),
                        Gtk.MessageType.QUESTION,
                        Gtk.ButtonsType.YES_NO) == Gtk.ResponseType.NO:
            return
        
        conf = ConfigParser()
        conf.read(self.ffile)
        conf.remove_section(self.format)
        with open(self.ffile, 'w') as configfile:
            conf.write(configfile)
        
        # remove iter
        prev_iter = None
        next_iter = None
        for row in self.store:
            if row[0] == self.format:
                prev_iter = self.store.iter_previous(row.iter)
                next_iter = self.store.iter_next(row.iter)
                self.store.remove(row.iter)
                break
        #
        if prev_iter == None:
            self.main_win.btn_formats.set_label(self.store[next_iter][0])
        else:
            self.main_win.btn_formats.set_label(self.store[prev_iter][0])
        
        # Update fav menu
        self.main_win.remove_from_fav(self.format)
        
        # close dialog
        self.close()
    
    
    def __init__(self, prnt, frmt, store):
        Gtk.Dialog.__init__(self,
                            parent=prnt,
                            use_header_bar=True)
        self.set_size_request(700, 450)
        self.set_border_width(4)
        self.set_title(_('Edition'))
        
        self.format = frmt
        self.store = store
        self.titlebar = self.get_titlebar()
        self.main_win = prnt
        
        self.vbox.set_spacing(6)
        grid = LabeledGrid(self.vbox)
        
        # Warning
        lbl_warn = Gtk.Label(_('<span foreground="red"><i><b>WARNING:</b> Please change these values with care!</i></span>'), use_markup=True)
        self.vbox.pack_end(lbl_warn, False, False, 0)
        self.vbox.pack_end(Gtk.Separator(), False, False, 0)
        
        grid.append_title(_('Audio:'))
        
        self.entry_ab = Gtk.Entry()
        self.spin_def_ab = Gtk.SpinButton.new_with_range(1, 4, 1)
        self.entry_ab.connect('changed', self.on_bitrate_changed, self.spin_def_ab)
        
        box_ab = Gtk.Box(spacing=6)
        box_ab.pack_start(self.entry_ab, True, True, 0)
        box_ab.pack_start(Gtk.Label(_('Default')), False, False, 0)
        box_ab.pack_start(self.spin_def_ab, False, False, 0)
        
        grid.append_row(_('Audio Bitrates'), box_ab, True)
        self.entry_afreq = Gtk.Entry()
        grid.append_row(_('Audio Frequencies'), self.entry_afreq, True)
        self.entry_ach = Gtk.Entry()
        grid.append_row(_('Audio Channels'), self.entry_ach, True)
        self.entry_acodec = Gtk.Entry()
        grid.append_row(_('Audio Codecs'), self.entry_acodec, True)
        
        # video
        grid.append_title(_('Video:'))
        self.entry_vb = Gtk.Entry()
        self.spin_def_vb = Gtk.SpinButton().new_with_range(1, 4, 1)
        self.entry_vb.connect('changed', self.on_bitrate_changed, self.spin_def_vb)
        
        box_vb = Gtk.Box(spacing=6)
        box_vb.pack_start(self.entry_vb, True, True, 0)
        box_vb.pack_start(Gtk.Label(_('Default')), False, False, 0)
        box_vb.pack_start(self.spin_def_vb, False, False, 0)

        grid.append_row(_('Video Bitrates'), box_vb, True)
        self.entry_vfps = Gtk.Entry()
        grid.append_row(_('Video FPS'), self.entry_vfps, True)
        self.entry_vsize = Gtk.Entry()
        grid.append_row(_('Video Sizes'), self.entry_vsize, True)
        self.entry_vcodec = Gtk.Entry()
        grid.append_row(_('Video Codecs'), self.entry_vcodec, True)
        self.entry_vratio = Gtk.Entry()
        grid.append_row(_('Aspect Ratios'), self.entry_vratio, True)

        grid.append_title(_('Other Options:'))
        self.entry_extra = Gtk.Entry()
        grid.append_row(_('Extra Options'), self.entry_extra, True)
        
        box_title = Gtk.Box()
        Gtk.StyleContext.add_class(box_title.get_style_context(), "linked")
        
        # Format Entry
        self.entry_frmt = Gtk.Entry()
        self.entry_frmt.set_alignment(0.5)
        self.entry_frmt.set_size_request(320, 1)
        box_title.pack_start(self.entry_frmt, True, True, 0)

        # Save Button
        btn_save = ButtonWithIcon('document-save-symbolic')
        btn_save.set_tooltip_text(_('Save'))
        btn_save.connect('clicked', self.on_btn_save)
        box_title.pack_start(btn_save, True, True, 0)
        
        # Remove button
        self.btn_remove = ButtonWithIcon('edit-delete-symbolic')
        self.btn_remove.set_tooltip_text(_('Remove'))
        self.btn_remove.connect('clicked', self.remove_format)
        box_title.pack_start(self.btn_remove, False, False, 0)
        
        self.titlebar.set_custom_title(box_title)
        
        # Set to default button
        btn_def = ButtonWithIcon('view-refresh-symbolic')
        btn_def.set_tooltip_text(_('Restore default'))
        btn_def.connect('clicked', self.on_btn_def)
        self.titlebar.pack_end(btn_def)
        
        self.set_focus(btn_save)
        
        # work
        self.ffile = self.get_formats_file()
        self.load_settings()
        
    
    
    def show_dialog(self):
        self.show_all()
        self.run()
        self.destroy()
