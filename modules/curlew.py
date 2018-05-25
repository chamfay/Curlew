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


from configparser import ConfigParser
import gettext
import mimetypes
import os
from os.path import basename, isdir, splitext, join, dirname, realpath, \
isfile, exists, getsize, abspath
import pickle
import re
from subprocess import Popen, PIPE, call, check_output
import sys
import time
from shutil import copyfile, which
from urllib.parse import unquote

try:
    import gi
    gi.require_version('Gtk', '3.0')
    
    from gi.repository import Gtk, GLib, Gdk, GObject, GdkPixbuf, Gio, Pango
    import dbus.glib, dbus.service
    
    from modules.customwidgets import LabeledHBox, TimeLayout, HScale, \
    SpinsFrame, LabeledGrid, ComboWithEntry, ButtonWithIcon, ToggleBtnWithIcon
    from modules.about import About
    from modules.functions import show_message, get_format_size, \
    duration_to_time, time_to_duration, check_codec
    from modules.logdialog import LogDialog
    from modules.errdialog import ErrDialog
    from modules.tray import StatusIcon
    from modules.languages import LANGUAGES
    from modules.favdialog import FavoriteDialog
    from modules.waitdialog import WaitDialog
    from modules.formats import Formats
    from modules.infobars import InfoBar
    from modules.codecsdialog import CodecsDialog
    from modules.consts import CONF_PATH, HOME, CONF_FILE, DTA_DIR, \
    ORG_FFILE, USR_FFILE, SOUND_FILE
    from modules.configs import get_b_config, get_s_config
    from modules.players import choose_player
except Exception as e:
    print(e)
    sys.exit(1)

# Files
ERR_LOG_FILE = join(CONF_PATH, 'errors.log')
FAV_FILE = join(CONF_PATH, 'fav.list')
PASS_LOG = '/tmp/pass1log'
PASS_1_FILE = '/tmp/pass1file'
PREVIEW_FILE = '/tmp/Preview'
IMG_PREV = '/tmp/img_prev.jpeg'
INTERNAL_ENCODER = abspath(join(DTA_DIR, 'ffmpeg'))

TEN_SECONDS = '10'

# Localization.
DOMAIN = 'curlew'
LOCALDIR = join(DTA_DIR, 'locale')
gettext.install(DOMAIN, LOCALDIR)

# Treeview cols nbrs
C_SKIP = 0  # Skip (checkbox)
C_NAME = 1  # File name
C_FSIZE = 2  # File size
C_FDURA = 3  # File duration
C_ESIZE = 4  # Estimated output size
C_ELAPT = 5  # Elapsed time
C_REMN = 6  # Remaining time
C_PRGR = 7  # Progress value
C_STAT = 8  # Stat string
C_PULS = 9  # Pulse
C_FILE = 10  # complete file name 'complete_path/file.ext'

# Stack children
CHILD_WELCOME = 'welcome'
CHILD_FILES = 'files'
CHILD_ADVANCED = 'advanced'
CHILD_INFOS = 'infos'
CHILD_ERRORS = 'errors'
CHILD_MERGE = 'merge'

# Task type
TASK_CONVERT = 0
TASK_MERGE   = 1
TASK_GIF     = 2

# Error code
CODE_SUCCESS = 0
CODE_STOPPED = 9
CODE_FAILED = 256

#--- Main class        
class Curlew(Gtk.ApplicationWindow):
    
    def on_codec_changed(self, *w):
        msg = _('<span color="red"><i><b>{}</b> Codec not found!</i></span>')
        acodec = self.c_acodec.get_active_text()
        if check_codec(self.encoder, acodec):
            self.l_acodec.set_text('')
        else:
            self.l_acodec.set_markup(msg.format(acodec))

        vcodec = self.c_vcodec.get_active_text()
        if check_codec(self.encoder, vcodec):
            self.l_vcodec.set_text('')
        else:
            self.l_vcodec.set_markup(msg.format(vcodec))
     
    def on_link_clicked(self, w):
        dlg = CodecsDialog(self, self.encoder, self.link_label)
        dlg.show_dialog()
        return True
    
    def play_sound(self, sfile):
        try:
            gi.require_version('Gst', '1.0')
            from gi.repository import Gst
            Gst.init()
            pl = Gst.ElementFactory.make("playbin", "player")
            pl.set_property('uri', 'file://' + sfile)
            pl.set_state(Gst.State.PLAYING)
        except Exception as e:
            print(e)
    
    
    def on_select_fav(self, action, param, item):
        sele_fmt = item.get_attribute_value(Gio.MENU_ATTRIBUTE_LABEL).get_string()
        self.btn_formats.set_label(sele_fmt)
        self.fill_options()
    
    
    def load_submenu(self):
        self.submenu.remove_all()
        i = 0
        for fformat in self.get_fav_list():
            item = Gio.MenuItem.new(fformat, 'Fav.Select{}'.format(i))
            self.submenu.append_item(item)
            action_select = Gio.SimpleAction.new('Select{}'.format(i))
            action_select.connect('activate', self.on_select_fav, item)
            self.action_group.insert(action_select)
            i += 1
    
    
    def on_add_fav(self, widget):
        fav_list = self.get_fav_list()
        fav_format = self.btn_formats.get_label()        
        
        # limit fav list to 10 elmnts
        if len(fav_list) > 9:
            self.info_bar.show_message(
                _('You can\'t add more than 10 elements.'),
                Gtk.MessageType.INFO)
            return
        
        # format already exist
        if fav_format in fav_list:
            self.info_bar.show_message(
                _('"{}" is already exist in favorite list!').format(fav_format),
                Gtk.MessageType.INFO)
            return
        
        fav_list.append(fav_format)
        self.save_fav_list(fav_list)
        
        self.load_submenu()
    
    def save_fav_list(self, fav_list):
        favfile = open(FAV_FILE, "wb")
        pickle.dump(fav_list, favfile)
        favfile.close()
    
    
    def on_edit_fav(self, action, param):
        fav_list = self.get_fav_list()
        if not fav_list:
            self.info_bar.show_message(_('No Favorites List.'), Gtk.MessageType.WARNING)
            return
        fav_dlg = FavoriteDialog(self, self.get_fav_list())
        fav_dlg.run()
        fav_dlg.save(FAV_FILE)
        self.load_submenu()
        fav_dlg.destroy()

    
    def on_cb_remove_toggled(self, w):
        self.cb_rename.set_sensitive(not w.get_active())
    
    
    def on_cb_rename_toggled(self, w):
        self.cb_remove.set_sensitive(not w.get_active())
    
    
    def on_entry_player_changed(self, e):
        e.set_icon_from_icon_name(Gtk.EntryIconPosition.PRIMARY, e.get_text())
        self.player = e.get_text()
    
    
    def __init__(self, app, *files_list):
        
        # Install Local
        self.install_locale()

        # Super class
        Gtk.Window.__init__(self, title=_('Curlew'), application=app)
        self.app = app
        
        # Global menu
        gmenu = Gio.Menu()
        self.app.set_app_menu(gmenu)
        
        # Global menu items
        gmenu.append(_("About"), "win.about")
        about_action = Gio.SimpleAction.new("about", None)
        about_action.connect("activate", self.on_btn_about_clicked)
        self.add_action(about_action)
        
        gmenu.append(_("Quit"), "win.quit")
        quit_action = Gio.SimpleAction.new("quit", None)
        quit_action.connect("activate", self.quit_cb)
        self.add_action(quit_action)
    
        self.set_icon_name('curlew')
        
        # Restore saved position and size
        self.restore_last_position()
        
        #--- Global Variables
        self.curr_open_folder = HOME
        self.curr_save_folder = HOME
        self.is_converting = False
        self.is_merging = False
        self.fp_conv = None
        self.tree_iter = None
        self.total_duration = 0.0
        self.out_file = None
        self.counter = 20
        self.errs_nbr = 0
        self.pass_nbr = 0
        self.play_process = None
        self.task_type = TASK_CONVERT
        
        '''
        self.pass_nbr = 0: Single pass encoding option
        self.pass_nbr = 1: Two-pass encoding option (1st pass)
        self.pass_nbr = 2: Two-pass encoding option (2nd pass)
        '''
        
        self.encoder = ''
        self.player  = ''
        self.is_preview = False
        
        self._start_time = None
        self.elapsed_time = '0.00.00'
        
        self.last_format = None
        self.formats_list = []
        
        self.is_maxi = False
        
        #--- Regex
        self.reg_avconv_u = \
        re.compile('''size=\s+(\d+\.*\d*).*time=(\d+\.\d*)''')  # ubuntu
        self.reg_avconv_f = \
        re.compile('''size=\s+(\d+\.*\d*).*time=(\d+:\d+:\d+.\d+)''')  # fedora
        self.reg_duration = \
        re.compile('''Duration:.*(\d+:\d+:\d+\.\d+)''')
        
        self.link_label = _('Available Codecs')
        
        #--- Global vbox
        vbox_global = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(vbox_global)
        
        # Header bar
        self.header = Gtk.HeaderBar()
        self.header.set_show_close_button(True)
        self.set_titlebar(self.header)
        
        # Infobar
        self.info_bar = InfoBar()
        vbox_global.pack_start(self.info_bar, False, False, 0)
        
        
        # Add File/Folder buttons
        box_add = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        Gtk.StyleContext.add_class(box_add.get_style_context(), "linked")
        self.header.pack_start(box_add)
        
#         Gtk.IconSize.DIALOG
#         Gtk.IconSize.DND
#         Gtk.IconSize.MENU
#         Gtk.IconSize.LARGE_TOOLBAR
#         Gtk.IconSize.SMALL_TOOLBAR

        self.btn_add_file = ButtonWithIcon('document-new-symbolic')
        self.btn_add_file.set_tooltip_text(_('Add Files'))
        self.btn_add_file.connect('clicked', self.on_add_file_clicked)
        box_add.pack_start(self.btn_add_file, False, False, 0)
        
        self.btn_add_folder = ButtonWithIcon('folder-new-symbolic')
        self.btn_add_folder.set_tooltip_text(_('Add Folders'))
        self.btn_add_folder.connect('clicked', self.on_add_folder_clicked)
        box_add.pack_start(self.btn_add_folder, False, False, 0)
        
        # Remove/Clear buttons
        box_rm_clr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        Gtk.StyleContext.add_class(box_rm_clr.get_style_context(), "linked")
        self.header.pack_start(box_rm_clr)
        
        self.btn_remove = ButtonWithIcon('edit-delete-symbolic')
        self.btn_remove.set_tooltip_text(_('Remove Files'))
        self.btn_remove.connect('clicked', self.on_remove_cb)
        box_rm_clr.pack_start(self.btn_remove, False, False, 0)
        
        self.btn_clear = ButtonWithIcon('edit-clear-all-symbolic')
        self.btn_clear.set_tooltip_text(_('Clear Files List'))
        self.btn_clear.connect('clicked', self.on_clear_cb)
        box_rm_clr.pack_start(self.btn_clear, False, False, 0)
        
        # File info
        self.btn_info = ToggleBtnWithIcon('dialog-question-symbolic') 
        self.btn_info.set_tooltip_text(_('File Information'))
        self.btn_info.connect('toggled', self.on_file_info_cb)
        self.header.pack_start(self.btn_info)
        
        
        # Convert/Stop
        box_convert = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        Gtk.StyleContext.add_class(box_convert.get_style_context(), "linked")
        
        # Toggle options
        self.btn_opts = ToggleBtnWithIcon('emblem-system-symbolic')
        self.btn_opts.set_tooltip_text(_('Advanced Options'))
        self.btn_opts.connect('toggled', self.on_opts_toggled)
        self.header.pack_start(self.btn_opts)
        
        self.btn_convert = Gtk.Button(_('Convert'))
        self.btn_convert.set_size_request(90, -1)
        self.btn_convert.set_tooltip_text(_('Start Conversion'))
        self.btn_convert.connect('clicked', self.on_convert_cb)
        self.btn_convert.get_style_context().add_class(Gtk.STYLE_CLASS_SUGGESTED_ACTION)
        box_convert.pack_start(self.btn_convert, False, False, 0)
        
        # Switch button (Convert/Merge)
        self.btn_sw = Gtk.MenuButton()
        self.btn_sw.set_tooltip_text(_('Select Action'))
        self.btn_sw.get_style_context().add_class(Gtk.STYLE_CLASS_SUGGESTED_ACTION)
        box_convert.pack_start(self.btn_sw, False, False, 0)
        
        #-----------------------------------
        
        menu = Gio.Menu()
        self.btn_sw.set_menu_model(menu)
        
        action_con = Gio.SimpleAction.new('convert', None)
        action_con.connect('activate', self.convert_files_cb)
        
        action_mer = Gio.SimpleAction.new('merge', None)
        action_mer.connect('activate', self.merge_files_cb)
        
        #action_gif = Gio.SimpleAction.new('make-gif', None)
        #action_gif.connect('activate', self.make_gif_cb)
        
        self.add_action(action_con)
        self.add_action(action_mer)
        #self.add_action(action_gif)
        
        menu.append(_('Convert Files'), 'win.convert')
        menu.append(_('Merge Files'), 'win.merge')
        #menu.append('Make GIF', 'win.make-gif')
        
        #-----------------------------------
        
        self.btn_stop = ButtonWithIcon('process-stop-symbolic')
        self.btn_stop.set_tooltip_text(_('Stop Process'))
        self.btn_stop.connect('clicked', self.on_btn_stop_clicked)
        self.btn_stop.get_style_context().add_class(Gtk.STYLE_CLASS_DESTRUCTIVE_ACTION)
        box_convert.pack_start(self.btn_stop, False, False, 0)
        self.header.pack_start(box_convert)
        
        # Stack
        self.stack = Gtk.Stack()
        self.stack.set_transition_duration(500)
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_UP_DOWN)
        
        #--- Welcome page
        sw_welcome = Gtk.ScrolledWindow(border_width=4,
                                        shadow_type=Gtk.ShadowType.ETCHED_IN)
        self.stack.add_named(sw_welcome, CHILD_WELCOME)
        

        lbl_welcome = Gtk.Label(_('<b><span size="xx-large">Welcome to Curlew Multimedia Converter!</span></b>'),
                                use_markup=True)
        btn_files = ButtonWithIcon('document-new-symbolic', Gtk.IconSize.BUTTON)
        btn_files.set_relief(Gtk.ReliefStyle.NONE)
        btn_folders = ButtonWithIcon('folder-new-symbolic', Gtk.IconSize.BUTTON)
        btn_folders.set_relief(Gtk.ReliefStyle.NONE)
        
        hbox_btns = Gtk.Box(spacing=2)
        hbox_btns.pack_start(Gtk.Label(_('<i>Click</i>'), use_markup=True), False, False, 0)
        hbox_btns.pack_start(btn_files, False, False, 0)
        hbox_btns.pack_start(Gtk.Label(_('<i>to add files, or</i>'), use_markup=True), False, False, 0)
        hbox_btns.pack_start(btn_folders, False, False, 0)
        hbox_btns.pack_start(Gtk.Label(_('<i>to add files from folders,</i>'), use_markup=True), False, False, 0)
        
        align = Gtk.Alignment.new(0.5, 0.5, 0, 0)
        align.add(hbox_btns)
        
        vbox_elemts = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        
        vbox_elemts.pack_start(lbl_welcome, False, False, 0)
        vbox_elemts.pack_start(align, False, False, 0)
        vbox_elemts.pack_start(Gtk.Label(_('<i>or you can drag files and drop them to here.</i>'), use_markup=True), False, False, 0)
        
        align = Gtk.Alignment.new(0.5, 0.5, 0, 0)
        align.add(vbox_elemts)
        
        sw_welcome.add(align)
        
        btn_files.connect('clicked', self.on_add_file_clicked)
        btn_folders.connect('clicked', self.on_add_folder_clicked)
        
        #--- Merge page
        scroll_merge = Gtk.ScrolledWindow(border_width=4,
                                          shadow_type=Gtk.ShadowType.ETCHED_IN)
        vb_merge = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, border_width=8)
        scroll_merge.add(vb_merge)
        self.stack.add_named(scroll_merge, CHILD_MERGE)
        
        vb_widgets = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        vb_merge.pack_start(vb_widgets, True, False, 0)
        
        self.lbl_merge_status = Gtk.Label(use_markup=True)
        self.pb_merge = Gtk.ProgressBar()
        self.lbl_merge_details = Gtk.Label()
        
        vb_widgets.pack_start(self.lbl_merge_status, True, False, 0)
        vb_widgets.pack_start(self.pb_merge, True, False, 0)
        vb_widgets.pack_start(self.lbl_merge_details, True, False, 0)
        
        
        #--- List of files
        self.store = Gtk.ListStore(bool,  # active 
                                   str,  # file_name
                                   str,  # file size
                                   str,  # duration
                                   str,  # estimated file_size
                                   str,  # elapsed time
                                   str,  # time remaining
                                   float,  # progress
                                   str,  # status (progress txt)
                                   int,  # pulse
                                   str  # complete file_name
                                   )         
        self.tree = Gtk.TreeView(self.store)
        self.tree.set_has_tooltip(True)
        self.tree_sel = self.tree.get_selection()
        self.tree_sel.set_mode(Gtk.SelectionMode.MULTIPLE)
        
        self.tree.connect("button-press-event", self.on_tree_button_pressed)
        self.tree.connect("key-release-event", self.on_tree_key_released)
        self.tree.connect("cursor-changed", self.on_tree_cursor_changed)
        
        scroll = Gtk.ScrolledWindow(border_width=4)
        scroll.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        scroll.add(self.tree)
        
        self.paned = Gtk.Paned()
        self.stack.add_named(self.paned, CHILD_FILES)
        
        vbox_global.pack_start(self.stack, True, True, 0)
        
        #--- Image preview
        vbox_image = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        vbox_image.set_border_width(4)
        
        frame = Gtk.Frame()
        frame.set_shadow_type(Gtk.ShadowType.IN)
        frame.add(vbox_image)
        
        event_box = Gtk.EventBox(border_width=4)
        event_box.add(frame)
        event_box.connect('button-press-event', self.on_event_cb)
        
        self.image_prev = Gtk.Image()
        self.image_prev.set_padding(4, 4)
        
        # popup
        self.popup_hide = Gtk.Menu()
        self.hide_item = Gtk.CheckMenuItem.new_with_label(_('Show Sidebar'))
        self.hide_item.connect('toggled', self.on_hide_item_activate)
        self.popup_hide.append(self.hide_item)
        self.popup_hide.show_all()
        
        self.label_infos = Gtk.Label()
        
        vbox_image.pack_start(self.image_prev, False, True, 0)
        vbox_image.pack_start(self.label_infos, False, True, 6)
        
        self.paned.pack1(scroll, True, False)
        self.paned.pack2(event_box, False, False)
        
        self._child = self.paned.get_child2()
        
        #--- CheckButton cell
        cell = Gtk.CellRendererToggle()
        cell.connect('toggled', self.on_toggled_cb)
        col = Gtk.TreeViewColumn("#", cell, active=C_SKIP)
        self.tree.append_column(col)
        
        #--- Filename cell
        cell = Gtk.CellRendererText()
        col = Gtk.TreeViewColumn(_("File"), cell, text=C_NAME)
        col.set_resizable(True)
        col.set_min_width(100)
        self.tree.append_column(col)
        
        #--- filesize cell
        cell = Gtk.CellRendererText()
        col = Gtk.TreeViewColumn(_("Size"), cell, text=C_FSIZE)
        col.set_resizable(True)
        self.tree.append_column(col)
        
        #--- file duration cell
        cell = Gtk.CellRendererText()
        col = Gtk.TreeViewColumn(_("Duration"), cell, text=C_FDURA)
        col.set_resizable(True)
        self.tree.append_column(col)
        
        #--- Size cell
        cell = Gtk.CellRendererText()
        col = Gtk.TreeViewColumn(_("Estimated size"), cell, text=C_ESIZE)
        col.set_resizable(True)
        col.set_fixed_width(60)
        self.tree.append_column(col)
        
        #--- Elapsed time cell
        cell = Gtk.CellRendererText()
        col = Gtk.TreeViewColumn(_("Elapsed time"), cell, text=C_ELAPT)
        col.set_fixed_width(60)
        col.set_resizable(True)
        self.tree.append_column(col)
        
        #--- Remaining time cell
        cell = Gtk.CellRendererText()
        col = Gtk.TreeViewColumn(_("Remaining time"), cell, text=C_REMN)
        col.set_resizable(True)
        self.tree.append_column(col)
        
        #--- Progress cell
        cell = Gtk.CellRendererProgress()
        col = Gtk.TreeViewColumn(_("Progress"), cell,
                                 value=C_PRGR, text=C_STAT, pulse=C_PULS)
        col.set_min_width(80)
        col.set_resizable(True)
        self.tree.append_column(col)        
        
        
        #--- TreeView's Popup menu
        self.popup = self.build_treeview_popup()
        
        # Formats dialog
        self.btn_formats = Gtk.MenuButton()
        self.btn_formats.set_tooltip_markup(_("Choose a format"))
        vbox = Gtk.Box(spacing=6, orientation=Gtk.Orientation.VERTICAL)
        vbox.set_border_width(4)
        vbox_global.add(vbox)
        
        hbox = Gtk.Box()
        Gtk.StyleContext.add_class(hbox.get_style_context(), "linked")
        vbox.add(hbox)
        
        # Fav button
        self.btn_fav = ButtonWithIcon('user-bookmarks-symbolic')
        self.btn_fav.set_tooltip_text(_("Add to Favorite"))
        self.btn_fav.connect('clicked', self.on_add_fav)
        
        # Fav Button
        self.mb_fav = Gtk.MenuButton()
        self.mb_fav.set_tooltip_markup(_("Favorite list"))
        self.mb_fav.set_image(Gtk.Image
                              .new_from_icon_name("view-list-symbolic",
                                                  Gtk.IconSize.MENU))
        
        hbox.pack_start(self.btn_formats, True, True, 0)
        hbox.pack_start(self.btn_fav , False, False, 0)
        hbox.pack_start(self.mb_fav, False, False, 0)
        
        self.action_group = Gio.SimpleActionGroup()
        self.insert_action_group('Fav', self.action_group)
        
        self.menu_fav = Gio.Menu()
        self.mb_fav.set_menu_model(self.menu_fav)
        
        # edit_list btn
        menu_item_edit = Gio.MenuItem.new(_("Edit Favorite List"), 'Fav.EditList')
        action_edit = Gio.SimpleAction.new('EditList')
        action_edit.connect('activate', self.on_edit_fav)
        self.action_group.insert(action_edit)
#         icon = GLib.Variant.new_string('open-menu-symbolic')
#         menu_item_edit.set_attribute_value('verb-icon', icon)
        
        # menu btns
        menu_btns = Gio.Menu()
        #menu_btns.append_item(menu_item_add)
        menu_btns.append_item(menu_item_edit)
        
        item_btns = Gio.MenuItem.new_section(None, menu_btns)
        h_btns = GLib.Variant.new_string("horizontal-buttons")
        item_btns.set_attribute_value("display-hint", h_btns)
        
        self.menu_fav.append_item(item_btns)
        
        self.submenu = Gio.Menu()
        self.menu_fav.append_section(None, self.submenu)
        
        self.load_submenu()
        
        #--- advanced options
        self.note = Gtk.Notebook()
        self.note.set_border_width(4)
        self.stack.add_named(self.note, CHILD_ADVANCED)
        
        #--- audio page
        self.vb_audio = Gtk.Box(spacing=4, border_width=5, orientation=Gtk.Orientation.VERTICAL)
        self.note.append_page(self.vb_audio, Gtk.Label(_("Audio")))
       
        self.c_abitrate = ComboWithEntry()
        self.c_afreq = ComboWithEntry()
        self.c_ach = ComboWithEntry()
        
        self.c_acodec = ComboWithEntry()
        self.c_acodec.connect('changed', self.on_codec_changed)
        self.l_acodec = Gtk.Label()
        hbox_acodec = Gtk.Box(spacing=10)
        hbox_acodec.pack_start(self.c_acodec, True, True, 0)
        hbox_acodec.pack_start(self.l_acodec, True, True, 0)

        
        grid_audio = LabeledGrid(self.vb_audio)
        grid_audio.append_row(_("Audio Bitrate"), self.c_abitrate)
        grid_audio.append_row(_("Audio Frequency"), self.c_afreq)
        grid_audio.append_row(_("Audio Channels"), self.c_ach)
        grid_audio.append_row(_("Audio Codec"), hbox_acodec)
        
        # Convert all tracks
        self.cb_all_tracks = Gtk.CheckButton(_('Include all tracks'))
        self.cb_all_tracks.set_tooltip_text(_('Convert all audio tracks of file'))
        self.vb_audio.add(self.cb_all_tracks)
        
        # Volume slider
        self.hb_volume = LabeledHBox(_('Volume (%)'), self.vb_audio)
        self.vol_scale = HScale(self.hb_volume, 100, 25, 400, 25)
        
        # Audio quality for ogg
        self.hb_aqual = LabeledHBox(_('Audio Quality'), self.vb_audio)
        self.a_scale = HScale(self.hb_aqual, 3, 0, 10)
        
        link = Gtk.LinkButton()
        link.set_label(self.link_label)
        link.set_alignment(1.0, 0.5)
        link.connect('activate-link', self.on_link_clicked)
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.vb_audio.pack_end(hbox, False, False, 0)
        hbox.pack_end(link, False, False, 0)
        
        
        #--- video page
        self.vb_video = Gtk.Box(spacing=4, border_width=5, orientation=Gtk.Orientation.VERTICAL)
        self.note.append_page(self.vb_video, Gtk.Label(_("Video")))
        

        self.c_vbitrate = ComboWithEntry()
        self.c_vfps = ComboWithEntry()
        self.c_vsize = ComboWithEntry()
        
        self.c_vcodec = ComboWithEntry()
        self.c_vcodec.connect('changed', self.on_codec_changed)
        self.l_vcodec = Gtk.Label()
        hbox_vcodec = Gtk.Box(spacing=10)
        hbox_vcodec.pack_start(self.c_vcodec, True, True, 0)
        hbox_vcodec.pack_start(self.l_vcodec, False, False, 0)
        
        self.c_vratio = ComboWithEntry()
        
        grid_video = LabeledGrid(self.vb_video)
        grid_video.append_row(_("Video Bitrate"), self.c_vbitrate)
        grid_video.append_row(_("Video FPS"), self.c_vfps)
        grid_video.append_row(_("Video Size"), self.c_vsize)
        grid_video.append_row(_("Video Codec"), hbox_vcodec)
        grid_video.append_row(_("Aspect Ratio"), self.c_vratio)
        
        hbox = Gtk.Box(spacing=8)
        self.vb_video.pack_start(hbox, False, False, 0)
        
        # 2-pass
        self.cb_2pass = Gtk.CheckButton(_('2-Pass'))
        hbox.pack_start(self.cb_2pass, False, False, 0)
        
        # Video only (no sound)
        self.cb_video_only = Gtk.CheckButton(_('Video only'))
        self.cb_video_only.connect('toggled', self.on_cb_video_only_toggled)
        hbox.pack_start(self.cb_video_only, False, False, 0)
        
        # Fix for bad index file
        self.cb_bad_indx = Gtk.CheckButton(_('Fix bad index'))
        self.cb_bad_indx.set_tooltip_text("")
        hbox.pack_start(self.cb_bad_indx, False, False, 0)
        
        # Video quality for ogv
        self.hb_vqual = LabeledHBox(_('Video Quality'), self.vb_video)
        self.v_scale = HScale(self.hb_vqual, 5, 0, 20)

        link = Gtk.LinkButton()
        link.set_label(self.link_label)
        link.set_alignment(1.0, 0.5)
        link.connect('activate-link', self.on_link_clicked)
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.vb_video.pack_end(hbox, False, False, 0)
        hbox.pack_end(link, False, False, 0)
        
        #--- Subtitle page
        self.frame_sub = Gtk.Frame(border_width=5)
        self.note.append_page(self.frame_sub, Gtk.Label(_("Subtitle")))
        
        self.vb_sub = Gtk.Box(spacing=5, border_width=5, sensitive=False, orientation=Gtk.Orientation.VERTICAL)
        self.frame_sub.add(self.vb_sub)
        
        #--- Sub Active/Desactive
        self.cb_sub = Gtk.CheckButton(_('Use Subtitle (ffmpeg only)'))
        self.frame_sub.set_label_widget(self.cb_sub)
        self.cb_sub.connect('toggled', self.cb_sub_toggled)
        
        grid_sub = LabeledGrid(self.vb_sub)
        
        #--- Subtitle filename
        self.hb_sub = Gtk.Box()
        Gtk.StyleContext.add_class(self.hb_sub.get_style_context(), "linked")
        self.entry_sub = Gtk.Entry()
        self.hb_sub.pack_start(self.entry_sub, True, True, 0)
        
        #---- Select subtitle
        b_enc = Gtk.Button(' ... ')
        self.hb_sub.pack_start(b_enc, False, False, 0)
        b_enc.connect('clicked', self.b_enc_cb)
        grid_sub.append_row(_('Subtitle: '), self.hb_sub, True)
        
        #--- Subtitle font
        self.b_font = Gtk.FontButton()
        self.b_font.set_show_size(False)
        self.b_font.set_show_style(False)
        
        # grid_sub.append_row(_('Font: '), self.b_font, True)
        
        hbox = Gtk.Box(spacing=30)
        
        #--- Subtitle position
        self.hb_pos = Gtk.Box(spacing=4)
        
        adj = Gtk.Adjustment(100, 0, 100, 2)
        self.spin_pos = Gtk.SpinButton(adjustment=adj)
        self.hb_pos.pack_start(self.spin_pos, True, True, 0)
        
        self.hb_pos.pack_start(Gtk.Label('      ' + _('Size: ')), True, True, 0)
        
        #--- Subtitle size
        adj = Gtk.Adjustment(4, 0, 100, 1)
        self.spin_size = Gtk.SpinButton(adjustment=adj)
        self.hb_pos.pack_start(self.spin_size, True, True, 0)
        
        # grid_sub.append_row(_('Position: '), self.hb_pos, False)
        
        self.vb_sub.pack_start(hbox, False, False, 0)
        
        
        #--- Subtitle Encoding
        encs = [
                'cp1250', 'cp1252', 'cp1253', 'cp1254',
                'cp1255', 'cp1256', 'cp1257', 'cp1258',
                'iso-8859-1', 'iso-8859-2', 'iso-8859-3', 'iso-8859-4',
                'iso-8859-5', 'iso-8859-6', 'iso-8859-7', 'iso-8859-8',
                'iso-8859-9', 'iso-8859-10', 'iso-8859-11', 'iso-8859-12',
                'iso-8859-13', 'iso-8859-14', 'iso-8859-15', 'utf-7',
                'utf-8', 'utf-16', 'utf-32', 'ASCII'
                ]
        self.cmb_encoding = Gtk.ComboBoxText()
        self.cmb_encoding.set_entry_text_column(0)
        self.cmb_encoding.set_id_column(0)
        for enc in encs:
            self.cmb_encoding.append_text(enc)
        self.cmb_encoding.set_active(5)
        self.cmb_encoding.set_wrap_width(6)
        grid_sub.append_row(_('Encoding: '), self.cmb_encoding, True)
        
        # Delay subtitle
        self.hb_delay = Gtk.Box(spacing=6)
        self.sub_delay = Gtk.SpinButton()        
        self.sub_delay.set_adjustment(Gtk.Adjustment(0, -90000, 90000, 1))
        self.hb_delay.pack_start(self.sub_delay, False, True, 0)
        self.hb_delay.pack_start(Gtk.Label(_("sec")), False, False, 0)
        # grid_sub.append_row(_('Delay: '), self.hb_delay)
        
        
        # Filters page
        # -- Fade Filter
        grid_filters = LabeledGrid()
        grid_filters.set_border_width(5)
        self.note.append_page(grid_filters, Gtk.Label(_('Filters')))
        
        grid_filters.append_title(_('Fade In / Fade Out'))
        self.spin_fade = Gtk.SpinButton().new_with_range(0, 20, 1)
        hbox_fade = Gtk.Box(spacing=8)
        grid_filters.append_widget(hbox_fade)
        
        hbox_fade.add(Gtk.Label(_('Duration (sec)')))
        hbox_fade.add(self.spin_fade)
        
        self.cmb_fade_pos = ComboWithEntry(False)
        self.cmb_fade_pos.set_list([_('At the beginning'), _('At the end'), _('Both')])
        hbox_fade.add(Gtk.Label(_('Position')))
        hbox_fade.add(self.cmb_fade_pos)
        
        self.cmb_fade_type = ComboWithEntry(False)
        self.cmb_fade_type.set_list([_('Audio'), _('Video'), _('Both')])
        hbox_fade.add(Gtk.Label(_('Type')))
        hbox_fade.add(self.cmb_fade_type)
        
        # -- Crop/Pad Filters        
        grid_filters.append_title(_('Crop / Pad'))
        
        # Cropping
        self.crop = SpinsFrame(_('Crop'))
        grid_filters.append_widget(self.crop)
        
        # Padding
        self.pad = SpinsFrame(_('Pad'))
        grid_filters.append_widget(self.pad)
        
        #--- "More" page
        self.vb_more = Gtk.Box(spacing=4, border_width=5, orientation=Gtk.Orientation.VERTICAL)
        self.note.append_page(self.vb_more, Gtk.Label(_("More")))
        
        # Split file
        self.cb_split = Gtk.CheckButton(_('Split File'))
        self.cb_split.connect('toggled', self.cb_split_cb)
        
        self.frame = Gtk.Frame(label_widget=self.cb_split)
        self.vb_more.pack_start(self.frame, False, False, 0)
        
        self.vb_group = Gtk.Box(sensitive=False, spacing=4, orientation=Gtk.Orientation.VERTICAL)
        self.vb_group.set_border_width(4)
        self.frame.add(self.vb_group)
        
        self.tl_begin = TimeLayout(self.vb_group, _('Begin time: '))
        hb_dur = Gtk.Box(spacing=10)
        self.vb_group.pack_start(hb_dur, False, False, 0)
        self.tl_duration = TimeLayout(hb_dur, _('Duration: '))
        self.cb_end = Gtk.CheckButton(_('To the end'))
        self.cb_end.connect('toggled', self.cb_end_cb)
        hb_dur.pack_start(self.cb_end, False, False, 0)
        self.tl_duration.set_duration(5)
        
        # Copy Mode
        self.cb_copy = Gtk.CheckButton(_('Use Copy Mode'))
        self.cb_copy.set_tooltip_text(_("Keep the same codecs as the input file"))
        self.cb_copy.connect('toggled', self.on_cb_copy_mode_toggled)
        self.vb_group.add(self.cb_copy)
        
        # Other Parameters entry.
        grid_other = LabeledGrid(self.vb_more)
        self.e_extra = Gtk.Entry()
        
        grid_other.append_row(_('Other opts:'), self.e_extra, True)
        
        # Threads
        self.s_threads = Gtk.SpinButton.new_with_range(0, 10, 1)
        grid_other.append_row(_('Threads:'), self.s_threads)
        
        # Encoder type (ffmpeg / avconv)
        self.cmb_encoder = ComboWithEntry(with_entry=True)
        self.cmb_encoder.set_id_column(0)
        self.cmb_encoder.connect('changed', self.cmb_encoder_cb)
        
        hbox_enc = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        hbox_enc.pack_start(self.cmb_encoder, False, False, 0)
        self.btn_enc = Gtk.Button('...')
        self.btn_enc.connect('clicked', self.browse_for_encoder)
        hbox_enc.pack_start(self.btn_enc, False, False, 0)
        
        grid_other.append_row(_('Converter:'), hbox_enc)
        
        # Player
        self.entry_player = Gtk.Entry()
        self.entry_player.set_text(self.player)
        self.entry_player.connect('changed', self.on_entry_player_changed)
        grid_other.append_row(_('Player:'), self.entry_player)
        
        
        # File info Page
        self.txt_info = Gtk.TextView()
        self.txt_info.set_editable(False)
        self.txt_info.set_cursor_visible(False)
        self.txt_info.set_border_width(8)
        
        self.scroll_info = Gtk.ScrolledWindow()
        self.scroll_info.set_shadow_type(Gtk.ShadowType.IN)
        self.scroll_info.add(self.txt_info)
        self.scroll_info.set_border_width(4)
        
        font_desc = Pango.FontDescription('Monospace')
        self.txt_info.override_font(font_desc)
        
        self.txt_buffer_info = Gtk.TextBuffer()
        self.txt_info.set_buffer(self.txt_buffer_info)
        
        self.stack.add_named(self.scroll_info, CHILD_INFOS)
                
        
        # Load internal encoder (ffmpeg)
        if exists(INTERNAL_ENCODER):
            self.cmb_encoder.append_text(INTERNAL_ENCODER)
        # Load available encoder
        if which('avconv'):
            self.cmb_encoder.append_text(which('avconv'))
        if which('ffmpeg'):
            self.cmb_encoder.append_text(which('ffmpeg'))
        
        self.cmb_encoder.set_active(0)
        
        # Check player
        if not get_s_config('player'):
            plyr = choose_player()
            if plyr:
                self.entry_player.set_text(plyr)
            else:
                self.info_bar.show_message(_('Please select a player'), Gtk.MessageType.ERROR)
                self.show_all()
                self.btn_opts.set_active(True)
                self.note.set_current_page(4)
                self.set_focus(self.entry_player)
                    
        
        #--- Configuration page
        self.vb_config = Gtk.Box(spacing=4, border_width=5, orientation=Gtk.Orientation.VERTICAL)
        self.note.append_page(self.vb_config, Gtk.Label(_('Configs')))
        
        grid_config = LabeledGrid(self.vb_config)
        
        
        #--- Application language
        self.cmb_lang = ComboWithEntry(False)
        self.cmb_lang.set_tooltip_markup(_("Your language will appear after restart Curlew"))
        self.cmb_lang.set_id_column(0)
        # Fill
        self.cmb_lang.set_list(sorted(LANGUAGES.keys()))
        self.cmb_lang.prepend_text('< System >')
        self.cmb_lang.set_active(0)
        
        grid_config.append_row(_('Language:'), self.cmb_lang)
        
        # Show / Hide side bar
        self.cb_sideb = Gtk.CheckButton(_('Show Sidebar'))
        self.cb_sideb.connect('toggled', self.on_cb_sideb_toggled)
        self.vb_config.pack_start(self.cb_sideb, False, False, 0)
        
        # Use tray icon
        self.cb_tray = Gtk.CheckButton(_('Show tray icon'))
        self.cb_tray.connect('toggled', self.on_cb_tray_toggled)
        self.vb_config.pack_start(self.cb_tray, False, False, 0)
        
        # Show/Hide Statusbar
        self.cb_status = Gtk.CheckButton(_('Show Statusbar'))
        self.cb_status.connect('toggled', self.on_cb_status_toggled)
        self.vb_config.pack_start(self.cb_status, False, False, 0)
        
        sep = Gtk.Separator()
        self.vb_config.pack_start(sep, False, False, 0)
        
        # Shutdown after conversion
        self.cb_halt = Gtk.CheckButton(_('Shutdown computer after finish'))
        self.cb_halt.connect('toggled', self.on_cb_halt_toggled)
        self.vb_config.pack_start(self.cb_halt, False, False, 0)
        
        # Suspend after conversion
        self.cb_suspend = Gtk.CheckButton(_('Suspend computer after finish'))
        self.cb_suspend.connect('toggled', self.on_cb_suspend_toggled)
        self.vb_config.pack_start(self.cb_suspend, False, False, 0)
        
        # Play sound after conversion
        self.cb_play = Gtk.CheckButton(_('Play sound after finish'))
        self.vb_config.pack_start(self.cb_play, False, False, 0)
        
        # Output page
        self.vb_output = Gtk.Box(spacing=4, border_width=5, orientation=Gtk.Orientation.VERTICAL)
        grid_output = LabeledGrid(self.vb_output)
        self.note.append_page(self.vb_output, Gtk.Label(_('Output')))
        
        #--- Destination
        self.e_dest = Gtk.Entry()
        self.e_dest.set_text(HOME)
        self.b_dest = Gtk.Button('...')
        self.cb_dest = Gtk.CheckButton(_('Source Path'))
        self.cb_dest.connect('toggled', self.on_cb_dest_toggled)
        self.b_dest.connect('clicked', self.on_dest_clicked)
        
        hbox = Gtk.Box(spacing=4)
        grid_output.append_row(_('Destination:'), hbox, True)
        
        self.entry_merged_file = Gtk.Entry()
        self.entry_merged_file.set_tooltip_text(_("This name is for merged file"))
        grid_output.append_row(_('Output Filename:'), self.entry_merged_file, True)
        self.entry_merged_file.set_text('output_file')
        
        # Replace/Skip/Rename
        self.cmb_exist = ComboWithEntry(False)
        self.cmb_exist.set_list([_('Overwrite it'),
                                 _('Choose another name'),
                                 _('Skip conversion')])
        grid_output.append_row(_('File exist:'), self.cmb_exist)
        
        hbox2 = Gtk.Box()
        Gtk.StyleContext.add_class(hbox2.get_style_context(), "linked")
        hbox2.pack_start(self.e_dest, True, True, 0)
        hbox2.pack_start(self.b_dest, False, True, 0)
        
        hbox.pack_start(hbox2, True, True, 0)
        hbox.pack_start(self.cb_dest, False, False, 0)
        
        sep = Gtk.Separator()
        self.vb_output.pack_start(sep, False, False, 0)
        
        # Remove source file
        self.cb_remove = Gtk.CheckButton(_('Delete input file after conversion'))
        self.cb_remove.connect('toggled', self.on_cb_remove_toggled)
        self.vb_output.pack_start(self.cb_remove, False, False, 0)

        # Rename source file
        self.cb_rename = Gtk.CheckButton(_('Rename input file after conversion'))
        self.cb_rename.connect('toggled', self.on_cb_rename_toggled)
        self.vb_output.pack_start(self.cb_rename, False, False, 0)
        
        #--- Status
        self.label_details = Gtk.Label()
        self.label_details.set_no_show_all(True)
        vbox.pack_start(self.label_details, False, False, 0)
        
        # Status icon
        self.trayico = StatusIcon(self)
        
        #--- Load formats from formats.cfg file
        self.f_file = ConfigParser()
        try:
            self.f_file.read(self.get_formats_file_name())
        except Exception as e:
            show_message(self, e.__str__(), Gtk.MessageType.ERROR)
            exit()
        
        self.formats_list = self.f_file.sections()
        
        #--- Load saved options.
        self.btn_formats.set_label(self.formats_list[0])
        self.load_states()
        
        self.show_interface()        
        self.fill_options()
        
        my_store = Gtk.ListStore(str)
        f_dlg = Formats(self, self.formats_list, self.btn_formats.get_label(), my_store)
        self.btn_formats.set_popover(f_dlg)
        
        
        
        
        #--- Drag and Drop
        targets = Gtk.TargetList.new([])
        targets.add_uri_targets((1 << 5) - 1)
        self.drag_dest_set(Gtk.DestDefaults.ALL, [], Gdk.DragAction.COPY)
        self.drag_dest_set_target_list(targets)
        self.connect('drag-data-received', self.drop_data_cb)
        
        #--- Window connections
        self.connect('delete-event', self.on_delete)
        self.connect("key-press-event", self.on_key_press)
        self.connect("window-state-event", self.on_window_state)
    
        #--- Status icon
        self.trayico.set_visible(self.cb_tray.get_active())
        
        if files_list:
            self.add_files(*files_list)
            
    def on_toggled_cb(self, widget, Path):
        self.store[Path][C_SKIP] = not self.store[Path][C_SKIP]        
    
    def on_key_press(self, widget, event):
        """Cancel preview and stop conversion"""
        if event.keyval == Gdk.KEY_Escape:
            self.is_preview = False
            self.on_btn_stop_clicked()
        # Paste (Control + V)
        elif event.keyval == 118:
            clip = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
            uris = clip.wait_for_uris()
            if uris:
                self.add_files(*uris)
    
    def on_window_state (self, w, e):
        mask = Gdk.WindowState.MAXIMIZED
        self.is_maxi = self.get_window().get_state() & mask == mask
            
    def on_delete(self, widget, data):
        if self.cb_tray.get_active():
            self.hide_on_delete()
        else:
            self.quit_cb(widget)
        return True
    
    def quit_cb(self, *args):
        self.save_states()
        
        # Stop playing before quit.
        if self.play_process != None:
            if self.play_process.poll() == None:
                self.play_process.kill()
        
        # Stop converting or merging
        if self.is_converting or self.is_merging:
            ''' Press quit btn during conversion process '''
            resp = show_message(self, _('Do you want to quit Curlew and abort process?'),
                                Gtk.MessageType.QUESTION,
                                Gtk.ButtonsType.YES_NO)
            if resp == Gtk.ResponseType.YES:
                if self.is_converting:
                    self.fp_conv.kill()
                elif self.is_merging:
                    self.fp_mrg.kill()
                self.force_delete_file(self.out_file)
                self.app.quit()
            return
        
        # Quit normaly
        self.app.quit()
    
    #--- Add files
    def on_add_file_clicked(self, *args):
        open_dlg = Gtk.FileChooserDialog(_("Add file"),
                                         self, Gtk.FileChooserAction.OPEN,
                                        (_('_OK'),
                                         Gtk.ResponseType.OK,
                                         _('_Cancel'),
                                         Gtk.ResponseType.CANCEL))
        if self.curr_open_folder:
            open_dlg.set_current_folder(self.curr_open_folder)
        open_dlg.set_select_multiple(True)
        open_dlg.set_icon_name('curlew')
        
        #--- File filters
        Filter = Gtk.FileFilter()
        Filter.set_name(_("All supported files"))
        Filter.add_mime_type("video/*")
        Filter.add_mime_type("audio/*")
        Filter.add_pattern("*.[Rr][Mm]*")
        open_dlg.add_filter(Filter)
        
        Filter = Gtk.FileFilter()
        Filter.set_name(_("Video files"))
        Filter.add_mime_type("video/*")
        Filter.add_pattern("*.[Rr][Mm]*")
        open_dlg.add_filter(Filter)
        
        Filter = Gtk.FileFilter()
        Filter.set_name(_("Audio files"))
        Filter.add_mime_type("audio/*")
        Filter.add_pattern("*.[Rr][Mm]")
        open_dlg.add_filter(Filter)
        
        Filter = Gtk.FileFilter()
        Filter.set_name(_("All files"))
        Filter.add_pattern("*")
        open_dlg.add_filter(Filter)
        
        res = open_dlg.run()
        if res == Gtk.ResponseType.OK:
            files = open_dlg.get_filenames()
            self.curr_open_folder = open_dlg.get_current_folder()
            open_dlg.destroy()
            self.add_files(*files)
        else:
            open_dlg.destroy()
        
    def add_files(self, *files):
        file_name = ''
        wait_dlg = WaitDialog(self)
        tot = len(files)

        mimetypes.add_type('video/realmedia', '.rmvb')
        mimetypes.add_type('video/mpeg', '.VOB')
        for file_name in files:
            mime = mimetypes.guess_type(file_name)[0]
            if mime != None:
                if 'video/' in mime or 'audio/' in mime:

                    wait_dlg.set_filename(basename(file_name))
                    wait_dlg.set_progress((files.index(file_name) + 1.0) / tot)
                    if wait_dlg.skip: break
                    
                    while Gtk.events_pending():
                        Gtk.main_iteration()

                    if file_name.startswith('file://'):
                        file_name = unquote(file_name[7:])
                    if isfile(file_name):
                        dura = self.get_time(file_name)
                        self.store.append([
                                           True,
                                           splitext(basename(file_name))[0],
                                           get_format_size(getsize(file_name) / 1024),
                                           dura,
                                           None,
                                           None,
                                           None,
                                           0.0,
                                           _('Ready!'),
                                           - 1,
                                           realpath(file_name)
                                           ])
        
        wait_dlg.destroy()
        
        self.stack.set_visible_child_full(CHILD_FILES,
                                          Gtk.StackTransitionType.CROSSFADE)
        
        return dirname(file_name) + os.sep
    
    #--- Add folder that contain media files
    def on_add_folder_clicked(self, mi):
        folder_dlg = Gtk.FileChooserDialog(_('Add folder'), self,
                                           Gtk.FileChooserAction.SELECT_FOLDER,
                                           (_('_OK'),
                                            Gtk.ResponseType.OK,
                                            _('_Cancel'),
                                            Gtk.ResponseType.CANCEL)
                                           )
        folder_dlg.set_select_multiple(True)
        folder_dlg.set_icon_name('curlew')
        
        if self.curr_open_folder:
            folder_dlg.set_current_folder(self.curr_open_folder)
            folder_dlg.set_filename(self.curr_open_folder)
        
        resp = folder_dlg.run()
        if resp == Gtk.ResponseType.OK:
            files_list = []
            curr_folders = folder_dlg.get_filenames()
            for curr_folder in curr_folders:
                for root, dirs, files in os.walk(curr_folder):
                    it_files = (join(root, file_name) for file_name in files)
                    for curr_file in it_files:
                        files_list.append(curr_file)
                
            self.curr_open_folder = folder_dlg.get_filename()
            folder_dlg.destroy()
            self.add_files(*files_list)
        folder_dlg.destroy()
    
    
    def on_dest_clicked(self, widget):
        save_dlg = Gtk.FileChooserDialog(_("Choose destination"), self,
                                    Gtk.FileChooserAction.SELECT_FOLDER,
                                    (_('_OK'), Gtk.ResponseType.OK,
                                    _('_Cancel'), Gtk.ResponseType.CANCEL))
        save_dlg.set_current_folder(self.curr_save_folder)
        save_dlg.set_icon_name('curlew')
        res = save_dlg.run()
        if res == Gtk.ResponseType.OK:
            self.e_dest.set_text(save_dlg.get_filename())
        self.curr_save_folder = save_dlg.get_current_folder()
        save_dlg.destroy()
    
    def cb_split_cb(self, cb_split):
        self.vb_group.set_sensitive(cb_split.get_active())    
    
    def set_visibilities(self):
        section = self.btn_formats.get_label()
        media_type = self.f_file.get(section, 'type')

        # sens : [AudioP, VideoP, SubtitleP, aQuality, vQuality, CropPad]
        sens = {
                'audio': [True, False, False, False, False, False, True],
                'video': [True, True, True, False, False, True, True],
                'ogg': [True, False, False, True, False, False, True],
                'ogv': [True, True, False, True, True, False, True],
                'presets': [False, False, False, False, False, False, False],
                'copy': [False, False, True, False, False, False, False]
                }

        self.vb_audio.set_visible(sens[media_type][0])  # Audio page
        self.vb_video.set_visible(sens[media_type][1])  # Video page
        self.frame_sub.set_visible(sens[media_type][2])  # Subtitle page
        self.hb_aqual.set_visible(sens[media_type][3])  # Audio quality slider (ogg)
        self.hb_vqual.set_visible(sens[media_type][4])  # video Quality slider (ogv)
        self.crop.set_sensitive(sens[media_type][5])
        self.pad.set_sensitive(sens[media_type][5])
        
        # Select first visible page.
        widgets = (self.vb_audio, self.vb_video, self.frame_sub)
        for widget in widgets:
            if not widget.get_visible():
                continue
            else:
                self.note.set_current_page(widgets.index(widget))
                break
        
    
    def show_interface(self):
        # Show all widgets
        self.show_all()
        # Hide some widgets
        self.vb_audio.hide()
        self.vb_video.hide()
        self.frame_sub.hide()
        self.hb_aqual.hide()
        self.hb_vqual.hide()
    
    #--- fill options widgets
    def fill_options(self):
        section = self.btn_formats.get_label()
        
        # reread formats file
        self.f_file.read(self.get_formats_file_name())
        
        #
        if not self.f_file.has_section(section):
            self.remove_from_fav(section)
            self.btn_formats.set_label(self.formats_list[0])
            return
        
        # Call
        self.set_visibilities()
        
        if self.f_file.has_option(section, 'extra'):
            self.e_extra.set_text(self.f_file[section]['extra'])
        else:
            self.e_extra.set_text('')
            
        # For presets
        if self.f_file.has_option(section, 'cmd'):
            self.presets_cmd = self.f_file[section]['cmd'].split()
            return
            
        if self.f_file.has_option(section, 'ab'):
            self.c_abitrate.set_list(self.f_file[section]['ab'].split())
            
        if self.f_file.has_option(section, 'def_ab'):
            self.c_abitrate.set_text(self.f_file[section]['def_ab'])
        
        if self.f_file.has_option(section, 'afreq'):
            self.c_afreq.set_list(self.f_file[section]['afreq'].split())
        
        if self.f_file.has_option(section, 'ach'):    
            self.c_ach.set_list(self.f_file[section]['ach'].split())
        
        if self.f_file.has_option(section, 'acodec'):
            self.c_acodec.set_list(self.f_file[section]['acodec'].split())
            
        if self.f_file.has_option(section, 'vb'):
            self.c_vbitrate.set_list(self.f_file[section]['vb'].split())
            
        if self.f_file.has_option(section, 'def_vb'):
            self.c_vbitrate.set_text(self.f_file[section]['def_vb'])
            
        if self.f_file.has_option(section, 'vfps'):
            self.c_vfps.set_list(self.f_file[section]['vfps'].split())
        
        if self.f_file.has_option(section, 'vcodec'):
            self.c_vcodec.set_list(self.f_file[section]['vcodec'].split())
            
        if self.f_file.has_option(section, 'vsize'):
            self.c_vsize.set_list(self.f_file[section]['vsize'].split())
        
        if self.f_file.has_option(section, 'vratio'):
            self.c_vratio.set_list(self.f_file[section]['vratio'].split())
        
        
    
    def build_cmd(self,
                         input_file, out_file,
                         start_pos='-1', part_dura='-1'):
        '''
        start_pos <=> -ss, part_dura <=> -t
        '''
        section = self.btn_formats.get_label()
        media_type = self.f_file.get(section, 'type')
        
        cmd = [self.encoder, '-y', '-hide_banner']  # , '-xerror']
        
        # Bad index
        if self.cb_bad_indx.get_active():
            cmd.extend(['-fflags','+igndts+genpts'])
        
        if start_pos != '-1' and part_dura != '-1':
            cmd.extend(['-ss', start_pos])
        
        cmd.extend(['-i', input_file])
        
        # Threads nbr
        if self.s_threads.get_value() != 0:
            cmd.extend(['-threads',
                        '{}'.format(self.s_threads.get_value_as_int())])
        
        # Force format
        if self.f_file.has_option(section, 'ff'):
            cmd.extend(['-f', self.f_file.get(section, 'ff')])
            
        # Extract Audio
        if media_type in ['audio', 'ogg']:
            cmd.append('-vn')

       
        # Fade filter
        if self.spin_fade.get_value() != 0:
            d = self.spin_fade.get_value()
            st = self.get_duration(input_file) - d
            
            cmd_fa_b = 'afade=t=in:ss=0:d={}'.format(d)
            cmd_fa_e = 'afade=t=out:st={0}:d={1}'.format(st, d)
            cmd_fa_a = 'afade=t=in:ss=0:d={0},afade=t=out:st={1}:d={0}'.format(d, st)
            
            cmd_fv_b = 'fade=in:st=0:d={}'.format(d)
            cmd_fv_e = 'fade=out:st={0}:d={1}'.format(st, d)
            cmd_fv_a = 'fade=in:st=0:d={0},fade=out:st={1}:d={0}'.format(d, st)
            
            #--- is fade active
            if self.spin_fade.get_value() != 0:
                
                #if audio
                if self.cmb_fade_type.get_active()  ==  0:
                    fade_a_strs = ['-af']
                    if self.cmb_fade_pos.get_active()  ==  0:
                        fade_a_strs.append(cmd_fa_b)
                    elif self.cmb_fade_pos.get_active() == 1:
                        fade_a_strs.append(cmd_fa_e)
                    elif self.cmb_fade_pos.get_active() == 2:
                        fade_a_strs.append(cmd_fa_a)
                    cmd.extend(fade_a_strs)
                
                # if video
                elif self.cmb_fade_type.get_active() == 1:
                    fade_v_strs = ['-vf']
                    if self.cmb_fade_pos.get_active()  ==  0:
                        fade_v_strs.append(cmd_fv_b)
                    elif self.cmb_fade_pos.get_active() == 1:
                        fade_v_strs.append(cmd_fv_e)
                    elif self.cmb_fade_pos.get_active() == 2:
                        fade_v_strs.append(cmd_fv_a)
                    cmd.extend(fade_v_strs)
                
                # video and audio
                elif self.cmb_fade_type.get_active() == 2:
                    fade_a_strs = ['-af']
                    fade_v_strs = ['-vf']
                    if self.cmb_fade_pos.get_active()  ==  0:
                        fade_a_strs.append(cmd_fa_b)
                        fade_v_strs.append(cmd_fv_b)
                    elif self.cmb_fade_pos.get_active() == 1:
                        fade_a_strs.append(cmd_fa_e)
                        fade_v_strs.append(cmd_fv_e)
                    elif self.cmb_fade_pos.get_active() == 2:
                        fade_a_strs.append(cmd_fa_a)
                        fade_v_strs.append(cmd_fv_a)
                    cmd.extend(fade_a_strs)
                    cmd.extend(fade_v_strs)


        # Video opts
        if media_type == 'video':
            # Extract video only
            if self.cb_video_only.get_active():
                cmd.append('-an')
            
            # Video bitrate
            if self.c_vbitrate.is_not_default():
                cmd.extend(['-b:v', self.c_vbitrate.get_text()])
            # Video FPS
            if self.c_vfps.is_not_default():
                cmd.extend(['-r', self.c_vfps.get_text()])
            # Video codec
            if self.c_vcodec.is_not_default():
                cmd.extend(['-vcodec', self.c_vcodec.get_text()])
            
            # Video aspect ratio    
            if self.c_vratio.get_text() == 'default':
                # -- force aspect ratio
                if self.c_vcodec.get_text() in ['libxvid', 'mpeg4', 'h263']:
                    cmd.extend(['-aspect', self.get_aspect_ratio(input_file)])
            else:
                cmd.extend(['-aspect', self.c_vratio.get_text()])
            
            
            #--- Apply filters crop/pad/resize
            filters = []
            # Crop
            if self.crop.get_active():
                filters.append(self.crop.get_crop())
            
            # Pad
            if self.pad.get_active():
                filters.append(self.pad.get_pad())
            
            # Resize video
            if self.c_vsize.is_not_default():
                filters.append('scale={}'.format(self.c_vsize.get_text()))
            
            # TODO: add more subtitle support.
            # Subtitle
            if self.cb_sub.get_active():
                filters.append('subtitles=filename={}:charenc={}'.format(self.entry_sub.get_text(),
                                                                          self.cmb_encoding.get_active_text()
                                                                        ))
                # filters.append('charenc={}'.format(self.cmb_encoding.get_active_text()))
            
            if filters:
                cmd.append('-vf')
                cmd.append(','.join(filters))
            
        
        # Audio
        if media_type in ['audio', 'video', 'ogg', 'ogv']:
            # Audio bitrate
            if self.c_abitrate.is_not_default():
                cmd.extend(['-b:a', self.c_abitrate.get_text()])
            # Audio Freq.
            if self.c_afreq.is_not_default():
                cmd.extend(['-ar', self.c_afreq.get_text()])
            # Audio channel
            if self.c_ach.is_not_default():
                cmd.extend(['-ac', self.c_ach.get_text()])
            
            # Audio codec
            if self.c_acodec.is_not_default():
                cmd.extend(['-acodec', self.c_acodec.get_text()])
                #
                if self.c_acodec.get_text() == 'aac':
                    cmd.extend(['-strict', '-2'])

        # Ogg format
        if media_type in ['ogg', 'ogv']:
            cmd.extend(['-aq', str(self.a_scale.get_value())])
        
        # ogv format
        if media_type == 'ogv':
            cmd.extend(['-qscale', str(self.v_scale.get_value())])
            
        # Copy mode format (useful for splitting)
        if media_type == 'copy':
            cmd.extend(['-acodec', 'copy'])
            cmd.extend(['-vcodec', 'copy'])
        
        # Convert all audio tracks
        if self.cb_all_tracks.get_active():
            cmd.extend(['-map', '0:v', '-map', '0:a'])
        
        #--- Extra options (add other specific options if exist)
        if self.e_extra.get_text().strip() != '':
            cmd.extend(self.e_extra.get_text().split())
        

        # Presets formats
        if media_type == 'presets':
            cmd.extend(self.presets_cmd)
        
        # Split file by time
        if start_pos != '-1' and part_dura != '-1':
            if not self.cb_end.get_active():
                cmd.extend(['-t', part_dura])
        
        # Volume (gain)
        if self.vol_scale.get_value() != 100:
            cmd.extend(['-vol', self.per_to_vol(self.vol_scale.get_value())])
        
        # 2-pass (avconv)
        if self.pass_nbr == 1:
            cmd.append('-an')  # disable audio
            cmd.extend(['-pass', '1'])
            cmd.extend(['-passlogfile', PASS_LOG])
        elif self.pass_nbr == 2:
            cmd.extend(['-pass', '2'])
            cmd.extend(['-passlogfile', PASS_LOG])
        
        #--- Last
        cmd.append(out_file)
        print(' '.join(cmd))       
        return cmd

    #--- Convert funtcion
    def on_convert_cb(self, widget):
        if len(self.store) == 0 or self.is_converting:
            return
        
        # Invalid path
        if not isdir(self.e_dest.get_text()):
            self.info_bar.show_message(_('Destination path is not valid.'))
            self.btn_opts.set_active(True)
            self.set_focus(self.e_dest)
            self.note.set_current_page(6)
            return
        # Inaccessible path
        if not os.access(self.e_dest.get_text(), os.W_OK):
            self.info_bar.show_message(_('Destination path is not accessible.'))
            self.btn_opts.set_active(True)
            self.set_focus(self.e_dest)
            self.note.set_current_page(6)
            return
        
        # Merging
        if self.task_type == TASK_MERGE:
            self.merge_files()
            return
        
        # Invalid audio and video codecs
        codec_txts = []
        
        acodec = self.c_acodec.get_active_text()
        if not check_codec(self.encoder, acodec):
            codec_txts = [_('"{}" audio codec not found.').format(acodec)]
         
        vcodec = self.c_vcodec.get_active_text()
        if not check_codec(self.encoder, vcodec):
            codec_txts.append(_('"{}" video codec not found.').format(vcodec))
         
        if codec_txts:
            self.info_bar.show_message('\n'.join(codec_txts))
            return
        
        # Show files list
        self.btn_opts.set_active(False)
        
        self.tree_iter = self.store.get_iter_first()
        self.is_converting = True
        self.pass_nbr = int(self.cb_2pass.get_active())
        
        # Delete last error log
        self.force_delete_file(ERR_LOG_FILE)
        self.errs_nbr = 0
        
        self._start_time = time.time()
        GObject.timeout_add(100, self._on_elapsed_timer)
        
        self.btn_sw.set_sensitive(False)
        self.btn_convert.set_sensitive(False)
        
        self.convert_file()
        

    def convert_file(self):
        
        #--- Check
        if self.tree_iter != None:
            #--- Do not convert this file (unchecked file)
            if self.store[self.tree_iter][C_SKIP] == False:
                self.store[self.tree_iter][C_STAT] = _("Skipped!")
                # Jump to next file
                self.tree_iter = self.store.iter_next(self.tree_iter)
                if self.tree_iter == None:
                    self.btn_convert.set_sensitive(True)
                    self.btn_sw.set_sensitive(True)
                self.convert_file()
                return
                     
            #--- Get input file
            input_file = self.store[self.tree_iter][C_FILE]
            # When input file not found
            if not isfile(input_file):
                self.store[self.tree_iter][C_STAT] = _("Not found!")
                self.tree_iter = self.store.iter_next(self.tree_iter)
                self.convert_file()
                return    
            
            #----------------------------
            output_format = self.btn_formats.get_label()
            f_type = self.f_file.get(output_format, 'type')
            ext = self.f_file.get(output_format, 'ext')

            if f_type == 'copy':
                ext = splitext(basename(input_file))[1][1:]

            part = splitext(basename(input_file))[0] + '.' + ext
            
            # Same destination as source file
            if self.cb_dest.get_active():
                out_file = join(dirname(input_file), part)
            # Use entry destination path
            else:
                out_file = join(self.e_dest.get_text(), part)
            
            #--- If output file already exist
            if exists(out_file):
                # Overwrite it.
                if self.cmb_exist.get_active() == 0:
                    #--- Rename output file if has the same name as input file
                    if input_file == out_file:
                        out_file = '{}~.{}'.format(splitext(out_file)[0], ext)
                    self.force_delete_file(out_file)
                # Choose another name.
                elif self.cmb_exist.get_active() == 1:
                    out_file = self.new_name(out_file)
                # Skip conversion.
                elif self.cmb_exist.get_active() == 2:
                    self.store[self.tree_iter][C_STAT] = _('Skipped!')
                    self.tree_iter = self.store.iter_next(self.tree_iter)
                    self.convert_file()
                    return
            
            self.out_file = out_file
        
            # Encoding in /tmp "temporary folder" in 1st pass
            if self.pass_nbr == 1:
                out_file = PASS_1_FILE
            
            #---
            if self.cb_split.get_active():
                full_cmd = \
                self.build_cmd(input_file, out_file,
                               self.tl_begin.get_time_str(),
                               self.tl_duration.get_time_str())
            else:
                full_cmd = self.build_cmd(input_file, out_file)
            
            #--- Total file duration
            self.total_duration = self.get_duration(input_file)
            
            #---  To be converted duration
            if self.cb_split.get_active():
                # to the end.
                if self.cb_end.get_active():
                    self.total_duration = self.total_duration - self.tl_begin.get_duration()
                else:
                    self.total_duration = self.tl_duration.get_duration()
            
            # Stored start time
            self.begin_time = time.time()
            
            #--- deactivated controls
            self.enable_controls(False)
            
            #--- Start the process
            try:
                self.fp_conv = Popen(full_cmd, stdout=PIPE, stderr=PIPE,
                                universal_newlines=True, bufsize=-1)
            except:
                self.info_bar.show_message(_('Encoder not found (ffmpeg/avconv).'))
                self.is_converting = False
                self.enable_controls(True)
                return -1
            
            #--- Watch stdout and stderr
#             GLib.io_add_watch(self.fp_conv.stdout,
#                               GLib.IO_IN | GLib.IO_HUP,
#                               self.on_convert_output, out_file)
            GLib.io_add_watch(self.fp_conv.stderr,
                              GLib.IO_IN | GLib.IO_HUP,
                              self.on_convert_output, out_file)
            #--- On end process
            GLib.child_watch_add(self.fp_conv.pid, self.on_convert_end, (out_file, full_cmd))
            
        else:
            self.is_converting = False
            if self.errs_nbr > 0:
                dia = LogDialog(self, ERR_LOG_FILE)
                dia.show_dialog()
    
    
    #--- Stop conversion cb
    def on_btn_stop_clicked(self, *args):
        #TODO: enhance stop function
        # stop conversion task
        if self.task_type == TASK_CONVERT:
            if self.is_converting == True:
                resp = show_message(self,
                                    _('Do you want to stop conversion process?'),
                                    Gtk.MessageType.QUESTION,
                                    Gtk.ButtonsType.YES_NO)
                if resp == Gtk.ResponseType.YES and self.is_converting == True:
                    try:
                        if self.fp_conv:
                            self.fp_conv.kill()
                    except OSError as err:
                        print(err)
                    finally:
                        self.is_converting = False
                        self.enable_controls(True)
                        self.label_details.set_text('')
                        self.btn_opts.set_active(False)
                    return True
        # stop merging task
        elif self.task_type == TASK_MERGE:
            try: self.fp_mrg.kill()
            except: pass
        
                    
    
    def new_name(self, filename):
        """Return new filename like path/output~n.ext (n = 0,1 ...)"""
        part = splitext(filename)
        num = 1
        new_name = '{}~{}'.format(part[0], part[1])
        while exists(new_name):
            new_name = '{}~{}{}'.format(part[0], str(num), part[1])
            num += 1
        return new_name
    
    def get_duration(self, input_file):
        ''' Get duration file in seconds (float)'''
        duration = 0.0
        cmd = [self.encoder, '-i', input_file]
        try:
            proc = Popen(cmd, stdout=PIPE, stderr=PIPE)
            out_str = proc.stderr.read().decode(errors='replace')
        except: pass
                
        try:
            time_list = self.reg_duration.findall(out_str)[0].split(':')
        except:
            return duration
        duration = int(time_list[0]) * 3600 + int(time_list[1]) * 60 + float(time_list[2])
        return duration
    
    def get_time(self, input_file):
        ''' Get time duration file 0:00:00'''
        cmd = '{} -i "{}"'.format(self.encoder, input_file)
        proc = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
        out_str = proc.stderr.read().decode(errors='replace')
        try:
            return self.reg_duration.findall(out_str)[0]
        except:
            return '0:00:00.00'
    
    
    #---- Select subtitle
    def b_enc_cb(self, widget):
        dlg = Gtk.FileChooserDialog(_('Select subtitle'),
                                    self,
                                    Gtk.FileChooserAction.OPEN,
                                    (_('_Add'), Gtk.ResponseType.OK,
                                     _('_Cancel'), Gtk.ResponseType.CANCEL)
                                     )
        dlg.set_current_folder(self.curr_open_folder)
        Filter = Gtk.FileFilter()
        Filter.set_name(_("Subtitle files"))
        Filter.add_pattern("*.[Ss][Rr][Tt]*")
        Filter.add_pattern("*.[Ss][Uu][Bb]*")
        Filter.add_pattern("*.[Aa][Ss][Ss]*")
        Filter.add_pattern("*.[Ss][Ss][Aa]*")
        Filter.add_pattern("*.[Mm][Kk][Vv]*")
        dlg.add_filter(Filter)
        
        Filter = Gtk.FileFilter()
        Filter.set_name(_("All files"))
        Filter.add_pattern("*")
        dlg.add_filter(Filter)
        
        res = dlg.run()
        if res == Gtk.ResponseType.OK:
            self.entry_sub.set_text(dlg.get_filename())
        dlg.destroy()
    
    #--- Remove item
    def on_remove_cb(self, *args):
        iters = self.get_selected_iters()
        if not iters:
            return      
        elif self.is_converting:
            for Iter in iters:
                if self.store[Iter][:] != self.store[self.tree_iter][:]:
                    self.store.remove(Iter)
        else:
            for i in iters: self.store.remove(i)

    def get_selected_iter(self):
        '''Return first selected iter'''
        model, tree_path = self.tree_sel.get_selected_rows()
        # count_selected_rows() only for gtk3 >> 3.4
        if not self.tree_sel.count_selected_rows():
            return None
        return model.get_iter(tree_path)
    
    def get_selected_iters(self):
        ''' Get a list contain selected iters '''
        iters = []
        model, tree_path = self.tree.get_selection().get_selected_rows()
        if not tree_path:
            return iters
        for path in tree_path:
            iters.append(model.get_iter(path))
        return iters
    
    def on_play_cb(self, *args):
        if self.get_selected_iters():
            Iter = self.get_selected_iters()[0]
            
            # Kill previous process.
            if self.play_process != None:
                if self.play_process.poll() == None:
                    self.play_process.kill()
            
            cmd = [self.player, '{}'.format(self.store[Iter][C_FILE])]
            self.play_process = Popen(cmd, universal_newlines=True, bufsize=-1)

    def on_browse_src_cb(self, widget):
        sel_iter = self.get_selected_iters()[0]
        call(['xdg-open', dirname(self.store[sel_iter][C_FILE])])
    
    def on_browse_dest_cb(self, widget):
        if self.cb_dest.get_active():
            Iter = self.get_selected_iters()[0]
            call(['xdg-open', dirname(self.store[Iter][C_FILE])])
        else:
            call(['xdg-open', self.e_dest.get_text()])
            
    def on_preview_cb(self, widget):
        if self.is_converting:
            return
        
        self.is_preview = True
        
        Iter = self.get_selected_iters()[0]
        input_file = self.store[Iter][C_FILE]
        duration = self.get_duration(input_file)
        preview_begin = str(duration / 10)
        
        cmd = self.build_cmd(input_file, PREVIEW_FILE,
                                    preview_begin, TEN_SECONDS)
    
        try:
            fp_prev = Popen(cmd, stdout=PIPE, stderr=PIPE)
        except: return -1
        
        # Disable main window
        self.get_child().set_sensitive(False)
        
        # Wait...
        while fp_prev.poll() == None:
            while Gtk.events_pending():
                Gtk.main_iteration()
            # Cancel preview
            if not self.is_preview:
                self.get_child().set_sensitive(True)
                self.force_delete_file(PREVIEW_FILE)
                return
            self.store[Iter][C_PULS] = self.store[Iter][C_PULS] + 1
            self.store[Iter][C_STAT] = _('Wait...')
            time.sleep(0.05)
            
        # Update information.
        self.store[Iter][C_PRGR] = 0.0
        self.store[Iter][C_STAT] = _('Ready!')
        self.store[Iter][C_PULS] = -1
        
        # Play preview file.
        fp_play = Popen('{} "{}"'.format(self.player, PREVIEW_FILE), shell=True)
        
        # Delete preview file after the end of playing
        while fp_play.poll() == None:
            pass
        self.force_delete_file(PREVIEW_FILE)
        
        # Enable main window
        self.get_child().set_sensitive(True)
    

    #--- Clear list    
    def on_clear_cb(self, widget):
        if not self.is_converting:
            self.tree.set_model(None)
            self.store.clear()
            self.tree.set_model(self.store)
        
    def on_btn_about_clicked(self, *widget):
        a_dgl = About(self)
        a_dgl.show()
        
    def cb_sub_toggled(self, cb_sub):
        self.vb_sub.set_sensitive(cb_sub.get_active())
    
    # Keyboard events.
    def on_tree_key_released(self, widget, event):
        
        # Delete file with "Delete" key
        if event.keyval == Gdk.KEY_Delete:
            self.on_remove_cb()
        
        # Play file with "Return" key
        elif event.keyval == Gdk.KEY_Return:
            self.on_play_cb()
            
    # Mouse events
    def on_tree_button_pressed(self, tree_view, event):
        # There is no file
        if len(self.store) == 0:        
            treepath = self.tree.get_selection().get_selected_rows()[1]
            if len(treepath) == 0:
                return
        
        # Show popup menu with right click
        if event.button == 3:
            self.popup.show_all()
            self.popup.popup(None, None, None, None, 3,
                             Gtk.get_current_event_time())
        # Play with double click
        elif event.button == 1 and event.get_click_count()[1] == 2:
            self.on_play_cb()        
    
    
    #---- On end conversion
    def on_convert_end(self, pid, err_code, opts):
        (out_file, cmd) = opts
        if self.tree_iter != None:
            # Converion succeed
            if err_code == 0:
                # 2pass
                if self.pass_nbr == 1:
                    self.pass_nbr = 2
                    # Remove temoprary file
                    self.force_delete_file(PASS_1_FILE)
                    self.convert_file()
                    return
                elif self.pass_nbr == 2:
                    self.pass_nbr = 1
                
                self.store[self.tree_iter][C_SKIP] = False
                self.store[self.tree_iter][C_PRGR] = 100.0
                self.store[self.tree_iter][C_STAT] = _("Done!")
                self.store[self.tree_iter][C_PULS] = -1
                
                # Remove source file
                if self.cb_remove.get_active():
                    self.force_delete_file(self.store[self.tree_iter][C_FILE])
                elif self.cb_rename.get_active():
                    self.rename_file(self.store[self.tree_iter][C_FILE])
                
                # Update start time
                self._start_time = time.time()
                
                # Convert the next file
                self.tree_iter = self.store.iter_next(self.tree_iter)
                self.convert_file()
            
            # Converion failed
            elif err_code == 256:
                self.store[self.tree_iter][C_STAT] = _("Failed!")
                self.force_delete_file(out_file)
                
                # Write erros log
                self.write_log(cmd)
                self.errs_nbr += 1
                
                # Convert the next file
                self.tree_iter = self.store.iter_next(self.tree_iter)
                self.convert_file()
            
            # Conversion stopped
            elif err_code == 9:
                if self.is_converting == False:
                    self.btn_convert.set_sensitive(True)
                    self.btn_sw.set_sensitive(True)
                # Remove uncompleted file
                self.force_delete_file(out_file)
                return
                    
        else:
            self.is_converting = False
            
        if self.tree_iter == None:
            self.enable_controls(True)
            self.label_details.set_text('')
            self.btn_convert.set_sensitive(True)
            self.btn_sw.set_sensitive(True)
            # Play sound
            if self.cb_play.get_active() and err_code==0:
                self.play_sound(SOUND_FILE)
            # Shutdown system
            if self.cb_halt.get_active():
                self.shutdown()
            # Suspend system
            if self.cb_suspend.get_active():
                self.suspend()
        
    
        
    
    #--- Catch output 
    def on_convert_output(self, source, cond, out_file):
        #TODO: Fix empty err log file in some cases
        #--- Allow interaction with application widgets.
        self.log = source
        
        if self.tree_iter == None:
            return False
        
        #--- Skipped file during conversion (unckecked file during conversion)
        if self.store[self.tree_iter][C_SKIP] == False:
            self.store[self.tree_iter][C_STAT] = _("Skipped!")
            self.store[self.tree_iter][C_PRGR] = 0.0
            
            # Stop conversion
            try: self.fp_conv.kill()
            except OSError as detail:
                print(detail)
            
            # Delete the file
            self.force_delete_file(out_file)
            
            # Update start time
            self._start_time = time.time()
            
            # Jump to next file
            self.tree_iter = self.store.iter_next(self.tree_iter)
            self.convert_file()
            return False
        
        elif cond == GLib.IO_IN:
            line = '0'
            try:
                #FIXME: problem of empty log is here.
                line = self.log.readline()
            except Exception as e:
                print(e)
            
            # ffmpeg progress
            begin = line.find('time=')
            if begin != -1:
                self.label_details.set_text(line.strip())
                reg_avconv = self.reg_avconv_u
                
                # on ubuntu ... time like: time=00.00
                if reg_avconv.findall(line) != []:
                    elapsed_time = float(reg_avconv.findall(line)[0][1])
                
                # on fedora ... time like this 'time=00:00:00.00'
                else:
                    reg_avconv = self.reg_avconv_f
                    elapsed_time = reg_avconv.findall(line)[0][1]
                    elapsed_time = time_to_duration(elapsed_time)

                try:
                    time_ratio = elapsed_time / self.total_duration
                except ZeroDivisionError:
                    time_ratio = 0
                
                if time_ratio > 1: time_ratio = 1
                
                # Get estimated size
                curr_size = float(reg_avconv.findall(line)[0][0])
                try:
                    est_size = int((curr_size * self.total_duration) / elapsed_time)
                except ZeroDivisionError: 
                    est_size = 0
                
                # Waiting (pluse progressbar)
                if est_size == 0:
                    self.store[self.tree_iter][C_PULS] = self.store[self.tree_iter][C_PULS] + 1
                    self.store[self.tree_iter][C_STAT] = _('Wait...')
                else:
                    # Formating estimated size
                    size_str = get_format_size(est_size)
                    
                    # Calculate remaining time.
                    cur_time = time.time() - self.begin_time
                    try:
                        rem_dur = ((cur_time * self.total_duration) / elapsed_time) - cur_time
                    except ZeroDivisionError:
                        rem_dur = 0
                    
                    # Convert duration (sec) to time (0:00:00)
                    rem_time = duration_to_time(rem_dur)
                    self.store[self.tree_iter][C_ESIZE] = size_str
                    self.store[self.tree_iter][C_ELAPT] = self.elapsed_time
                    self.store[self.tree_iter][C_REMN] = rem_time
                    self.store[self.tree_iter][C_PRGR] = float(time_ratio * 100) 
                    if self.pass_nbr != 0:
                        self.store[self.tree_iter][C_STAT] = '{:.2%} (P{})'\
                        .format(time_ratio, self.pass_nbr)  # progress text
                    else:
                        self.store[self.tree_iter][C_STAT] = '{:.2%}'\
                        .format(time_ratio)  # progress text
                    self.store[self.tree_iter][C_PULS] = -1  # progress pusle
                
            #--- Continue read output
            return True
        # When len(line) == 0
        return False

    
    #--- Drag and drop callback
    def drop_data_cb(self, widget, dc, x, y, selection_data, info, t):
        drag_folder = self.add_files(*selection_data.get_uris())
        # Save directory from dragged filename.
        self.curr_open_folder = dirname(drag_folder)
    
    def on_cb_dest_toggled(self, widget):
        Active = not widget.get_active()
        self.e_dest.set_sensitive(Active)
        self.b_dest.set_sensitive(Active)
    
    def cmb_encoder_cb(self, combo):
        self.encoder = combo.get_active_text()
        self.on_codec_changed()
    
    def on_cb_video_only_toggled(self, cb):
        self.vb_audio.set_sensitive(not cb.get_active())
    
    def force_delete_file(self, file_name):
        ''' Force delete file_name '''
        while exists(file_name):
            try:
                os.unlink(file_name)
            except OSError:
                continue
    
    def rename_file(self, file_name):
        ''' Rename file_name '''
        while exists(file_name):
            try:
                path = os.path.dirname(os.path.realpath(file_name))
                base = os.path.basename(os.path.realpath(file_name))
                os.rename(join(path, file_name), join(path, "DONE " + base))
            except OSError:
                continue
    
    def per_to_vol(self, percent):
        # 100 --> 256, 200 --> 512, 300 --> 768 ...
        return '{}'.format((256 * int(percent)) / 100)

    def get_aspect_ratio(self, input_file):
        ''' extract adpect ratio from file if exist, otherwise use 4:3 
        (fix a problem) '''
        cmd = '{} -i {}'.format(self.encoder, input_file)
        proc = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
        out_str = proc.stderr.read().decode(errors='replace')
        try:
            reg_aspect = re.compile('''DAR\s+(\d*:\d*)''')
            return reg_aspect.findall(out_str)[0]
        except:
            return '4:3'
    
    def enable_controls(self, sens=True, merging=False):
        self.btn_formats.set_sensitive(sens)
        self.mb_fav.set_sensitive(sens)
        self.e_dest.set_sensitive(sens)
        self.b_dest.set_sensitive(sens)
        self.cb_dest.set_sensitive(sens)
        self.btn_fav.set_sensitive(sens)
        
        self.vb_audio.set_sensitive(sens)
        self.vb_video.set_sensitive(sens)
        self.vb_sub.set_sensitive(sens)
        self.vb_more.set_sensitive(sens)
        self.crop.set_sensitive(sens)
        self.pad.set_sensitive(sens)
        
        if merging:
            self.btn_add_file.set_sensitive(sens)
            self.btn_add_folder.set_sensitive(sens)
            self.btn_clear.set_sensitive(sens)
            self.btn_remove.set_sensitive(sens)
            self.btn_opts.set_sensitive(sens)
            self.btn_info.set_sensitive(sens)
    
    def save_states(self):
        conf = GLib.KeyFile()
        conf.load_from_file(CONF_FILE, GLib.KeyFileFlags.NONE)
                
        group = 'configs'
        conf.set_string(group, 'curr_open_folder', self.curr_open_folder)
        conf.set_string(group, 'curr_save_folder', self.curr_save_folder)
        conf.set_string(group, 'e_dest_text', self.e_dest.get_text())
        conf.set_string(group, 'format', self.btn_formats.get_label())
        conf.set_boolean(group, 'is_same_dest', self.cb_dest.get_active())
        conf.set_integer(group, 'overwrite_mode', self.cmb_exist.get_active())
        
        if self.cmb_encoder.get_text():
            conf.set_string(group, 'encoder', self.cmb_encoder.get_active_text())
        
        conf.set_string(group, 'player', self.entry_player.get_text())
        conf.set_string(group, 'font', self.b_font.get_font_name())
        conf.set_string(group, 'encoding', self.cmb_encoding.get_active_id())  #
        conf.set_boolean(group, 'side_bar', self.cb_sideb.get_active())
        conf.set_boolean(group, 'tray', self.cb_tray.get_active())
        conf.set_string(group, 'language', self.cmb_lang.get_active_id())
        
        conf.set_boolean(group, 'video_2pass', self.cb_2pass.get_active())
        conf.set_boolean(group, 'video_video_only', self.cb_video_only.get_active())
        
        # play sound
        conf.set_boolean(group, 'play-sound', self.cb_play.get_active())
        
        # statusbar
        conf.set_boolean(group, 'status-bar', self.cb_status.get_active())
        
        # Size, position and state
        conf.set_integer_list(group, 'position', self.get_position())
        conf.set_boolean(group, 'maximized', self.is_maxi)
        if not self.is_maxi:
            conf.set_integer_list(group, 'size', self.get_size())
        
            
        # Resave file
        conf.save_to_file(CONF_FILE)
        conf.unref()
        
        
    def load_states(self):
        conf = GLib.KeyFile()
        try:
            conf.load_from_file(CONF_FILE, GLib.KeyFileFlags.NONE)
        except:
            conf.unref()
            return
        
        group = 'configs'
        
        try:
            self.curr_open_folder = conf.get_string(group, 'curr_open_folder')
            self.curr_save_folder = conf.get_string(group, 'curr_save_folder')
            self.e_dest.set_text(conf.get_string(group, 'e_dest_text'))
            self.btn_formats.set_label(conf.get_string(group, 'format'))
            self.cb_dest.set_active(conf.get_boolean(group, 'is_same_dest'))
            self.cmb_exist.set_active(conf.get_integer(group, 'overwrite_mode'))
            
            self.cmb_encoder.set_text(conf.get_string(group, 'encoder'))
            self.entry_player.set_text(conf.get_string(group, 'player'))
            self.b_font.set_font(conf.get_string(group, 'font'))
            self.cmb_encoding.set_active_id(conf.get_string(group, 'encoding'))
            self.cb_sideb.set_active(conf.get_boolean(group, 'side_bar'))
            self.cb_tray.set_active(conf.get_boolean(group, 'tray'))
            self.cmb_lang.set_active_id(conf.get_string(group, 'language'))
            
            self.cb_2pass.set_active(conf.get_boolean(group, 'video_2pass'))
            self.cb_video_only.set_active(conf.get_boolean(group, 'video_video_only'))
            
            # play sound
            self.cb_play.set_active(conf.get_boolean(group, 'play-sound'))
            
            # status
            self.cb_status.set_active(conf.get_boolean(group, 'status-bar'))
            
            conf.unref()
            
        except Exception as e:
            conf.unref()
            print(e)
    
    def write_log(self, cmd):
        with open(ERR_LOG_FILE, 'a') as f_log:
            # Command line
            f_log.write('Command line #{}:\n****************\n'\
                        .format(self.errs_nbr + 1))
            f_log.write('{}\n'.format(' '.join(cmd)))
            # Error details
            f_log.write('\nError detail:\n*************\n')
            f_log.write(self.log.read())
            f_log.write('\n\n\n')
    
    def on_cb_tray_toggled(self, cb_tray):
        self.trayico.set_visible(cb_tray.get_active())
    
    def install_locale(self):
        conf = GLib.KeyFile()
        try:
            conf.load_from_file(CONF_FILE, GLib.KeyFileFlags.NONE)
            lang_name = conf.get_string('configs', 'language')
        except: return
        
        
        # System language
        if lang_name == '< System >':
            return
        
        # RTL/LTR direction
        if lang_name == 'العربية':
            self.set_default_direction(Gtk.TextDirection.RTL)
        else:
            self.set_default_direction(Gtk.TextDirection.LTR)
            
        # Set language
        try:
            lang_code = LANGUAGES[lang_name]
            lang = gettext.translation(DOMAIN, LOCALDIR, languages=[lang_code])
            lang.install()
        except: pass
    
    def shutdown(self):
        # Start timer
        GObject.timeout_add(1000, self._on_timer_shutdown)
    
    def _on_timer_shutdown(self):
        self.label_details.set_markup(_('<span foreground="red" weight="bold">System will shutdown after {} sec.</span>').format(self.counter))
        self.counter -= 1
        if self.counter < 0:
            cmd = 'dbus-send --system --print-reply --dest=org.freedesktop.ConsoleKit /org/freedesktop/ConsoleKit/Manager org.freedesktop.ConsoleKit.Manager.Stop'
            call(cmd, shell=True)
            return False
        return True
    
    def suspend(self):
        # Start timer
        GObject.timeout_add(1000, self._on_timer_suspend)
    
    def _on_timer_suspend(self):
        self.label_details.set_markup(_('<span foreground="red" weight="bold">System will suspend after {} sec.</span>').format(self.counter))
        self.counter -= 1
        if self.counter < 0:
            self.label_details.set_text('')
            cmd = 'sync'
            call(cmd, shell=True)
            cmd = 'dbus-send --system --print-reply --dest=org.freedesktop.UPower /org/freedesktop/UPower org.freedesktop.UPower.Suspend'
            call(cmd, shell=True)
            return False
        return True
    
  
    def on_cb_ass_toggled(self, cb_ass):
        active = not cb_ass.get_active()
        self.b_font.set_sensitive(active)
        self.hb_pos.set_sensitive(active)
    
    # Calculate elapsed time
    def _on_elapsed_timer(self):
        if not self.is_converting:
            return False
        self.elapsed_time = duration_to_time(time.time() - self._start_time)
        return True
        
    def get_fav_list(self):
        if not exists(FAV_FILE):
            return []
        with open(FAV_FILE, 'rb') as favfile:
            return pickle.load(favfile)
    
    # Remove element from favorite list
    def remove_from_fav(self, element):
        fav_list = self.get_fav_list()
        if element in fav_list:
            fav_list.remove(element)
        self.save_fav_list(fav_list)
        self.load_submenu()
    
    #
    def cb_end_cb(self, w):
        self.tl_duration.set_sensitive(not w.get_active())
    
    # Copy mode callback 
    def on_cb_copy_mode_toggled(self, w):
        if w.get_active():
            self.last_format = self.btn_formats.get_label()
            self.btn_formats.set_label("Copy Mode")
        else:
            self.btn_formats.set_label(self.last_format)
    
    
    #
    def on_cb_halt_toggled(self, w):
        self.cb_suspend.set_sensitive(not w.get_active())

    #
    def on_cb_suspend_toggled(self, w):
        self.cb_halt.set_sensitive(not w.get_active())
       
    #
    def on_tree_cursor_changed(self, w):
        if not self.cb_sideb.get_active():
            return
        
        while Gtk.events_pending():
            Gtk.main_iteration()
        
        if len(self.store) == 0:
            return
        
        try : Iter = self.get_selected_iters()[0]
        except: return
        
        input_file = self.store[Iter][C_FILE]
        dura = self.store[Iter][C_FDURA]
        
        # Show file information
        self.label_infos.set_markup(_('<b>Duration:</b> {}\n'
                                    '<b>Size:</b> {}\n'
                                    '<b>Extension:</b> {}\n')
                                    .format(dura,
                                            self.store[Iter][C_FSIZE],
                                            splitext(input_file)[1],
                                            ))
        
        # Show image preview (screenshot)
        img_pos = time_to_duration(dura) / 10
        call('{} -y -ss {} -i "{}" -f image2 -frames:v 1 {}'
             .format(self.encoder, img_pos, input_file, IMG_PREV),
             shell=True, stdout=PIPE, stderr=PIPE)
        if exists(IMG_PREV):
            pix = GdkPixbuf.Pixbuf.new_from_file_at_size(IMG_PREV, 175, 130)
            self.image_prev.set_from_pixbuf(pix)
        else:
            self.image_prev.clear()

    
    def on_cb_sideb_toggled(self, w):
        self._child.set_visible(self.cb_sideb.get_active())
        self.hide_item.set_active(self.cb_sideb.get_active())
    
    
    def on_event_cb(self, w, e):
        if e.button == 3:
            self.popup_hide.show_all()
            self.popup_hide.popup(None, None, None, None, 3,
                             Gtk.get_current_event_time())
    
    
    def on_hide_item_activate(self, w):
        self.cb_sideb.set_active(self.hide_item.get_active())
    
    
    # file infos cb
    def on_file_info_cb(self, widget):
        
        try: Iter = self.get_selected_iters()[0]
        except:
            widget.set_active(False)
            return
        if not which('mediainfo'):
            self.info_bar.show_message(_('Please install "mediainfo" package.'))
            widget.set_active(False)
            return
        
        # Show info
        is_active = not widget.get_active()
        if widget.get_active():
            self.stack.set_visible_child_name(CHILD_INFOS)
            input_file = self.store[Iter][C_FILE]
            buf = check_output('mediainfo "{}"'.format(input_file), shell=True, universal_newlines=True)
            self.txt_buffer_info.set_text(buf)
        else:
            self.stack.set_visible_child_name(CHILD_FILES)
        
        self.txt_info.set_visible(not is_active)
        self.btn_add_file.set_sensitive(is_active)
        self.btn_add_folder.set_sensitive(is_active)
        self.btn_remove.set_sensitive(is_active)
        self.btn_clear.set_sensitive(is_active)
        self.btn_convert.set_sensitive(is_active)
        self.btn_opts.set_sensitive(is_active)
    
    def on_cb_status_toggled(self, widget):
        is_active = widget.get_active()
        self.label_details.set_visible(is_active)        
        
    
    def restore_last_position(self):
        conf = GLib.KeyFile()
        try:
            conf.load_from_file(CONF_FILE, GLib.KeyFileFlags.NONE)
        except:
            conf.unref()
            return
        
        group = 'configs'
        try:
            if (conf.get_boolean(group, 'maximized')):
                self.maximize()
            else:
                x, y = conf.get_integer_list(group, 'position')
                w, h = conf.get_integer_list(group, 'size')
                self.resize(w, h)
                self.move(x, y)
        except Exception as e:
            print(e)
        finally:
            conf.unref()
    
    
    # Return formats.cfg full path
    def get_formats_file_name(self):
        if not exists(USR_FFILE):
            copyfile(ORG_FFILE, USR_FFILE)
        
        if not exists(CONF_FILE):
            conf = GLib.KeyFile()
            conf.set_string('configs', 'formats_file', USR_FFILE)
            conf.save_to_file(CONF_FILE)
            conf.unref()
        
        return USR_FFILE
    
    def get_str_from_conf(self, conf_file, section, key):
        conf = GLib.KeyFile()
        if not exists(conf_file):
            conf.set_string(section, key, join(CONF_PATH, 'formats.cfg'))
            conf.save_to_file(conf_file)
            return
        
        conf.load_from_file(join(conf_file), GLib.KeyFileFlags.NONE)
        value = conf.get_string(section, key)
        conf.unref()
        return value
    
    #
    def build_treeview_popup(self):
        
        popup = Gtk.Menu()
        
        play_item = Gtk.MenuItem.new_with_label(_('Play'))
        play_item.connect('activate', self.on_play_cb)
        
        preview_item = Gtk.MenuItem.new_with_mnemonic(_('_Preview'))
        preview_item.connect('activate', self.on_preview_cb)
        
        remove_item = Gtk.MenuItem.new_with_label(_('Remove'))
        remove_item.connect('activate', self.on_remove_cb)
        
        browse_src = Gtk.MenuItem.new_with_label(_('Browse source'))
        browse_src.connect('activate', self.on_browse_src_cb)
        
        browse_item = Gtk.MenuItem.new_with_label(_('Browse destination'))
        browse_item.connect('activate', self.on_browse_dest_cb)
        
        popup.append(play_item)
        popup.append(preview_item)
        popup.append(remove_item)
        popup.append(Gtk.SeparatorMenuItem.new())
        popup.append(browse_src)
        popup.append(browse_item)
        
        return popup
    
    def on_opts_toggled(self, toggle):
        is_active = not toggle.get_active()
        # Show options
        if toggle.get_active():
            self.stack.set_visible_child_name(CHILD_ADVANCED)
        # Show files list
        else:
            self.stack.set_visible_child_name(CHILD_FILES)
        
        self.btn_add_file.set_sensitive(is_active)
        self.btn_add_folder.set_sensitive(is_active)
        self.btn_remove.set_sensitive(is_active)
        self.btn_clear.set_sensitive(is_active)
        self.btn_info.set_sensitive(is_active)
    
    def browse_for_encoder(self, btn):
        open_dlg = Gtk.FileChooserDialog(_("Choose Encoder"),
                                        self, Gtk.FileChooserAction.OPEN,
                                        (_('_OK'),
                                        Gtk.ResponseType.OK,
                                        _('_Cancel'),
                                        Gtk.ResponseType.CANCEL))
        open_dlg.set_current_folder(HOME)
        open_dlg.set_icon_name('curlew')

        res = open_dlg.run()
        if res == Gtk.ResponseType.OK:
            file_name = open_dlg.get_filename()
            if not self.cmb_encoder.find_text(file_name):
                self.cmb_encoder.append_text(file_name)
                self.cmb_encoder.set_text(file_name)
        #
        open_dlg.destroy()
    
    
    def merge_files_cb(self, widget, a):
        self.btn_convert.set_label(_('Merge'))
        self.btn_convert.set_tooltip_text(_('Start Merging'))
        self.task_type = TASK_MERGE
    
    def convert_files_cb(self, widget, a):
        self.btn_convert.set_label(_('Convert'))
        self.btn_convert.set_tooltip_text(_('Start Conversion'))
        self.task_type = TASK_CONVERT
        
    def make_gif_cb(self, widget, a):
        self.btn_convert.set_label(_('Make GIF'))
        self.btn_convert.set_tooltip_text(_('Make GIF file'))
        self.task_type = TASK_GIF
    
    
    #--- Merge function
    def merge_files(self):
        if self.is_merging:
            return
        files_to_merge = ''
        input_file = ''
        # self.total_files_size: size of files to be merged
        self.total_files_size = 0
        for line in self.store:
            input_file = line[10]
            self.total_files_size += getsize(input_file)
            files_to_merge += "file '{}'\n".format(input_file)

        tmp_file = '/tmp/to_be_merged.txt'
        with open(tmp_file, 'w') as log:
            log.write(files_to_merge)
        
        # Output file
        ext = splitext(input_file)[1]
        part = self.entry_merged_file.get_text() + ext
        
        # Same destination as source file
        if self.cb_dest.get_active():
            self.out_file = join(dirname(input_file), part)
        # Use entry destination path
        else:
            self.out_file = join(self.e_dest.get_text(), part)
        
        
        cmd = [self.encoder, '-y', '-hide_banner', '-f', 'concat', '-safe', '0',
               '-i', tmp_file, '-c', 'copy', self.out_file]
        self.fp_mrg = Popen(cmd, shell=False, stdout=PIPE, stderr=PIPE, 
                            universal_newlines=True)
        
        GLib.io_add_watch(self.fp_mrg.stderr, GLib.IO_IN | GLib.IO_HUP,
                          self.on_mrg_output)
        GLib.child_watch_add(self.fp_mrg.pid, self.on_mrg_end)
        
        
        self.btn_sw.set_sensitive(False)
        self.btn_convert.set_sensitive(False)
        self.enable_controls(False, True)
        
        self.stack.set_visible_child_name(CHILD_MERGE)
        self.lbl_merge_status.set_markup(_('<i>Merging files, please wait...</i>'))
        self.lbl_merge_details.set_markup(_('<i>Percent: 0 %</i>'))
        self.pb_merge.set_fraction(0.0)
        
    def on_mrg_output(self, src, cond):
        #self.mrg_err_file = src
        
        Gtk.main_iteration()
        
        # On Data read
        if cond == GLib.IO_IN:
            try:
                out_file_size = getsize(self.out_file)
            except:
                out_file_size = 0
            frac = out_file_size / self.total_files_size
            self.pb_merge.set_fraction(frac)
            
            self.lbl_merge_details.set_markup(_('<i>Percent: {:.0f} %</i>').format(frac*100))
            self.is_merging = True
            return True
        # On error
        elif cond == GLib.IO_HUP:
            return False
        
        return False
    
    def on_mrg_end(self, pid, err_code):
        #
        if err_code == CODE_SUCCESS:
            show_message(self, _('Merging operation completed successfully!'),
                         Gtk.MessageType.INFO, Gtk.ButtonsType.CLOSE)
        #
        elif err_code == CODE_STOPPED:
            self.force_delete_file(self.out_file)
        #
        elif err_code == CODE_FAILED:
            errd = ErrDialog(self, self.fp_mrg.stderr, _('Merge Error'))
            errd.show_dialog()
            self.force_delete_file(self.out_file)
        
        self.stack.set_visible_child_name(CHILD_FILES)
        self.is_merging = False
        self.btn_convert.set_sensitive(True)
        self.btn_sw.set_sensitive(True)
        self.enable_controls(True, True)
            
                


class CurlewApp(Gtk.Application):
    def __init__(self, *args):
        Gtk.Application.__init__(self)
        self.args = args
    
    def do_activate(self):
        win = Curlew(self, *self.args)
        #win.show_all()
        win._child.set_visible(win.cb_sideb.get_active())
    
    def do_startup(self):
        Gtk.Application.do_startup(self)



class DBusService(dbus.service.Object):
    def __init__(self, app, *args):
        self.app = app
        bus_name = dbus.service.BusName('org.curlew', bus=dbus.SessionBus())
        dbus.service.Object.__init__(self, bus_name, '/org/curlew')

    @dbus.service.method(dbus_interface='org.curlew')
    
    def present(self, *args):
        self.app.add_files(*args)
        self.app.present()


def main(*args):
    if dbus.SessionBus().request_name("org.curlew") != \
       dbus.bus.REQUEST_NAME_REPLY_PRIMARY_OWNER:
        print('Curlew is already running')
        '''
        method = dbus.SessionBus().get_object("org.curlew", "/org/curlew").\
        get_dbus_method("present")
        method(*args)
        '''
    else:
        app = CurlewApp(*args)
        app.run()
        DBusService(app)

if __name__ == '__main__':
    main(*sys.argv[1:])


