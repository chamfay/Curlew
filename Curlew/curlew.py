#-*- coding:utf-8 -*-

#===============================================================================
# Application: Curlew multimedia converter
# Author: Fayssal Chamekh <chamfay@gmail.com>
# License: Waqf public license,
# Please see: http://www.ojuba.org/wiki/doku.php/waqf/license for more infos.
#===============================================================================

try:
    import sys
    import os
    import re
    import time
    import gettext
    from subprocess import Popen, PIPE, call
    from os.path import basename, isdir, splitext, join, dirname, realpath, \
    isfile, exists, getsize
    from os import listdir
    from ConfigParser import ConfigParser, NoOptionError
    from urllib import unquote
    from gi.repository import Gtk, GLib, Gdk, GObject
    import dbus.glib, dbus.service
    import cPickle
    
    from customwidgets import LabeledHBox, TimeLayout, CustomHScale, \
    CustomToolButton, SpinsFrame, LabeledGrid, CustomComboEntry
    from about import About
    from functions import show_message, get_format_size, duration_to_time, \
    time_to_duration
    from logdialog import LogDialog
    from tray import StatusIcon
    from languages import LANGUAGES
    from favdialog import Favorite
    
except Exception as detail:
    print(detail)
    sys.exit(1)

#--- Localization setup
exedir = dirname(sys.argv[0])

DOMAIN = 'curlew'
LOCALDIR = ''

# Curlew script (default locale)
if isdir(join(exedir, '..', 'share/locale')):
    LOCALDIR = join(exedir, '..', 'share/locale')

# Curlew script (test)
elif isdir(join(exedir, 'locale')):
    LOCALDIR = join(exedir, 'locale')

# curlew.py
else:
    LOCALDIR = join(exedir, '..', 'locale')
    
gettext.install(DOMAIN, LOCALDIR)


#--- Constants
APP_DIR      = dirname(realpath(__file__))
HOME         = os.getenv("HOME")
TEN_SECONDS  = '10'
CONF_PATH    = join(HOME, '.curlew')
OPTS_FILE    = join(CONF_PATH, 'curlew.cfg')
ERROR_LOG    = join(CONF_PATH, 'errors.log')
PASS_LOG     = '/tmp/pass1log'
PASS_1_FILE  = '/tmp/pass1file'
PREVIEW_FILE = '/tmp/preview'
IMG_PREV     = '/tmp/img_prev.jpeg'
FAV_FILE     = join(CONF_PATH, 'fav.list')


# Make .curlew folder if not exist
if not exists(CONF_PATH): os.mkdir(CONF_PATH)

# Treeview cols nbrs
C_SKIP = 0             # Skip (checkbox)
C_NAME = 1             # File name
C_FSIZE = 2            # File size
C_ESIZE = 3            # Estimated output size
C_ELAPT = 4            # Elapsed time
C_REMN = 5             # Remaining time
C_PRGR = 6             # Progress value
C_STAT = 7             # Stat string
C_PULS = 8             # Pulse
C_FILE = 9             # complete file name /path/file.ext


#--- Main class        
class Curlew(Gtk.Window):    
    
    def __init__(self, *cmd_line_files):
        #--- Global Variables
        self.curr_open_folder = HOME
        self.curr_save_folder = HOME
        self.is_converting = False
        self.fp = None
        self.Iter = None
        self.total_duration = 0.0
        self.out_file = None
        self.counter = 20
        self.errs_nbr = 0
        self.pass_nbr = 0
        '''
        self.pass_nbr = 0: Single pass encoding option
        self.pass_nbr = 1: Two-pass encoding option (1st pass)
        self.pass_nbr = 2: Two-pass encoding option (2nd pass)
        '''
        
        self.encoder = ''
        self.player = 'ffplay'
        self.is_preview = False
        self.dict_icons = {}
        self.icons_path = ''
        
        self._start_time = None
        self.elapsed_time = '0.00.00'
        
        self.last_format = None
        
        #--- Regex
        self.reg_avconv_u = \
        re.compile('''size=\s+(\d+\.*\d*).*time=(\d+\.\d*)''') # ubuntu
        self.reg_avconv_f = \
        re.compile('''size=\s+(\d+\.*\d*).*time=(\d+:\d+:\d+.\d+)''') # fedora
        self.reg_menc = \
        re.compile('''.(\d+\.*\d*)s.*\((.\d+)%.*\s+(\d+)mb''')
        self.reg_duration = \
        re.compile('''Duration:.*(\d+:\d+:\d+\.\d+)''')
        
        # Install Local
        self.install_locale()
               
        Gtk.Window.__init__(self)        
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_title(_('Curlew'))
        self.set_border_width(6)
        self.set_size_request(730, -1)
        self.set_icon_name('curlew')
        
        #--- Global vbox
        vbox = Gtk.Box(spacing=6, orientation=Gtk.Orientation.VERTICAL)
        self.add(vbox)
        
        #--- Toolbar
        toolbar = Gtk.Toolbar()
        toolbar.set_icon_size(Gtk.IconSize.DIALOG)
        vbox.pack_start(toolbar, False, True, 0)
        
        
        #--- ToolButtons
        # Add toolbutton
        self.add_tb = CustomToolButton('add', _('Add'), 
                                       _('Add files'),
                                       self.tb_add_cb, toolbar)
        
        # Remove toolbutton
        self.remove_tb = CustomToolButton('remove', _('Remove'), 
                                          _('Remove files'),
                                          self.tb_remove_cb, toolbar)
        
        # Clear toolbutton
        self.clear_tb = CustomToolButton('clear', _('Clear'), 
                                         _('Clear files list'),
                                         self.tb_clear_cb, toolbar)
        
        # Separator
        toolbar.insert(Gtk.SeparatorToolItem(), -1)
        
        # Convert toolbutton
        self.convert_tb = CustomToolButton('convert', _('Convert'), 
                                           _('Start Conversion'),
                                           self.convert_cb, toolbar)
        
        # Stop toolbutton
        self.stop_tb = CustomToolButton('stop', _('Stop'), 
                                        _('Stop Conversion'),
                                        self.tb_stop_cb, toolbar)
        
        # Separator
        toolbar.insert(Gtk.SeparatorToolItem(), -1)
        
        # About toolbutton
        self.about_tb = CustomToolButton('about', _('About'), 
                                         _('About Curlew'),
                                         self.tb_about_cb, toolbar)
        
        # Separator
        toolbar.insert(Gtk.SeparatorToolItem(), -1)
        
        # Quit toolbutton
        self.quit_tb = CustomToolButton('quit', _('Quit'), 
                                        _('Quit application'),
                                        self.quit_cb, toolbar)
        
        #--- List of files
        self.store = Gtk.ListStore(bool,  # active 
                                   str,   # file_name
                                   str,   # duration
                                   str,   # estimated file_size
                                   str,   # elapsed time
                                   str,   # time remaining
                                   float, # progress
                                   str,   # status (progress txt)
                                   int,   # pulse
                                   str    # complete file_name
                                   )         
        self.tree = Gtk.TreeView(self.store)
        self.tree.set_has_tooltip(True)
        self.tree.set_rubber_banding(True)

        tree_select = self.tree.get_selection()
        tree_select.set_mode(Gtk.SelectionMode.MULTIPLE)
        
        self.tree.connect("button-press-event", self.on_button_press)
        self.tree.connect("key-press-event", self.on_tree_key_press)
        self.tree.connect("cursor-changed", self.on_tree_cursor_changed)
        
        scroll = Gtk.ScrolledWindow()
        scroll.set_size_request(500, 220)
        scroll.set_shadow_type(Gtk.ShadowType.IN)
        scroll.add(self.tree)
        
        self.paned = Gtk.Paned()
        vbox.pack_start(self.paned, True, True, 0)
        
        #--- Image preview
        vbox_image = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        vbox_image.set_border_width(4)
        
        frame = Gtk.Frame()
        frame.set_shadow_type(Gtk.ShadowType.IN)
        frame.add(vbox_image)
        
        event_box = Gtk.EventBox()
        event_box.add(frame)
        event_box.connect('button-press-event', self.on_event_cb)
        
        self.image_prev  = Gtk.Image()
        self.image_prev.set_padding(4, 4)
        
        # popup
        self.popup_hide = Gtk.Menu()
        self.hide_item = Gtk.CheckMenuItem().new_with_label(_('Show sidebar'))
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
        col = Gtk.TreeViewColumn(None, cell, active=C_SKIP)
        self.tree.append_column(col)
        
        #--- File name cell
        cell = Gtk.CellRendererText()
        col = Gtk.TreeViewColumn(_("File"), cell, text=C_NAME)
        col.set_resizable(True)
        col.set_min_width(150)
        self.tree.append_column(col)
        
        #--- Duration cell
        cell = Gtk.CellRendererText()
        col = Gtk.TreeViewColumn(_("Size"), cell, text=C_FSIZE)
        self.tree.append_column(col)
        
        
        #--- Size cell
        cell = Gtk.CellRendererText()
        col = Gtk.TreeViewColumn(_("Estimated size"), cell, text=C_ESIZE)
        col.set_fixed_width(60)
        self.tree.append_column(col)
        
        #--- Elapsed time cell
        cell = Gtk.CellRendererText()
        col = Gtk.TreeViewColumn(_("Elapsed time"), cell, text=C_ELAPT)
        col.set_fixed_width(60)
        self.tree.append_column(col)
        
        #--- Remaining time cell
        cell = Gtk.CellRendererText()
        col = Gtk.TreeViewColumn(_("Remaining time"), cell, text=C_REMN)
        self.tree.append_column(col)
        
        #--- Progress cell
        cell = Gtk.CellRendererProgress()
        col = Gtk.TreeViewColumn(_("Progress"), cell, 
                                 value=C_PRGR, text=C_STAT, pulse=C_PULS)
        col.set_min_width(100)
        self.tree.append_column(col)
        
        #--- Popup menu (TreeView)
        self.popup = Gtk.Menu()
        remove_item = Gtk.ImageMenuItem().new_from_stock(Gtk.STOCK_REMOVE, None)
        remove_item.set_always_show_image(True)
        remove_item.connect('activate', self.tb_remove_cb)
        
        play_item = Gtk.ImageMenuItem.new_from_stock(Gtk.STOCK_MEDIA_PLAY, None)
        play_item.set_always_show_image(True)
        play_item.connect('activate', self.on_play_cb)
        
        browse_item = Gtk.ImageMenuItem.new_from_stock(Gtk.STOCK_DIRECTORY, None)
        browse_item.set_always_show_image(True)
        browse_item.set_label(_('Browse destination'))
        browse_item.connect('activate', self.on_browse_cb)
        
        preview_item = Gtk.MenuItem(_('Preview before converting'))
        preview_item.connect('activate', self.on_preview_cb)
        
        self.popup.append(play_item)
        self.popup.append(preview_item)
        self.popup.append(remove_item)
        self.popup.append(browse_item)
        
        #--- Output formats
        self.cmb_formats = Gtk.ComboBoxText()
        self.cmb_formats.set_entry_text_column(0)
        self.cmb_formats.set_id_column(0)
        self.cmb_formats.set_has_tooltip(True)
        self.cmb_formats.connect('changed', self.on_cmb_formats_changed)
        self.cmb_formats.connect('query-tooltip', self.on_cmb_formats_tooltip)
        
        hbox = Gtk.Box(spacing=6)
        hl = LabeledGrid(vbox)
        hl.append_row(_("<b>Format:</b>"), hbox, True)
        
        # Favorite button
        self.btn_fav = Gtk.Button()
        self.btn_fav.set_image(Gtk.Image
                               .new_from_icon_name("emblem-favorite", 
                                                   Gtk.IconSize.MENU))
        self.btn_fav.connect('clicked', self.show_menu)
        self.btn_fav.set_tooltip_markup(_("Favorite list"))
        hbox.pack_start(self.cmb_formats, True, True, 0)
        hbox.pack_start(self.btn_fav, False, False, 0)
        
        # Buid Favorite menu
        self.build_fav_menu()        
        
        #--- Destination
        self.e_dest = Gtk.Entry()
        self.e_dest.set_text(HOME)
        self.b_dest = Gtk.Button(' ... ')
        self.b_dest.set_size_request(30, -1)
        self.cb_dest = Gtk.CheckButton(_('Source Path'))
        self.cb_dest.connect('toggled', self.on_cb_dest_toggled)
        self.b_dest.connect('clicked', self.on_dest_clicked)
        
        hbox = Gtk.Box(spacing=6)
        hl.append_row(_('<b>Destination:</b>'), hbox, True)
        
        hbox.pack_start(self.e_dest, True, True, 0)
        hbox.pack_start(self.b_dest, False, True, 0)
        hbox.pack_start(self.cb_dest, False, True, 0)
        
        
        #--- advanced options
        self.exp_advanced = Gtk.Expander(label=_("<b>Advanced</b>"))
        self.exp_advanced.set_use_markup(True)
        self.exp_advanced.set_resize_toplevel(True)
        vbox.pack_start(self.exp_advanced, False, True, 0)
        
        note = Gtk.Notebook()
        self.exp_advanced.add(note)
        
        #--- audio page
        self.vb_audio = Gtk.Box(spacing=4, border_width=5, orientation=Gtk.Orientation.VERTICAL)
        note.append_page(self.vb_audio, Gtk.Label(_("Audio")))
       
        self.c_abitrate = CustomComboEntry()
        self.c_afreq = CustomComboEntry()
        self.c_ach = CustomComboEntry()
        self.c_acodec = CustomComboEntry()
        
        grid_audio = LabeledGrid(self.vb_audio)
        grid_audio.append_row(_("Audio Bitrate"), self.c_abitrate)
        grid_audio.append_row(_("Audio Frequency"), self.c_afreq)
        grid_audio.append_row(_("Audio Channels"), self.c_ach)
        grid_audio.append_row(_("Audio Codec"), self.c_acodec)
        
        # volume
        self.hb_volume = LabeledHBox(_('Volume (%)'), self.vb_audio)
        self.vol_scale = CustomHScale(self.hb_volume, 100, 25, 400, 25)
        
        self.vb_audio.pack_start(Gtk.Separator(), False, False, 0)
        
        # Audio quality for ogg
        self.hb_aqual = LabeledHBox(_('Audio Quality'), self.vb_audio)
        self.a_scale = CustomHScale(self.hb_aqual, 3, 0, 10)
        
        
        #--- video page
        self.vb_video = Gtk.Box(spacing=4, border_width=5, orientation=Gtk.Orientation.VERTICAL)
        note.append_page(self.vb_video, Gtk.Label(_("Video")))
        

        self.c_vbitrate = CustomComboEntry()
        self.c_vfps = CustomComboEntry()
        self.c_vsize = CustomComboEntry()
        self.c_vcodec = CustomComboEntry()
        self.c_vratio = CustomComboEntry()
        
        grid_video = LabeledGrid(self.vb_video)
        grid_video.append_row(_("Video Bitrate"), self.c_vbitrate)
        grid_video.append_row(_("Video FPS"), self.c_vfps)
        grid_video.append_row(_("Video Size"), self.c_vsize)
        grid_video.append_row(_("Video Codec"), self.c_vcodec)
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
        
        self.vb_video.pack_start(Gtk.Separator(), False, False, 0)
        
        # Video quality for ogv
        self.hb_vqual = LabeledHBox(_('Video Quality'), self.vb_video)
        self.v_scale = CustomHScale(self.hb_vqual, 5, 0, 20)
        
        #--- Subtitle page
        self.frame_sub = Gtk.Frame(border_width=5)
        note.append_page(self.frame_sub, Gtk.Label(_("Subtitle")))
        
        self.vb_sub = Gtk.Box(spacing=5, border_width=5, sensitive=False, orientation=Gtk.Orientation.VERTICAL)
        self.frame_sub.add(self.vb_sub)
        
        #--- Sub Active/Desactive
        self.cb_sub = Gtk.CheckButton(_('Use Subtitle'))
        self.frame_sub.set_label_widget(self.cb_sub)
        self.cb_sub.connect('toggled', self.cb_sub_toggled)
        
        grid_sub = LabeledGrid(self.vb_sub)
        
        #--- Subtitle filename
        self.hb_sub = Gtk.Box(spacing=6)
        self.entry_sub = Gtk.Entry()
        self.hb_sub.pack_start(self.entry_sub, True, True, 0)
        
        #---- Select subtitle
        b_enc = Gtk.Button(' ... ')
        b_enc.set_size_request(30, -1)
        self.hb_sub.pack_start(b_enc, False, False, 0)
        b_enc.connect('clicked', self.b_enc_cb)
        grid_sub.append_row(_('Subtitle: '), self.hb_sub, True)
        
        #--- Subtitle font
        self.b_font = Gtk.FontButton()
        self.b_font.set_show_size(False)
        self.b_font.set_show_style(False)
        
        grid_sub.append_row(_('Font: '), self.b_font, True)
        
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
        
        grid_sub.append_row(_('Position: '), self.hb_pos, False)
        
        self.vb_sub.pack_start(hbox, False, False, 0)
        
        
        #--- Subtitle Encoding
        encs = ['cp1250', 'cp1252', 'cp1253', 'cp1254',
               'cp1255', 'cp1256', 'cp1257', 'cp1258',
               'iso-8859-1', 'iso-8859-2', 'iso-8859-3', 'iso-8859-4',
               'iso-8859-5', 'iso-8859-6', 'iso-8859-7', 'iso-8859-8',
               'iso-8859-9', 'iso-8859-10', 'iso-8859-11', 'iso-8859-12',
               'iso-8859-13', 'iso-8859-14', 'iso-8859-15',
               'utf-7', 'utf-8', 'utf-16', 'utf-32', 'ASCII']
        self.cmb_enc = Gtk.ComboBoxText()
        self.cmb_enc.set_entry_text_column(0)
        self.cmb_enc.set_id_column(0)
        for enc in encs:
            self.cmb_enc.append_text(enc)
        self.cmb_enc.set_active(5)
        self.cmb_enc.set_wrap_width(4)
        grid_sub.append_row(_('Encoding: '), self.cmb_enc, True)
        
        # Delay subtitle
        self.hb_delay = Gtk.Box(spacing=6)
        self.sub_delay = Gtk.SpinButton()        
        self.sub_delay.set_adjustment(Gtk.Adjustment(0, -90000, 90000, 1))
        self.hb_delay.pack_start(self.sub_delay, False, True, 0)
        self.hb_delay.pack_start(Gtk.Label(_("sec")), False, False, 0)
        grid_sub.append_row(_('Delay: '), self.hb_delay)
        
        # harddup option
        self.cb_hard = Gtk.CheckButton(_('Harddup'))
        self.vb_sub.pack_start(self.cb_hard, False, False, 0)
        
        # SSA/ASS
        self.cb_ass = Gtk.CheckButton(_('Use SSA/ASS subtitle'))
        self.cb_ass.connect('toggled', self.on_cb_ass_toggled)
        self.vb_sub.pack_start(self.cb_ass, False, False, 0)
        
        
        #--- Crop/Pad page
        self.vb_crop = Gtk.Box(spacing=5, border_width=5, orientation=Gtk.Orientation.VERTICAL)
        note.append_page(self.vb_crop, Gtk.Label(_('Crop / Pad')))
        
        # Cropping video
        self.crop = SpinsFrame(_('Crop'))
        self.vb_crop.pack_start(self.crop, False, False, 0)
        
        # Padding video
        self.pad = SpinsFrame(_('Pad'))
        self.vb_crop.pack_start(self.pad, False, False, 0)
        
        
        #--- "More" page
        self.vb_more = Gtk.Box(spacing=4, border_width=5, orientation=Gtk.Orientation.VERTICAL)
        note.append_page(self.vb_more, Gtk.Label(_("More")))
        
        # Split file
        self.cb_split = Gtk.CheckButton(_('Split File'))
        self.cb_split.connect('toggled', self.cb_split_cb)
        
        self.frame = Gtk.Frame(label_widget = self.cb_split)
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
        self.s_threads = Gtk.SpinButton().new_with_range(0, 10, 1)
        grid_other.append_row(_('Threads:'), self.s_threads)

        #-- Use same quality as source file
        self.cb_same_qual = Gtk.CheckButton(_('Source Quality'))
        self.cb_same_qual.set_tooltip_text(_('Use the same quality as source'
                                             ' file'))
        self.cb_same_qual.connect('toggled', self.on_cb_same_qual_toggled)
        self.vb_more.pack_start(self.cb_same_qual, False, False, 0)
        
        # Encoder type (ffmpeg / avconv)
        self.cmb_encoder = CustomComboEntry(False)
        self.cmb_encoder.set_id_column(0)
        self.cmb_encoder.connect('changed', self.cmb_encoder_cb)
        grid_other.append_row(_('Converter:'), self.cmb_encoder)
        
        # Load available encoder
        if call(['which', 'avconv'], stdout=PIPE) == 0:
            self.cmb_encoder.append_text('avconv')
        if call(['which', 'ffmpeg'], stdout=PIPE) == 0:
            self.cmb_encoder.append_text('ffmpeg')
        self.cmb_encoder.set_active(0)
        
        
        #--- Configuration page
        self.vb_config = Gtk.Box(spacing=4, border_width=5, orientation=Gtk.Orientation.VERTICAL)
        note.append_page(self.vb_config, Gtk.Label(_('Configs')))
        
        grid_config = LabeledGrid(self.vb_config)
        
        # Replace/Skip/Rename
        self.cmb_exist = CustomComboEntry(False)
        self.cmb_exist.set_list([_('Overwrite it'),
                                 _('Choose another name'),
                                 _('Skip conversion')])
        grid_config.append_row(_('File exist:'), self.cmb_exist)
        
        
        #--- Application language
        self.cmb_lang = CustomComboEntry(False)
        self.cmb_lang.set_tooltip_markup(_("Your language will appear after restart Curlew"))
        self.cmb_lang.set_id_column(0)
        # Fill
        self.cmb_lang.set_list(sorted(LANGUAGES.keys()))
        self.cmb_lang.prepend_text('< System >')
        self.cmb_lang.set_active(0)
        
        grid_config.append_row(_('Language:'), self.cmb_lang)
        
        hb_icons = Gtk.Box(spacing=4)
        
        #--- Icons theme
        self.cmb_icons = CustomComboEntry(False)
        self.cmb_icons.connect('changed', self.on_cmb_icons_changed)
        self.cmb_icons.set_id_column(0)
        hb_icons.pack_start(self.cmb_icons, False, False, 0)
        
        #--- Show icons text
        self.cb_icon_text = Gtk.CheckButton(_('Show toolbar\'s buttons text'))
        self.cb_icon_text.connect('toggled', self.cb_icon_text_cb, toolbar)
        hb_icons.pack_start(self.cb_icon_text, False, False, 0)
        
        grid_config.append_row(_('Icons:'), hb_icons)
        
        # Show / Hide side bar
        self.cb_sideb = Gtk.CheckButton(_('Show sidebar'))
        self.cb_sideb.connect('toggled', self.on_cb_sideb_toggled)
        self.vb_config.pack_start(self.cb_sideb, False, False, 0)
        
        # Use tray icon
        self.cb_tray = Gtk.CheckButton(_('Show tray icon'))
        self.cb_tray.connect('toggled', self.on_cb_tray_toggled)
        self.vb_config.pack_start(self.cb_tray, False, False, 0)
        
        # Shutdown after conversion
        self.cb_halt = Gtk.CheckButton(_('Shutdown computer after finish'))
        self.cb_halt.connect('toggled', self.on_cb_halt_toggled)
        self.vb_config.pack_start(self.cb_halt, False, False, 0)
        
        # Suspend after conversion
        self.cb_suspend = Gtk.CheckButton(_('Suspend computer after finish'))
        self.cb_suspend.connect('toggled', self.on_cb_suspend_toggled)
        self.vb_config.pack_start(self.cb_suspend, False, False, 0)
        
        # Remove source file
        self.cb_remove = Gtk.CheckButton(_('Delete input file after conversion'))
        self.vb_config.pack_start(self.cb_remove, False, False, 0)

        vbox.pack_start(Gtk.Separator(), False, False, 0)
        
        #--- Status
        self.label_details = Gtk.Label()
        vbox.pack_start(self.label_details, False, False, 0)
        
        # Status icon
        self.trayico = StatusIcon(self)
        self.fill_dict()
        
        
        #--- Load formats from formats.cfg file
        self.f_file = ConfigParser()
        self.f_file.read(join(APP_DIR, 'formats.cfg'))
        for section in sorted(self.f_file.sections()):
            self.cmb_formats.append_text(section)
        self.cmb_formats.set_active(0)
        
        #--- Load saved options.
        self.load_options()
        
        
        #--- Show interface
        self.show_all()
        
        #-- Show/Hide sidebar
        self._child.set_visible(self.cb_sideb.get_active())
        
        #--- Drag and Drop
        targets = Gtk.TargetList.new([])
        targets.add_uri_targets((1 << 5) - 1)
        self.drag_dest_set(Gtk.DestDefaults.ALL, [], Gdk.DragAction.COPY)
        self.drag_dest_set_target_list(targets)
        self.connect('drag-data-received', self.drop_data_cb)
        
        #--- Window connections
        self.connect('destroy', Gtk.main_quit)
        self.connect('delete-event', self.on_delete)
        self.connect("key-press-event", self.on_key_press)
    
        #--- Status icon
        self.trayico.set_visible(self.cb_tray.get_active())
        
        if cmd_line_files:
            self.tb_do_add(*cmd_line_files)
            
    def on_toggled_cb(self, widget, Path):
        self.store[Path][C_SKIP] = not self.store[Path][C_SKIP]
        
    def on_cb_same_qual_toggled(self, widget):
        active = widget.get_active()
        if active:
            self.vb_audio.set_sensitive(False)
            self.vb_video.set_sensitive(False)
        else:
            self.set_sensitives()
        
    
    def on_key_press(self, widget, event):
        """Cancel preview and stop conversion"""
        if event.keyval == Gdk.KEY_Escape:
            self.is_preview = False
            self.tb_stop_cb()
            
    def on_delete(self, widget, data):
        if self.cb_tray.get_active():
            self.hide_on_delete()
            return True
        else:
            self.quit_cb(widget)
            return False
    
    def quit_cb(self, *args):
        self.save_options()
        if self.is_converting:
            ''' Press quit btn during conversion process '''
            resp = show_message(None, _('Do you want to quit Curlew and \
abort conversion process?'),
                                Gtk.MessageType.QUESTION,
                                Gtk.ButtonsType.YES_NO)
            if resp == Gtk.ResponseType.YES:
                try:
                    self.fp.kill()
                    self.fp.terminate()
                    self.force_delete_file(self.out_file)
                except: 
                    pass
                Gtk.main_quit()
            return
        Gtk.main_quit()
    
    #--- Add files
    def tb_add_cb(self, *args):
        open_dlg = Gtk.FileChooserDialog(_("Add file"),
                                         self, Gtk.FileChooserAction.OPEN,
                                        (Gtk.STOCK_OK, 
                                         Gtk.ResponseType.OK,
                                         Gtk.STOCK_CANCEL,
                                         Gtk.ResponseType.CANCEL))
        if self.curr_open_folder:
            open_dlg.set_current_folder(self.curr_open_folder)
        open_dlg.set_select_multiple(True)
        
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
            self.tb_do_add(*open_dlg.get_filenames())
            #--- Saved current folder
            self.curr_open_folder = open_dlg.get_current_folder()
        open_dlg.destroy()
        
    def tb_do_add(self, *args):
        for file_name in args:
            if isfile(file_name):
                self.store.append([
                                   True,
                                   splitext(basename(file_name))[0],
                                   get_format_size(getsize(file_name)/1024),
                                   None,
                                   None,
                                   None,
                                   0.0,
                                   _('Ready!'),
                                   -1,
                                   realpath(file_name)
                                   ])
    
    
    def on_dest_clicked(self, widget):
        save_dlg = Gtk.FileChooserDialog(_("Choose destination"), self,
                                    Gtk.FileChooserAction.SELECT_FOLDER,
                                    (Gtk.STOCK_OK, Gtk.ResponseType.OK,
                                    Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL))
        save_dlg.set_current_folder(self.curr_save_folder)
        res = save_dlg.run()
        if res == Gtk.ResponseType.OK:
            self.e_dest.set_text(save_dlg.get_filename())
        self.curr_save_folder = save_dlg.get_current_folder()
        save_dlg.destroy()
    
    def cb_split_cb(self, cb_split):
        self.vb_group.set_sensitive(cb_split.get_active())
        
    def on_cmb_formats_changed(self, w):
        self.set_sensitives()
        self.fill_options()
    
    def on_cmb_formats_tooltip(self, widget, x, y, keyboard_mode, tooltip):
        #TODO: Enhance tooltip infos
        sect = self.cmb_formats.get_active_text()
        encoder = {'f': self.encoder, 'm': 'mencoder'}
        infos  = _('<b>Format:</b>\t{}\n'
                   '<b>Extension:</b>\t{}\n'
                   '<b>Encoder:</b>\t{}'
                   ).format(sect,
                            self.f_file.get(sect, 'ext'),
                            encoder[self.f_file.get(sect, 'encoder')],
                            )
        widget.set_tooltip_markup(infos)
    
    
    def set_sensitives(self):
        section = self.cmb_formats.get_active_text()
        media_type = self.f_file.get(section, 'type')

        # sens = [AudioP, VideoP, SubtitleP, aQuality, vQuality, CropPad, SameQual]
        if media_type == 'audio':
            sens = [True, False, False, False, False, False, True]
        elif media_type == 'video':
            sens = [True, True, False, False, False, True, True]
        elif media_type == 'mvideo':
            sens = [True, True, True, False, False, False, False]            
        elif media_type == 'ogg':
            sens = [True, False, False, True, False, False, True]
        elif media_type == 'ogv':
            sens = [True, True, False, True, True, False, True]
        elif media_type == 'presets':
            sens = [False, False, False, False, False, False, False]
        elif media_type == 'copy':
            sens = [False, False, False, False, False, False, False]

        self.vb_audio.set_sensitive(sens[0])      # Audio page
        self.vb_video.set_sensitive(sens[1])      # Video page
        self.frame_sub.set_sensitive(sens[2])     # Subtitle page
        self.hb_aqual.set_sensitive(sens[3])      # Audio quality slider (ogg)
        self.hb_vqual.set_sensitive(sens[4])      # video Quality slider (ogv)
        self.vb_crop.set_sensitive(sens[5])       # Crop/Pad page
        self.cb_same_qual.set_sensitive(sens[6])  # Same quality combo
        
        self.cb_same_qual.set_active(False)
    
    
    #--- fill options widgets
    def fill_options(self):
        section = self.cmb_formats.get_active_text()
        
        if self.f_file.has_option(section, 'extra'):
            self.e_extra.set_text(self.f_file.get(section, 'extra'))
        else:
            self.e_extra.set_text('')
            
        # For presets
        if self.f_file.has_option(section, 'cmd'):
            self.presets_cmd = self.f_file.get(section, 'cmd').split()
            return
            
        if self.f_file.has_option(section, 'ab'):
            self.c_abitrate.set_list(self.f_file.get(section, 'ab').split())
            
        if self.f_file.has_option(section, 'def_ab'):
            self.c_abitrate.set_text(self.f_file.get(section, 'def_ab'))
        
        if self.f_file.has_option(section, 'afreq'):
            self.c_afreq.set_list(self.f_file.get(section, 'afreq').split())
        
        if self.f_file.has_option(section, 'ach'):    
            self.c_ach.set_list(self.f_file.get(section, 'ach').split())
        
        if self.f_file.has_option(section, 'acodec'):
            self.c_acodec.set_list(self.f_file.get(section, 'acodec').split())
            
        if self.f_file.has_option(section, 'vb'):
            self.c_vbitrate.set_list(self.f_file.get(section, 'vb').split())
            
        if self.f_file.has_option(section, 'def_vb'):
            self.c_vbitrate.set_text(self.f_file.get(section, 'def_vb'))
            
        if self.f_file.has_option(section, 'vfps'):
            self.c_vfps.set_list(self.f_file.get(section, 'vfps').split())
        
        if self.f_file.has_option(section, 'vcodec'):
            self.c_vcodec.set_list(self.f_file.get(section, 'vcodec').split())
            
        if self.f_file.has_option(section, 'vsize'):
            self.c_vsize.set_list(self.f_file.get(section, 'vsize').split())
        
        if self.f_file.has_option(section, 'vratio'):
            self.c_vratio.set_list(self.f_file.get(section, 'vratio').split())            
        
    
    def build_avconv_cmd(self,
                         input_file, out_file,
                         start_pos='-1', part_dura='-1'):
        '''
        start_pos <=> -ss, part_dura <=> -t
        '''
        section = self.cmb_formats.get_active_text()
        media_type = self.f_file.get(section, 'type')
        
        cmd = [self.encoder, '-y'] #, '-xerror']
        
        if start_pos != '-1' and part_dura != '-1':
            cmd.extend(['-ss', start_pos])
        
        cmd.extend(["-i", input_file])
        
        # Threads
        if self.s_threads.get_value() != 0:
            cmd.extend(['-threads', 
                        '{}'.format(self.s_threads.get_value_as_int())])
        
        # Force format
        if self.f_file.has_option(section, 'ff'):
            cmd.extend(['-f', self.f_file.get(section, 'ff')])
            
        # Extract Audio
        if media_type in ['audio', 'ogg']:
            cmd.append('-vn')
        
        # Use the same quality
        if self.cb_same_qual.get_active():
            if self.encoder == 'ffmpeg': cmd.append('-sameq')
            if self.encoder == 'avconv': cmd.append('-same_quant')
        else:
            # Video opts
            if media_type == 'video':
                # Extract video only
                if self.cb_video_only.get_active():
                    cmd.append('-an')
                
                # Video bitrate
                if self.c_vbitrate.not_default():
                    cmd.extend(['-b', self.c_vbitrate.get_text()])
                # Video FPS
                if self.c_vfps.not_default():
                    cmd.extend(['-r', self.c_vfps.get_text()])
                # Video codec
                if self.c_vcodec.not_default():
                    cmd.extend(['-vcodec', self.c_vcodec.get_text()])
                
                # Video aspect ratio    
                if self.c_vratio.get_text() == 'default':
                    #-- force aspect ratio
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
                if self.c_vsize.not_default():
                    filters.append('scale={}'.format(self.c_vsize.get_text()))
                
                if filters:
                    cmd.append('-vf')
                    cmd.append(','.join(filters))
            
            
            # Audio
            if media_type in ['audio', 'video', 'ogg', 'ogv']:
                # Audio bitrate
                if self.c_abitrate.not_default():
                    cmd.extend(['-ab', self.c_abitrate.get_text()])
                # Audio Freq.
                if self.c_afreq.not_default():
                    cmd.extend(['-ar', self.c_afreq.get_text()])
                # Audio channel
                if self.c_ach.not_default():
                    cmd.extend(['-ac', self.c_ach.get_text()])
                
                # Audio codec
                if self.c_acodec.not_default():
                    cmd.extend(['-acodec', self.c_acodec.get_text()])
                    #
                    if self.c_acodec.get_text() == 'aac':
                        cmd.extend(['-strict', 'experimental'])

            # Ogg format
            if media_type in ['ogg', 'ogv']:
                cmd.extend(['-aq', str(self.a_scale.get_value())])
            
            # ogv format
            if media_type == 'ogv':
                cmd.extend(['-qscale', str(self.v_scale.get_value())])
                
            # Copy mode format
            if media_type == 'copy':
                cmd.extend(['-acodec', 'copy'])
                cmd.extend(['-vcodec', 'copy'])
            
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
            cmd.append('-an') # disable audio
            cmd.extend(['-pass', '1'])
            cmd.extend(['-passlogfile', PASS_LOG])
        elif self.pass_nbr == 2:
            cmd.extend(['-pass', '2'])
            cmd.extend(['-passlogfile', PASS_LOG])
        
        #--- Last
        cmd.append(out_file)
        return cmd
    
    
    #--- MEncoder cmd
    def build_mencoder_cmd(self, 
                           input_file, out_file,
                           start_pos= -1, part_dura= -1):

        cmd = ['mencoder']
        #--- Input and output files
        cmd.append(input_file)
        cmd.extend(['-o', out_file])
        cmd.append('-noskip')
        
        # Split file (mencoder)
        if start_pos != -1 and part_dura != -1:
            cmd.extend(['-ss', start_pos])
            if not self.cb_end.get_active():
                cmd.extend(['-endpos', part_dura])
        
        #--- Subtitle font
        if self.cb_sub.get_active():
            # Subtitle file
            cmd.extend(['-sub', self.entry_sub.get_text()])
            cmd.append('-fontconfig') # configure font
            
            # Use SSA/ASS
            if self.cb_ass.get_active():
                cmd.append('-ass')
                #TODO: Add more options here.
            # Normal OSD
            else:
                # Font name
                cmd.extend(['-subfont', self.b_font.get_font_family().get_name()])
                cmd.extend(['-subfont-text-scale',
                            str(self.spin_size.get_value_as_int())])
                cmd.extend(['-subpos', str(self.spin_pos.get_value_as_int())])
                #--- Delay Sub
                if self.sub_delay.get_value() != 0:
                    cmd.extend(['-subdelay', str(self.sub_delay.get_value_as_int())])
            
            # RTL language (Arabic)
            cmd.extend(['-subcp', self.cmb_enc.get_active_text()])
            cmd.append('-flip-hebrew')
            cmd.append('-noflip-hebrew-commas')
        
        
        #--- Audio codec and opts
        cmd.extend(['-oac', self.c_acodec.get_text()])
        # No audio options with 'copy'
        if self.c_acodec.get_text() == 'copy':
            pass
        else:
            a_opts = []
            
            #--- For mp3lame codec
            if self.c_acodec.get_text() == 'mp3lame':
                cmd.append('-lameopts')
                # Use constant bitrate
                a_opts.append('cbr') 
                # Audio channels
                a_opts.append('mode={}'.format(self.c_ach.get_text())) 
                # Audio bitrate
                a_opts.append('br={}'.format(self.c_abitrate.get_text()))
            
            #--- For faac audio codec
            elif self.c_acodec.get_text() == 'faac':
                cmd.append('-faacopts')
                # Bitrate
                a_opts.append('br={}'.format(self.c_abitrate.get_text()))
            
            #--- For libavcodec audio (lavc)
            elif self.c_acodec.get_text() == 'lavc':
                cmd.append('-lavcopts')
                # Bitrate
                a_opts.append('abitrate={}'.format(self.c_abitrate.get_text()))
                # Codec used
                a_opts.append('acodec=mp2')
                
            #--- Append cmd with audio opts
            cmd.append(':'.join(a_opts))
            
        
        #--- Video codec and opts
        cmd.extend(['-ovc', self.c_vcodec.get_text()])
        
        #--- For XviD video codec
        v_opts = []
        if self.c_vcodec.get_text() == 'xvid':
            cmd.append('-xvidencopts')
            # Video bitrate
            v_opts.append('bitrate={}'.format(self.c_vbitrate.get_text()))
            # More...
            v_opts.append('autoaspect')
            v_opts.append('vhq=2:bvhq=1:trellis:hq_ac:chroma_me:chroma_opt')
            v_opts.append('quant_type=mpeg')
            # Pass number
            if self.pass_nbr != 0:
                v_opts.append('pass={}'.format(self.pass_nbr))
        
        #--- For libavcodec video opts (divx)
        elif self.c_vcodec.get_text() == 'lavc':
            cmd.append('-lavcopts')
            # Bitrate
            v_opts.append('vbitrate={}'.format(self.c_vbitrate.get_text()))
            # Additional options.
            v_opts.append('vcodec=mpeg4:autoaspect')
            if self.pass_nbr != 1:
                v_opts.append('mbd=2:trell')
                
            # Pass number (1 or 2)
            if self.pass_nbr != 0:
                v_opts.append('vpass={}'.format(self.pass_nbr))
        
        #--- For H.264 video
        elif self.c_vcodec.get_text() == 'x264':
            cmd.append('-x264encopts')
            # Bitrate
            v_opts.append('bitrate={}'.format(self.c_vbitrate.get_text()))
            # Additional options.
            v_opts.append('subq=5:8x8dct:me=umh:frameref=2:bframes=3:weight_b')
            # Pass number (1 or 2)
            if self.pass_nbr != 0:
                v_opts.append('pass={}'.format(self.pass_nbr))
        
        # Threads number (x264, xvid, divx)
        if self.s_threads.get_value() != 0:
            v_opts.append('threads={}'.format(self.s_threads.get_value_as_int()))
        
        # Append cmd with video opts
        cmd.append(':'.join(v_opts))
            
        # Add extra option if exist.
        if self.e_extra.get_text().strip() != '':
            cmd.extend(self.e_extra.get_text().split())
            
        # Add option suitable for each pass (1 or 2)
        if self.pass_nbr == 1:
            cmd.append('-nosound') # disable audio
            cmd.extend(['-passlogfile', PASS_LOG])
        elif self.pass_nbr == 2:
            cmd.extend(['-passlogfile', PASS_LOG])
        
        #--- Split file (encode part of file)
        if self.cb_split.get_active():
            cmd.extend(['-ss', self.tl_begin.get_time_str()])
            if not self.cb_end.get_active():
                cmd.extend(['-endpos', self.tl_duration.get_time_str()])
        
        filters = []
        #--- Video size
        if self.c_vsize.not_default():
            filters.append('scale={}'.format(self.c_vsize.get_text()))
        
        # Harddup
        if self.cb_hard.get_active():
            filters.append('harddup')
        
        if filters:
            cmd.append('-vf')
            cmd.append(','.join(filters))
        
        #--- Video FPS
        if self.c_vfps.get_active_text() != 'default':
            cmd.append('-mf')
            cmd.append('fps={}'.format(self.c_vfps.get_active_text()))
        
        return cmd

    #--- Convert funtcion
    def convert_cb(self, widget):
        if len(self.store) == 0 or self.is_converting:
            return
        
        # Return when invalid / inaccessible path
        if not isdir(self.e_dest.get_text()):
            show_message(self,
                         _('Destination path is not valid.'),
                         Gtk.MessageType.ERROR)
            self.set_focus(self.e_dest)
            return
        if not os.access(self.e_dest.get_text(), os.W_OK):
            show_message(self,
                         _('Destination path is not accessible.'),
                         Gtk.MessageType.ERROR)
            self.set_focus(self.e_dest)
            return
        
        self.set_focus(None)
        
        self.Iter = self.store.get_iter_first()
        self.is_converting = True
        self.pass_nbr = int(self.cb_2pass.get_active())
        # Delete error log
        self.force_delete_file(ERROR_LOG)
        self.errs_nbr = 0
        
        self._start_time = time.time()
        GObject.timeout_add(100, self._on_elapsed_timer)
        
        self.convert_file()
        

    def convert_file(self):
        f_type = self.f_file.get(self.cmb_formats.get_active_text(), 'type')
        ext = self.f_file.get(self.cmb_formats.get_active_text(), 'ext')
        encoder_type = self.f_file.get(self.cmb_formats.get_active_text(),
                                       'encoder')
        
        #--- Check
        if self.Iter != None:
            #--- Do not convert this file (unchecked)
            if self.store[self.Iter][C_SKIP] == False:
                self.store[self.Iter][C_STAT] = _("Skipped!")
                # Jump to next file
                self.Iter = self.store.iter_next(self.Iter)
                self.convert_file()
                return
                     
            #--- Get input file
            input_file = self.store[self.Iter][C_FILE]
            # When input file not found
            if not isfile(input_file):
                self.store[self.Iter][C_STAT] = _("Not found!")
                self.Iter = self.store.iter_next(self.Iter)
                self.convert_file()
                return    
            
            #----------------------------
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
                    self.store[self.Iter][C_STAT] = _('Skipped!')
                    self.Iter = self.store.iter_next(self.Iter)
                    self.convert_file()
                    return
            
            self.out_file = out_file
        
            # Encoding in /tmp "temporary folder" in 1st pass
            if self.pass_nbr == 1:
                out_file = PASS_1_FILE
            
            #--- Which encoder use (avconv of mencoder)
            if encoder_type == 'f':
                if self.cb_split.get_active():
                    full_cmd = \
                    self.build_avconv_cmd(input_file, out_file,
                                          self.tl_begin.get_time_str(),
                                          self.tl_duration.get_time_str())
                else:
                    full_cmd = self.build_avconv_cmd(input_file, out_file)
                    
            elif encoder_type == 'm':
                if self.cb_split.get_active():
                    full_cmd = self.build_mencoder_cmd(input_file, out_file,
                                            self.tl_begin.get_time_str(),
                                            self.tl_duration.get_time_str()) 
                else:
                    full_cmd = self.build_mencoder_cmd(input_file, out_file)
            
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
                self.fp = Popen(full_cmd, stdout=PIPE, stderr=PIPE,
                                universal_newlines=True, bufsize=-1)
            except:
                print('Encoder not found (ffmpeg/avconv or mencoder) :(')
                self.is_converting = False
                self.enable_controls(True)
                return -1
            
            #--- Watch stdout and stderr
            GLib.io_add_watch(self.fp.stdout,
                              GLib.IO_IN | GLib.IO_HUP,
                              self.on_output, encoder_type, out_file)
            GLib.io_add_watch(self.fp.stderr,
                              GLib.IO_IN | GLib.IO_HUP,
                              self.on_output, encoder_type, out_file)
            #--- On end process
            GLib.child_watch_add(self.fp.pid, self.on_end, (out_file, full_cmd))
            
        else:
            self.is_converting = False

            if self.errs_nbr > 0:
                resp = show_message(
                                    self,
                                    _('There are some errors occured.\n'
                                      'Do you want to show more details?'),
                                    Gtk.MessageType.WARNING,
                                    Gtk.ButtonsType.YES_NO)
                if resp == Gtk.ResponseType.YES:
                    dia = LogDialog(self, ERROR_LOG)
                    dia.show_dialog()
    
    
    #--- Stop conversion cb
    def tb_stop_cb(self, *args):        
        if self.is_converting == True:
            resp = show_message(None,
                                _('Do you want to stop conversion process?'),
                                Gtk.MessageType.QUESTION,
                                Gtk.ButtonsType.YES_NO)
            if resp == Gtk.ResponseType.YES and self.is_converting == True:
                try:
                    if self.fp:
                        self.fp.kill()
                except OSError as err:
                    print(err)
                finally:
                    self.is_converting = False
                    self.enable_controls(True)
                    self.label_details.set_text('')
                return True
                    
    
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
            Proc = Popen(cmd, stdout=PIPE, stderr=PIPE)
            out_str = Proc.stderr.read()
        except: pass
                
        try:
            time_list = self.reg_duration.findall(out_str)[0].split(':')
        except:
            return duration
        duration = int(time_list[0]) * 3600 + int(time_list[1]) * 60 + \
        float(time_list[2])
        return duration
    
    def get_time(self, input_file):
        ''' Get time duration file 0:00:00'''
        cmd = '{} -i "{}"'.format(self.encoder, input_file)
        Proc = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
        out_str = Proc.stderr.read()
        try:
            return self.reg_duration.findall(out_str)[0]
        except:
            return '0:00:00.00'
    
    #---- Select subtitle
    def b_enc_cb(self, widget):
        dlg = Gtk.FileChooserDialog(_('Select subtitle'),
                                    self,
                                    Gtk.FileChooserAction.OPEN,
                                    (Gtk.STOCK_ADD, Gtk.ResponseType.OK,
                                     Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
                                     )
        dlg.set_current_folder(self.curr_open_folder)
        Filter = Gtk.FileFilter()
        Filter.set_name(_("Subtitle files"))
        Filter.add_pattern("*.[Ss][Rr][Tt]*")
        Filter.add_pattern("*.[Ss][Uu][Bb]*")
        Filter.add_pattern("*.[Aa][Ss][Ss]*")
        Filter.add_pattern("*.[Ss][Ss][Aa]*")
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
    def tb_remove_cb(self, *args):
        iters = self.get_selected_iters()
        if not iters:
            return      
        elif self.is_converting:
            for Iter in iters:
                if self.store[Iter][:] != self.store[self.Iter][:]:
                    self.store.remove(Iter)
        else:
            for i in iters: self.store.remove(i)
    
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
            call('{} -autoexit "{}"'.format(self.player,
                                            self.store[Iter][C_FILE]),
                 shell=True)
        
    def on_browse_cb(self, widget):
        if self.cb_dest.get_active():
            Iter = self.get_selected_iters()[0]
            call(['xdg-open', dirname(self.store[Iter][C_FILE])])
        else:
            call(['xdg-open', self.e_dest.get_text()])
            
    def on_preview_cb(self, widget):
        if self.is_converting:
            return
        
        self.is_preview = True
        encoder_type = self.f_file.get(self.cmb_formats.get_active_text(),
                                       'encoder')
        Iter = self.get_selected_iters()[0]
        input_file = self.store[Iter][C_FILE]
        duration = self.get_duration(input_file)
        preview_begin = str(duration / 10)
        
        if encoder_type == 'f':
            cmd = self.build_avconv_cmd(input_file, PREVIEW_FILE,
                                        preview_begin, TEN_SECONDS)
        elif encoder_type == 'm':
            cmd = self.build_mencoder_cmd(input_file, PREVIEW_FILE,
                                          preview_begin, TEN_SECONDS)
    
        try:
            fp = Popen(cmd, stdout=PIPE, stderr=PIPE)
        except: return -1
        
        # Disable main window
        self.get_child().set_sensitive(False)
        
        # Wait...
        while fp.poll() == None:
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
            
        # Update informations.
        self.store[Iter][C_PRGR] = 0.0
        self.store[Iter][C_STAT] = _('Ready!')
        self.store[Iter][C_PULS] = -1
        
        # Play preview file.
        fp = Popen('{} -autoexit -window_title {} "{}"'.format(self.player,
                                                         _('Preview'),
                                                         PREVIEW_FILE),
             shell=True)
        
        # Delete preview file after the end of playing
        while fp.poll() == None:
            pass
        self.force_delete_file(PREVIEW_FILE)
        
        # Enable main window
        self.get_child().set_sensitive(True)
    

    #--- Clear list    
    def tb_clear_cb(self, widget):
        if not self.is_converting:
            self.tree.set_model(None)
            self.store.clear()
            self.tree.set_model(self.store)
        
    def tb_about_cb(self, widget):
        a_dgl = About(self)
        a_dgl.show()
        
    def cb_sub_toggled(self, cb_sub):
        self.vb_sub.set_sensitive(cb_sub.get_active())
    
    # Keyboard events.
    def on_tree_key_press(self, widget, event):
        
        # Delete file with "Delete" key
        if event.keyval == Gdk.KEY_Delete:
            self.tb_remove_cb()
        
        # Play file with "Return" key
        elif event.keyval == Gdk.KEY_Return:
            self.on_play_cb()
            
    # Mouse events
    def on_button_press(self, widget, event):
        # There is no file
        if len(self.store) == 0:
            if event.button == 1 and event.get_click_count()[1] == 2:
                self.tb_add_cb()
                return
        
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
    def on_end(self, pid, err_code, (out_file, cmd)):
        if self.Iter != None:
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
                
                self.store[self.Iter][C_SKIP] = False
                self.store[self.Iter][C_PRGR] = 100.0
                self.store[self.Iter][C_STAT] = _("Done!")
                self.store[self.Iter][C_PULS] = -1
                
                # Remove source file
                if self.cb_remove.get_active():
                    self.force_delete_file(self.store[self.Iter][C_FILE])
                
                # Update start time
                self._start_time = time.time()
                
                # Convert the next file
                self.Iter = self.store.iter_next(self.Iter)
                self.convert_file()
            
            # Converion failed
            elif err_code == 256:
                self.store[self.Iter][C_STAT] = _("Failed!")
                self.force_delete_file(out_file)
                
                # Write erros log
                self.write_log(cmd)
                self.errs_nbr += 1
                
                # Convert the next file
                self.Iter = self.store.iter_next(self.Iter)
                self.convert_file()
            
            # Conversion stopped
            elif err_code == 9:
                # Remove uncompleted file
                self.force_delete_file(out_file)
                return
                    
        else:
            self.is_converting = False
            
        if self.Iter == None:
            self.enable_controls(True)
            self.label_details.set_text('')
            # Shutdown system
            if self.cb_halt.get_active():
                self.shutdown()
            # Suspend system
            if self.cb_suspend.get_active():
                self.suspend()
        
    
        
    
    #--- Catch output 
    def on_output(self, source, condition, encoder_type, out_file):
        #--- Allow interaction with application widgets.
        self.log = source
        while Gtk.events_pending():
            Gtk.main_iteration()
        
        if self.Iter == None:
            return False
        
        #--- Skipped file during conversion (unckecked file during conversion)
        if self.store[self.Iter][C_SKIP] == False:
            self.store[self.Iter][C_STAT] = _("Skipped!")
            self.store[self.Iter][C_PRGR] = 0.0
            
            # Stop conversion
            try: self.fp.kill()
            except OSError as detail:
                print(detail)
            
            # Delete the file
            self.force_delete_file(out_file)
            
            # Update start time
            self._start_time = time.time()
            
            # Jump to next file
            self.Iter = self.store.iter_next(self.Iter)
            self.convert_file()
            return False
        
        line = source.readline()
        self.log = source
        if len(line) > 0:
            # avconv progress
            if encoder_type == 'f':
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
                        self.store[self.Iter][C_PULS] = self.store[self.Iter][C_PULS] + 1
                        self.store[self.Iter][C_STAT] = _('Wait...')
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
                        self.store[self.Iter][C_ESIZE] = size_str
                        self.store[self.Iter][C_ELAPT] = self.elapsed_time
                        self.store[self.Iter][C_REMN] = rem_time
                        self.store[self.Iter][C_PRGR] = float(time_ratio * 100) 
                        if self.pass_nbr != 0:
                            self.store[self.Iter][C_STAT] = '{:.2%} (P{})'\
                            .format(time_ratio, self.pass_nbr) # progress text
                        else:
                            self.store[self.Iter][C_STAT] = '{:.2%}'\
                            .format(time_ratio) # progress text
                        self.store[self.Iter][C_PULS] = -1 # progress pusle
            
            # mencoder progress
            elif encoder_type == 'm':
                begin = line.find('Pos:')
                if begin != -1:
                    # Print log
                    self.label_details.set_text(line.strip())
                    
                    #--- Get file size
                    file_size = self.reg_menc.findall(line)[0][2]
                    
                    #--- Get remaining time
                    dur = self.reg_menc.findall(line)[0][0]
                    rem_dur = self.total_duration - float(dur)
                    rem_time = duration_to_time(rem_dur)
                    
                    #--- Progress
                    prog_value = float(self.reg_menc.findall(line)[0][1])
                    
                    self.store[self.Iter][C_ESIZE] = file_size + _(' MB')
                    self.store[self.Iter][C_ELAPT] = self.elapsed_time
                    self.store[self.Iter][C_REMN] = rem_time
                    self.store[self.Iter][C_PRGR] = prog_value
                    if self.pass_nbr != 0:
                        self.store[self.Iter][C_STAT] = '{:.2f}% (P{})'\
                        .format(prog_value, self.pass_nbr)
                    else:    
                        self.store[self.Iter][C_STAT] = '{:.0f}%'.format(prog_value)
                    self.store[self.Iter][C_PULS] = -1
                
                if begin == -1 and self.is_converting:
                    time.sleep(0.05)
                    self.store[self.Iter][C_PULS] = self.store[self.Iter][C_PULS] + 1
                    self.store[self.Iter][C_STAT] = _('Wait...')
                
            
            #--- Continue read output
            return True
        # When len(line) == 0
        return False

    
    #--- Drag and drop callback
    def drop_data_cb(self, widget, dc, x, y, selection_data, info, t):
        for i in selection_data.get_uris():
            if i.startswith('file://'):
                File = unquote(i[7:])
                if isfile(File):
                    self.store.append([True,
                                       basename(File),
                                       get_format_size(getsize(File)/1024),
                                       None,
                                       None,
                                       None,
                                       0.0,
                                       _('Ready!'),
                                       -1,
                                       File])
                # Save directory from dragged filename.
                self.curr_open_folder = dirname(File)
    
    def on_cb_dest_toggled(self, widget):
        Active = not widget.get_active()
        self.e_dest.set_sensitive(Active)
        self.b_dest.set_sensitive(Active)
    
    def cmb_encoder_cb(self, combo):
        self.encoder = combo.get_active_text()
    
    def on_cb_video_only_toggled(self, cb):
        self.vb_audio.set_sensitive(not cb.get_active())
    
    def force_delete_file(self, file_name):
        ''' Force delete file_name '''
        while exists(file_name):
            try:
                os.unlink(file_name)
            except OSError:
                continue
    
    def per_to_vol(self, percent):
        # 100 --> 256, 200 --> 512, 300 --> 768 ...
        return '{}'.format((256 * int(percent)) / 100)

    def get_aspect_ratio(self, input_file):
        ''' extract adpect ratio from file if exist, otherwise use 4:3 
        (fix a problem) '''
        cmd = '{} -i {}'.format(self.encoder, input_file)
        Proc = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
        out_str = Proc.stderr.read()
        try:
            reg_aspect = re.compile('''DAR\s+(\d*:\d*)''')
            return reg_aspect.findall(out_str)[0]
        except:
            return '4:3'
    
    def enable_controls(self, sens=True):
        self.cmb_formats.set_sensitive(sens)
        self.e_dest.set_sensitive(sens)
        self.b_dest.set_sensitive(sens)
        self.cb_dest.set_sensitive(sens)
        self.cb_same_qual.set_sensitive(sens)
        
        self.vb_audio.set_sensitive(sens)
        self.vb_video.set_sensitive(sens)
        self.vb_sub.set_sensitive(sens)
        self.vb_more.set_sensitive(sens)
        self.vb_crop.set_sensitive(sens)
    
    def save_options(self):
        conf = ConfigParser()
        conf.read(OPTS_FILE)
        
        if not conf.has_section('configs'):
            conf.add_section('configs')
        
        conf.set('configs', 'curr_open_folder', self.curr_open_folder)
        conf.set('configs', 'curr_save_folder', self.curr_save_folder)
        conf.set('configs', 'e_dest_text', self.e_dest.get_text())
        conf.set('configs', 'cmb_formats_ind', self.cmb_formats.get_active())
        conf.set('configs', 'cb_same_dest_on', self.cb_dest.get_active())
        conf.set('configs', 'cb_same_qual_on', self.cb_same_qual.get_active())
        conf.set('configs', 'overwrite_mode', self.cmb_exist.get_active())
        conf.set('configs', 'encoder', self.cmb_encoder.get_active_id())
        conf.set('configs', 'font', self.b_font.get_font_name())
        conf.set('configs', 'encoding', self.cmb_enc.get_active_id())
        conf.set('configs', 'use_ass', self.cb_ass.get_active())
        conf.set('configs', 'side_bar', self.cb_sideb.get_active())
        conf.set('configs', 'tray', self.cb_tray.get_active())
        conf.set('configs', 'icons', self.cmb_icons.get_active_id())
        conf.set('configs', 'language', self.cmb_lang.get_active_id())
        conf.set('configs', 'text_icon', self.cb_icon_text.get_active())
        
        conf.set('configs', 'audio_bitrate', self.c_abitrate.get_text())
        conf.set('configs', 'audio_frequency', self.c_afreq.get_text())
        conf.set('configs', 'audio_channels', self.c_ach.get_text())
        conf.set('configs', 'audio_codec', self.c_acodec.get_text())
        
        conf.set('configs', 'video_bitrate', self.c_vbitrate.get_text())
        conf.set('configs', 'video_fps', self.c_vfps.get_text())
        conf.set('configs', 'video_size', self.c_vsize.get_text())
        conf.set('configs', 'video_codec', self.c_vcodec.get_text())
        conf.set('configs', 'video_ratio', self.c_vratio.get_text())
        
        conf.set('configs', 'video_2pass', self.cb_2pass.get_active())
        conf.set('configs', 'video_video_only', self.cb_video_only.get_active())
        
        with open(OPTS_FILE, 'w') as configfile:
            conf.write(configfile)
        
        
    def load_options(self):
        conf = ConfigParser()
        conf.read(OPTS_FILE)
        
        if not conf.has_section('configs'):
            return
        try:
            self.curr_open_folder = conf.get('configs', 'curr_open_folder')
            self.curr_save_folder = conf.get('configs', 'curr_save_folder')
            self.e_dest.set_text(conf.get('configs', 'e_dest_text'))
            self.cmb_formats.set_active(conf.getint('configs', 'cmb_formats_ind'))
            self.cb_dest.set_active(conf.getboolean('configs', 'cb_same_dest_on'))
            self.cb_same_qual.set_active(conf.getboolean('configs', 'cb_same_qual_on'))
            self.cmb_exist.set_active(conf.getint('configs', 'overwrite_mode'))
            self.cmb_encoder.set_active_id(conf.get('configs', 'encoder'))
            self.b_font.set_font(conf.get('configs', 'font'))
            self.cmb_enc.set_active_id(conf.get('configs', 'encoding'))
            self.cb_ass.set_active(conf.getboolean('configs', 'use_ass'))
            self.cb_sideb.set_active(conf.getboolean('configs', 'side_bar'))
            self.cb_tray.set_active(conf.getboolean('configs', 'tray'))
            self.cmb_icons.set_active_id(conf.get('configs', 'icons'))
            self.cmb_lang.set_active_id(conf.get('configs', 'language'))
            self.cb_icon_text.set_active(conf.getboolean('configs', 'text_icon'))
            
            self.c_abitrate.set_text(conf.get('configs', 'audio_bitrate'))
            self.c_afreq.set_text(conf.get('configs', 'audio_frequency'))
            self.c_ach.set_text(conf.get('configs', 'audio_channels'))
            self.c_acodec.set_text(conf.get('configs', 'audio_codec'))
            
            self.c_vbitrate.set_text(conf.get('configs', 'video_bitrate'))
            self.c_vfps.set_text(conf.get('configs', 'video_fps'))
            self.c_vsize.set_text(conf.get('configs', 'video_size'))
            self.c_vcodec.set_text(conf.get('configs', 'video_codec'))
            self.c_vratio.set_text(conf.get('configs', 'video_ratio'))
            
            self.cb_2pass.set_active(conf.getboolean('configs', 'video_2pass'))
            self.cb_video_only.set_active(conf.getboolean('configs', 'video_video_only'))
            
        except NoOptionError as err:
            print(err)
    
    def write_log(self, cmd):
        with open(ERROR_LOG, 'a') as f_log:
            # Command line
            f_log.write('Command line #{}:\n****************\n'\
                        .format(self.errs_nbr+1))
            f_log.write('{}\n'.format(' '.join(cmd)))
            # Error details
            f_log.write('\nError detail:\n*************\n')
            f_log.write(self.log.read())
            f_log.write('\n')
    
    def on_cb_tray_toggled(self, cb_tray):
        self.trayico.set_visible(cb_tray.get_active())
    
    def on_cmb_icons_changed(self, cmb_icons):
        '''Change toolbar icons'''
        icons_path = self.dict_icons[cmb_icons.get_active_text()]
        
        self.add_tb.set_icon(icons_path)
        self.remove_tb.set_icon(icons_path)
        self.clear_tb.set_icon(icons_path)
        self.convert_tb.set_icon(icons_path)
        self.stop_tb.set_icon(icons_path)
        self.about_tb.set_icon(icons_path)
        self.quit_tb.set_icon(icons_path)
        self.show_all()
    
    
    def fill_dict(self):
        self.dict_icons = {}
        
        root_icons_path = join(APP_DIR, 'icons')
        user_icons_path = join(CONF_PATH, 'icons')
        if not exists(user_icons_path):
            os.mkdir(user_icons_path)
        
        # Default (root) directory
        for i in listdir(root_icons_path):
            if isdir(join(root_icons_path, i)):
                self.dict_icons[i] = join(root_icons_path, i)
        
        # User directory
        for i in listdir(user_icons_path):
            if isdir(join(user_icons_path, i)):
                self.dict_icons[i] = join(user_icons_path, i)
        
        self.cmb_icons.set_list(self.dict_icons.keys())
    
    
    def install_locale(self):
        conf = ConfigParser()
        conf.read(OPTS_FILE)
        # .curlew.cfg not found
        try:
            lang_name = conf.get('configs', 'language')
        except:
            return
        
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
            cmd = 'dbus-send --system --print-reply --system --dest=org.freedesktop.ConsoleKit /org/freedesktop/ConsoleKit/Manager org.freedesktop.ConsoleKit.Manager.Stop'
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
            cmd = 'dbus-send --system --print-reply --system --dest=org.freedesktop.UPower /org/freedesktop/UPower org.freedesktop.UPower.Suspend'
            call(cmd, shell=True)
            return False
        return True
    
    # Show / Hide text in toolbar
    def cb_icon_text_cb(self, cb_icon_text, toolbar):
        if cb_icon_text.get_active():
            toolbar.set_style(Gtk.ToolbarStyle.BOTH)
        else:
            toolbar.set_style(Gtk.ToolbarStyle.ICONS)
    
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
    
    # Add current format to favorite list.
    def to_fav_cb(self, widget):
        fav_list = self.get_fav_list()
        fav_format = self.cmb_formats.get_active_text()
        
        # format already exist
        if fav_format in fav_list:
            return
        
        fav_list.append(fav_format)
        favfile = open(FAV_FILE, "wb")
        cPickle.dump(fav_list, favfile)
        favfile.close()
        
        self.build_fav_menu()
    
    # Remove current item from favorite
    def remove_from_fav(self, item):
        fav_list = self.get_fav_list()
        if not item in fav_list:
            return
        fav_list.remove(item)
        favfile = open(FAV_FILE, "wb")
        cPickle.dump(fav_list, favfile)
        favfile.close()
        
    def get_fav_list(self):
        if not exists(FAV_FILE):
            return []
        with open(FAV_FILE, 'r') as favfile:
            return cPickle.load(favfile)
    
    # show favorite menu
    def show_menu(self, widget):
        self.fav_menu.show_all()
        self.fav_menu.popup(None, None, None, None, 3, 
                            Gtk.get_current_event_time())
    
    # Select format from fav
    def on_item_activated(self, item):
        self.cmb_formats.set_active_id(item.get_label())
        self.fav_menu.select_item(item)
    
    def _append(self, menu, text):
        item = Gtk.MenuItem(text)
        item.connect('activate', self.on_item_activated)
        menu.append(item)
    
    def build_fav_menu(self):
        menu = Gtk.Menu()
        
        for fformat in self.get_fav_list():
            self._append(menu, fformat)
        
        menu.append(Gtk.SeparatorMenuItem())
        
        # "Add" item
        add_item = Gtk.ImageMenuItem(_("Add to favorite"))
        add_item.set_image(Gtk.Image.new_from_stock(Gtk.STOCK_ADD, 
                                                    Gtk.IconSize.MENU))
        add_item.set_always_show_image(True)
        add_item.connect('activate', self.to_fav_cb)
        menu.append(add_item)
        
        # Edit item
        edt_item = Gtk.ImageMenuItem(_("Edit list"))
        edt_item.set_image(Gtk.Image.new_from_stock(Gtk.STOCK_EDIT, 
                                                    Gtk.IconSize.MENU))
        edt_item.set_always_show_image(True)
        edt_item.connect('activate', self.edit_favorite)
        menu.append(edt_item)
        
        self.fav_menu = menu
        self.fav_menu.show_all()
    
    # Edit favorite list
    def edit_favorite(self, item):
        fav_dlg = Favorite(self, self.get_fav_list())
        fav_dlg.run()
        fav_dlg.save(FAV_FILE)
        self.build_fav_menu()
        fav_dlg.destroy()
    
    #
    def cb_end_cb(self, w):
        self.tl_duration.set_sensitive(not w.get_active())
    
    # Copy mode callback 
    def on_cb_copy_mode_toggled(self, w):
        if w.get_active():
            self.last_format = self.cmb_formats.get_active_text()
            self.cmb_formats.set_active_id("Copy Mode")
        else:
            self.cmb_formats.set_active_id(self.last_format)
    
    
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
        
        # Show file informations
        self.label_infos.set_markup(_('<b>Duration:</b> {}\n'
                                    '<b>Size:</b> {}\n'
                                    '<b>Extension:</b> {}\n')
                                    .format(self.get_time(input_file),
                                            self.store[Iter][C_FSIZE],
                                            splitext(input_file)[1],
                                            ))
        
        # Show image preview (screenshot)
        self.force_delete_file(IMG_PREV)
        img_pos = self.get_duration(input_file) / 10
        call('{} -ss {} -i "{}" -f image2 -frames:v 1 -s sqcif {}'
             .format(self.encoder, img_pos, input_file, IMG_PREV),
             shell=True, stdout=PIPE, stderr=PIPE)
        if exists(IMG_PREV):
            self.image_prev.set_from_file(IMG_PREV)
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
        


class DBusService(dbus.service.Object):
    def __init__(self, app, *args):
        self.app = app
        bus_name = dbus.service.BusName('org.Curlew', bus = dbus.SessionBus())
        dbus.service.Object.__init__(self, bus_name, '/org/Curlew')

    @dbus.service.method(dbus_interface='org.Curlew')
    
    def present(self, *args):
        self.app.tb_do_add(*args)
        self.app.present()


def main(*args):
    if dbus.SessionBus().request_name("org.Curlew") != \
       dbus.bus.REQUEST_NAME_REPLY_PRIMARY_OWNER:
        print('Curlew already running')
        method = dbus.SessionBus().get_object("org.Curlew", "/org/Curlew").\
        get_dbus_method("present")
        method(*args)
    else:
        app = Curlew(*args)
        DBusService(app)
        Gtk.main()

if __name__ == '__main__':
    main()
