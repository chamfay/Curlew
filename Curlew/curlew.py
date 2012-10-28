#-*- coding:utf-8 -*-


#===============================================================================
# Application : Curlew multimedia converter
# Author: Chamekh Fayssal <chamfay@gmail.com>
# License: Waqf license, see: http://www.ojuba.org/wiki/doku.php/waqf/license
#===============================================================================

# TODO: Fix combo sensitivities

try:
    import sys 
    import os
    import re
    import time
    from subprocess import Popen, PIPE, call
    from os.path import basename, isdir, splitext, join, dirname, realpath
    from ConfigParser import ConfigParser, NoOptionError, NoSectionError
    from urllib import unquote
    from gi.repository import Gtk, GLib, Gdk
    
    from customwidgets import LabeledHBox, TimeLayout, \
                              LabeledComboEntry, CustomHScale
    from about import APP_NAME, APP_VERSION, About
    from functions import * 
    import i18n
    
except Exception as detail:
    print(detail)
    sys.exit(1)


APP_DIR = dirname(realpath(__file__))
HOME = os.getenv("HOME")


def create_tool_btn(icon_name, tooltip, callback):
    ''' Build custom toolbutton '''
    toolbtn = Gtk.ToolButton()
    widget = Gtk.Image.new_from_file(join(APP_DIR, 'data', icon_name))
    toolbtn.set_icon_widget(widget)
    toolbtn.set_tooltip_markup(_('{}').format(tooltip))
    toolbtn.connect('clicked', callback)
    return toolbtn

def get_aspect_ratio(input_file):
    ''' extract adpect ratio from file if exist, otherwise use 4:3 
    (fix a problem) '''
    cmd = 'avconv -i {}'.format(input_file)
    Proc = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
    out_str = Proc.stderr.read()
    try:
        reg_aspect = re.compile('''DAR\s+(\d*:\d*)''')
        return reg_aspect.findall(out_str)[0]
    except:
        return '4:3'

#--- Main class        
class Curlew(Gtk.Window):
    
    def __init__(self):
        
        #--- Variables
        self.curr_open_folder = None
        self.curr_save_folder = None
        self.is_converting = False
        self.fp = None
        self.Iter = None
        self.output_details = ''
        self.total_duration = 0.0
        self.out_file = None
        self.opts_file = join(HOME, '.curlew.cfg')
        
        #--- Regex
        self.reg_avconv_u = re.compile('''size=\s+(\d+\.*\d*).*time=(\d+\.\d*)''') # ubuntu
        self.reg_avconv_f = re.compile('''size=\s+(\d+\.*\d*).*time=(\d+:\d+:\d+.\d+)''') # fedora
        self.reg_menc = re.compile('''.(\d+\.*\d*)s.*(.\d+)%.*\s+(\d+)mb''')
        self.reg_duration = re.compile('''Duration:.*(\d+:\d+:\d+\.\d+)''')
               
        Gtk.Window.__init__(self)        
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_title('{} {}'.format(APP_NAME, APP_VERSION))
        self.set_border_width(6)
        self.set_size_request(680, -1)
        self.set_icon_name('curlew')
        
        vbox = Gtk.VBox(spacing=6)
        self.add(vbox)

        #--- Toolbar
        toolbar = Gtk.Toolbar()
        toolbar.set_style(Gtk.ToolbarStyle.ICONS)
        toolbar.set_icon_size(Gtk.IconSize.DIALOG)
        vbox.pack_start(toolbar, False, True, 0)
        
        
        self.tb_add = create_tool_btn('add.png',
                                      'Add files',
                                      self.tb_add_clicked)
        toolbar.insert(self.tb_add, -1)
        
        self.tb_remove = create_tool_btn('remove.png',
                                         'Remove selected file',
                                         self.tb_remove_clicked)
        toolbar.insert(self.tb_remove, -1)
        
        self.tb_clear = create_tool_btn('clear.png',
                                        'Clear files list',
                                        self.tb_clear_clicked)
        toolbar.insert(self.tb_clear, -1)
        
        toolbar.insert(Gtk.SeparatorToolItem(), -1)
        
        self.tb_convert = create_tool_btn('convert.png',
                                          'Start Conversion',
                                          self.convert_cb)
        toolbar.insert(self.tb_convert, -1)
        
        self.tb_stop = create_tool_btn('stop.png',
                                       'Stop Conversion',
                                       self.tb_stop_clicked)
        toolbar.insert(self.tb_stop, -1)
        
        toolbar.insert(Gtk.SeparatorToolItem(), -1)
        
        self.tb_about = create_tool_btn('about.png',
                                        'About ' + APP_NAME,
                                        self.tb_about_clicked)
        toolbar.insert(self.tb_about, -1)
        
        toolbar.insert(Gtk.SeparatorToolItem(), -1)
        
        self.tb_quit = create_tool_btn('close.png',
                                       'Quit application',
                                       self.quit_cb)
        toolbar.insert(self.tb_quit, -1)
        
        #--- List of files
        self.store = Gtk.ListStore(bool, # active 
                                   str, # file_name
                                   str, # file_size
                                   str, # time remaining
                                   float, # progress
                                   str)     # status (progress txt)         
        self.tree = Gtk.TreeView(self.store)
        self.tree.set_has_tooltip(True)
        self.tree.set_rubber_banding(True)
        
        tree_select = self.tree.get_selection()
        tree_select.set_mode(Gtk.SelectionMode.MULTIPLE)
        
        self.tree.connect("button-press-event", self.show_popup)
        self.tree.connect("key-press-event", self.on_key_press)
        
        scroll = Gtk.ScrolledWindow()
        scroll.set_size_request(-1, 180)
        scroll.set_shadow_type(Gtk.ShadowType.IN)
        scroll.add(self.tree)
        vbox.pack_start(scroll, True, True, 0)
        
        #--- CheckButton cell
        cell = Gtk.CellRendererToggle()
        cell.connect('toggled', self.on_toggled_cb)
        col = Gtk.TreeViewColumn(None, cell, active=0)
        self.tree.append_column(col)
        
        #--- Files cell
        cell = Gtk.CellRendererText()
        col = Gtk.TreeViewColumn(_("Files"), cell, text=1)
        col.set_resizable(True)
        col.set_fixed_width(300)
        col.set_sizing(Gtk.TreeViewColumnSizing.FIXED)
        self.tree.append_column(col)
        
        #--- Size cell
        cell = Gtk.CellRendererText()
        col = Gtk.TreeViewColumn(_("Estimated size"), cell, text=2)
        col.set_fixed_width(60)
        self.tree.append_column(col)
        
        #--- Remaining time cell
        cell = Gtk.CellRendererText()
        col = Gtk.TreeViewColumn(_("Remaining time"), cell, text=3)
        col.set_resizable(True)
        self.tree.append_column(col)
        
        #--- Progress cell
        cell = Gtk.CellRendererProgress()
        col = Gtk.TreeViewColumn(_("Progress"), cell, value=4, text=5)
        col.set_resizable(True)
        col.set_min_width(80)
        self.tree.append_column(col)

        #--- Popup menu
        self.popup = Gtk.Menu()
        remove_item = Gtk.MenuItem(_('Remove'))
        remove_item.connect('activate', self.tb_remove_clicked)
        
        play_item = Gtk.MenuItem(_('Play'))
        play_item.connect('activate', self.on_play_cb)
        
        browse_item = Gtk.MenuItem(_('Browse destination'))
        browse_item.connect('activate', self.on_browse_cb)
        
        preview_item = Gtk.MenuItem(_('Preview before converting'))
        preview_item.connect('activate', self.on_preview_cb)
        
        self.popup.append(play_item)
        self.popup.append(preview_item)
        self.popup.append(remove_item)
        self.popup.append(browse_item)
        self.popup.show_all()
        
        #--- Output formats
        self.cb_formats = Gtk.ComboBoxText()
        self.cb_formats.set_entry_text_column(0)
        self.cb_formats.connect('changed', self.on_cb_formats_changed)
        hl = LabeledHBox(_("<b>Format:</b>"), vbox)
        hl.pack_start(self.cb_formats, True, True, 0)
        
        #--- Destination
        self.e_dest = Gtk.Entry()
        self.e_dest.set_text(HOME)
        self.b_dest = Gtk.Button(' ... ')
        self.b_dest.set_size_request(30, -1)
        self.cb_same_dest = Gtk.CheckButton(_('Source Path'))
        self.cb_same_dest.connect('toggled', self.cb_same_dest_cb)
        self.b_dest.connect('clicked', self.on_dest_clicked)     
        hl = LabeledHBox(_('<b>Destination:</b>'), vbox)
        hl.pack_start(self.e_dest, True, True, 0)
        hl.pack_start(self.b_dest, False, True, 0)
        hl.pack_start(self.cb_same_dest, False, True, 0)
        
        #--- Quality (low, medium, high)
        self.cb_quality = Gtk.ComboBoxText()
        map(self.cb_quality.append_text,
            [_("Low Quality"), _("Normal Quality"), _("High Quality")])
        self.cb_quality.set_active(1)
        self.cb_quality.connect('changed', self.on_cb_quality_changed)
        hl = LabeledHBox(_('<b>Quality:</b>'), vbox)
        hl.pack_start(self.cb_quality, True, True, 0)
        
        #-- Use same quality as source file
        self.cb_same_qual = Gtk.CheckButton(_('Source Quality'))
        self.cb_same_qual.set_tooltip_text(_('Use the same quality as source file'))
        self.cb_same_qual.connect('toggled', self.on_cb_same_qual_toggled)
        hl.pack_start(self.cb_same_qual, False, False, 0)
        
        #--- advanced options
        self.exp_advanced = Gtk.Expander(label=_("<b>Advanced</b>"))
        self.exp_advanced.set_use_markup(True)
        self.exp_advanced.set_resize_toplevel(True)
        vbox.pack_start(self.exp_advanced, False, True, 0)
        
        note = Gtk.Notebook()
        self.exp_advanced.add(note)
        
        #--- audio page
        self.vb_audio = Gtk.VBox()
        self.vb_audio.set_border_width(6)
        self.vb_audio.set_spacing(6)
        note.append_page(self.vb_audio, Gtk.Label(_("Audio")))
       
        self.c_abitrate = LabeledComboEntry(self.vb_audio, _("Audio Bitrate"))
        self.c_afreq = LabeledComboEntry(self.vb_audio, _("Audio Frequency"))
        self.c_ach = LabeledComboEntry(self.vb_audio, _("Audio Channels"))
        self.c_acodec = LabeledComboEntry(self.vb_audio, _("Audio Codec"))
        
        self.vb_audio.pack_start(Gtk.Separator(), False, False, 0)
        
        # Audio quality for ogg
        self.hb_aqual = LabeledHBox(_('Audio Quality'), self.vb_audio, 14)
        self.a_scale = CustomHScale(self.hb_aqual, 3, 0, 10)
        
        
        #--- video page
        self.vb_video = Gtk.VBox()
        self.vb_video.set_border_width(6)
        self.vb_video.set_spacing(6)
        note.append_page(self.vb_video, Gtk.Label(_("Video")))
        
        self.c_vbitrate = LabeledComboEntry(self.vb_video, _("Video Bitrate"))
        self.c_vfps = LabeledComboEntry(self.vb_video, _("Video FPS"))
        self.c_vsize = LabeledComboEntry(self.vb_video, _("Video Size"))
        self.c_vcodec = LabeledComboEntry(self.vb_video, _("Video Codec"))
        self.c_vratio = LabeledComboEntry(self.vb_video, _("Aspect Ratio"))
        
        self.vb_video.pack_start(Gtk.Separator(), False, False, 0)
        
        # Video quality for ogv
        self.hb_vqual = LabeledHBox(_('Video Quality'), self.vb_video, 14)
        self.v_scale = CustomHScale(self.hb_vqual, 5, 0, 20)
        
        #--- Subtitle page
        self.vb_sub = Gtk.VBox()
        self.vb_sub.set_border_width(6)
        self.vb_sub.set_spacing(6)
        note.append_page(self.vb_sub, Gtk.Label(_("Subtitle")))
        
        #--- Sub Active/Desactive
        self.cb_sub = Gtk.CheckButton(_('Use subtitle'))
        self.cb_sub.connect('toggled', self.cb_sub_toggled)
        self.vb_sub.pack_start(self.cb_sub, False, False, 0)
        
        #--- Subtitle filename
        self.hb_sub = LabeledHBox(_('Subtitle: '), self.vb_sub, 9)
        self.entry_sub = Gtk.Entry()
        self.hb_sub.pack_start(self.entry_sub, True, True, 0)
        self.hb_sub.set_sensitive(False)
        
        b_enc = Gtk.Button(' ... ')
        b_enc.set_size_request(30, -1)
        self.hb_sub.pack_start(b_enc, False, False, 0)
        b_enc.connect('clicked', self.b_enc_cb)
        
        #--- Subtitle font
        self.hb_font = LabeledHBox(_('Font: '), self.vb_sub, 9)
        self.b_font = Gtk.FontButton()
        self.hb_font.pack_start(self.b_font, True, True, 0)
        self.b_font.set_font_name('Arial 12')
        self.b_font.set_show_size(False)
        self.b_font.set_show_style(False)
        
        self.hb_font.set_sensitive(False)
        
        hbox = Gtk.HBox()
        hbox.set_spacing(30)
        
        #--- Subtitle position
        self.hb_pos = LabeledHBox(_('Position: '), hbox, 9)
        adj = Gtk.Adjustment(100, 0, 100, 2)
        self.spin_pos = Gtk.SpinButton()
        self.spin_pos.set_adjustment(adj)
        self.hb_pos.pack_start(self.spin_pos, True, True, 0)
        self.hb_pos.set_sensitive(False)
        
        #--- Subtitle size
        self.hb_size = LabeledHBox(_('Size: '), hbox, 0)
        adj = Gtk.Adjustment(4, 0, 100, 1)
        self.spin_size = Gtk.SpinButton()
        self.spin_size.set_adjustment(adj)
        self.hb_size.pack_start(self.spin_size, True, True, 0)
        self.hb_size.set_sensitive(False)
        
        self.vb_sub.pack_start(hbox, False, False, 0)
        
        #--- Subtitle Encoding
        enc = ['cp1250', 'cp1252', 'cp1253', 'cp1254',
               'cp1255', 'cp1256', 'cp1257', 'cp1258',
               'iso-8859-1', 'iso-8859-2', 'iso-8859-3', 'iso-8859-4',
               'iso-8859-5', 'iso-8859-6', 'iso-8859-7', 'iso-8859-8',
               'iso-8859-9', 'iso-8859-10', 'iso-8859-11', 'iso-8859-12',
               'iso-8859-13', 'iso-8859-14', 'iso-8859-15',
               'utf-7', 'utf-8', 'utf-16', 'utf-32', 'ASCII']
        self.hb_enc = LabeledHBox(_('Encoding: '), self.vb_sub, 9)
        self.combo_enc = Gtk.ComboBoxText()
        self.combo_enc.set_entry_text_column(0)
        map(self.combo_enc.append_text, enc)
        self.combo_enc.set_active(5)
        self.combo_enc.set_wrap_width(4)
        self.hb_enc.pack_start(self.combo_enc, True, True, 0)
        self.hb_enc.set_sensitive(False)
        
        #--- Other page (split,...)
        self.vb_other = Gtk.VBox()
        self.vb_other.set_border_width(6)
        self.vb_other.set_spacing(8)
        note.append_page(self.vb_other, Gtk.Label(_("Other")))
        
        #--- Split file section
        self.cb_split = Gtk.CheckButton(label=_('Split File'), active=False)
        self.cb_split.connect('toggled', self.cb_split_cb)
        self.vb_other.pack_start(self.cb_split, False, False, 0)
        self.tl_begin = TimeLayout(self.vb_other, _('Begin time: '))
        self.tl_duration = TimeLayout(self.vb_other, _('Duration: '))
        self.tl_begin.set_sensitive(False)
        self.tl_duration.set_sensitive(False)
        
        self.vb_other.pack_start(Gtk.Separator(), False, False, 0)
        
        self.cb_other = Gtk.CheckButton(label=_('Other Parameters:'), 
                                        active=False)
        self.cb_other.connect('toggled', self.on_cb_other)
        self.vb_other.pack_start(self.cb_other, False, False, 0)
        self.e_other = Gtk.Entry(sensitive=False)
        self.vb_other.pack_start(self.e_other, False, False, 0)
        
        vbox.pack_start(Gtk.Separator(), False, False, 0)
        
        #--- Status
        self.label_details = Gtk.Label()
        self.label_details.set_text('')
        vbox.pack_start(self.label_details, False, False, 0)
        
        #--- Show interface
        '''Must show interface before loading cb_formats combobox.'''
        self.show_all()
        
        #--- Load formats from format.cfg file
        self.f_file = ConfigParser()
        self.f_file.read(join(APP_DIR, 'formats.cfg'))
        map(self.cb_formats.append_text, self.f_file.sections())
        self.cb_formats.set_active(0)
        
        #--- Load saved options.
        self.load_options()
        
        #--- Drag and Drop
        targets = Gtk.TargetList.new([])
        targets.add_uri_targets((1 << 5) - 1)
        self.drag_dest_set(Gtk.DestDefaults.ALL, [], Gdk.DragAction.COPY)
        self.drag_dest_set_target_list(targets)
        self.connect('drag-data-received', self.drop_data_cb)
        
        #--- Window connections
        self.connect('destroy', Gtk.main_quit)
        self.connect('delete-event', self.on_delete)
    
    
    def on_toggled_cb(self, widget, Path):
        self.store[Path][0] = not self.store[Path][0]
    
    
    def on_cb_other(self, cb_other):
        self.e_other.set_sensitive(cb_other.get_active())
        
    def on_cb_same_qual_toggled(self, widget):
        active = widget.get_active()
        self.cb_quality.set_sensitive(not active)
        if active:
            self.vb_audio.set_sensitive(False)
            self.vb_video.set_sensitive(False)
        else:
            self.set_sensitives()
        
    
    def on_delete(self, widget, data):
        self.quit_cb(widget)
        return True
    
    def quit_cb(self, widget):
        if self.is_converting:
            ''' Press quit btn during conversion process '''
            resp = show_message(self, _('Do you want to quit Curlew and abort conversion process?'),
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
        
        self.save_options()
        Gtk.main_quit()
    
    #--- Add files
    def tb_add_clicked(self, widget):
        open_dlg = Gtk.FileChooserDialog(_("Add file"),
                                         self, Gtk.FileChooserAction.OPEN,
                                        (Gtk.STOCK_OK, 
                                         Gtk.ResponseType.OK,
                                         Gtk.STOCK_CANCEL,
                                         Gtk.ResponseType.CANCEL))
        open_dlg.set_current_folder(self.curr_open_folder)
        open_dlg.set_select_multiple(True)
        
        #--- File filters
        Filter = Gtk.FileFilter()
        Filter.set_name(_("All supported files"))
        Filter.add_mime_type("video/*")
        Filter.add_mime_type("audio/*")
        Filter.add_pattern("*.[Rr][AaMm]*")
        open_dlg.add_filter(Filter)
        
        Filter = Gtk.FileFilter()
        Filter.set_name(_("Video files"))
        Filter.add_mime_type("video/*")
        Filter.add_pattern("*.[Rr][AaMm]*")
        open_dlg.add_filter(Filter)
        
        Filter = Gtk.FileFilter()
        Filter.set_name(_("Audio files"))
        Filter.add_mime_type("audio/*")
        Filter.add_pattern("*.[Rr][AaMm]*")
        open_dlg.add_filter(Filter)
        
        Filter = Gtk.FileFilter()
        Filter.set_name(_("All files"))
        Filter.add_pattern("*")
        open_dlg.add_filter(Filter)
        
        res = open_dlg.run()
        if res == Gtk.ResponseType.OK:
            for file_name in open_dlg.get_filenames():
                self.store.append([True, file_name, None, None, 0.0,
                                   _('Ready!')])
                
            #--- Saved current folder
            self.curr_open_folder = open_dlg.get_current_folder()                
        open_dlg.destroy()
        
    
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
    
    def cb_split_cb(self, widget):
        is_checked = widget.get_active()
        self.tl_begin.set_sensitive(is_checked)
        self.tl_duration.set_sensitive(is_checked)
        
    def on_cb_formats_changed(self, widget):
        self.cb_quality.set_active(1) # return to Normal Quality
        self.fill_options()
        self.set_sensitives()
    
    def set_sensitives(self):
        section = self.cb_formats.get_active_text()
        media_type = self.f_file.get(section, 'type')

        # sens = [AudioP, VideoP, SubtitleP, QualityC, aQuality, vQuality]
        if media_type == 'audio':
            sens = [True, False, False, True, False, False]
        elif media_type == 'video':
            sens = [True, True, False, True, False, False]
        elif media_type == 'mvideo':
            sens = [True, True, True, True, False, False]
        elif media_type == 'fixed':
            sens = [False, False, False, False, False, False]
        elif media_type == 'ogg':
            sens = [True, False, False, False, True, False]
        elif media_type == 'ogv':
            sens = [True, True, False, False, True, True]
        elif media_type == 'presets':
            sens = [False, False, False, False, False, False]

        self.vb_audio.set_sensitive(sens[0])   # Audio page
        self.vb_video.set_sensitive(sens[1])   # Video page
        self.vb_sub.set_sensitive(sens[2])     # Subtitle page
        self.cb_quality.set_sensitive(sens[3]) # Quality combobox
        self.hb_aqual.set_sensitive(sens[4])   # Audio quality slider (ogg)
        self.hb_vqual.set_sensitive(sens[5])   # video Quality slider (ogv)
        
        self.cb_same_qual.set_active(False)
        is_true = not(self.f_file.get(section, 'encoder') == 'm' \
                      or media_type in ['fixed', 'presets'])
        self.cb_same_qual.set_sensitive(is_true)
        
        qual = self.f_file.has_option(section, 'aqual') \
        or self.f_file.has_option(section, 'vqual')
        self.cb_quality.set_sensitive(qual)
    
    
    #--- fill options widgets
    def fill_options(self):
        section = self.cb_formats.get_active_text()
        
        if self.f_file.has_option(section, 'extra'):
            self.cb_other.set_active(True)
            self.e_other.set_text(self.f_file.get(section, 'extra'))
        else:
            self.cb_other.set_active(False)
            self.e_other.set_text('')
            
        # For presets
        if self.f_file.has_option(section, 'cmd'):
            self.presets_cmd = self.f_file.get(section, 'cmd').split()
            return
            
        if self.f_file.has_option(section, 'abitrate'):
            li = self.f_file.get(section, 'abitrate').split()
            self.c_abitrate.set_list(li)
        
        if self.f_file.has_option(section, 'afreq'):
            li = self.f_file.get(section, 'afreq').split()
            self.c_afreq.set_list(li)
        
        if self.f_file.has_option(section, 'ach'):    
            li = self.f_file.get(section, 'ach').split()
            self.c_ach.set_list(li)
        
        if self.f_file.has_option(section, 'acodec'):
            li = self.f_file.get(section, 'acodec').split()
            self.c_acodec.set_list(li)
        
        if self.f_file.has_option(section, 'aqual'):
            aqual = self.f_file.get(section, 'aqual').split()
            self.c_abitrate.set_text(aqual[self.cb_quality.get_active()])
            
        if self.f_file.has_option(section, 'vbitrate'):
            li = self.f_file.get(section, 'vbitrate').split()
            self.c_vbitrate.set_list(li)
            
        if self.f_file.has_option(section, 'vbitrate'):
            li = self.f_file.get(section, 'vfps').split()
            self.c_vfps.set_list(li)
        
        if self.f_file.has_option(section, 'vcodec'):
            li = self.f_file.get(section, 'vcodec').split()
            self.c_vcodec.set_list(li)
            
        if self.f_file.has_option(section, 'vsize'):
            li = self.f_file.get(section, 'vsize').split()
            self.c_vsize.set_list(li)
        
        if self.f_file.has_option(section, 'vratio'):
            li = self.f_file.get(section, 'vratio').split()
            self.c_vratio.set_list(li)
        
        if self.f_file.has_option(section, 'vqual'):
            vqual = self.f_file.get(section, 'vqual').split()
            self.c_vbitrate.set_text(vqual[self.cb_quality.get_active()])
        
            
        
    
    def build_avconv_cmd(self,
                         input_file, out_file,
                         start_pos= -1, part_dura= -1):
        '''
        start_pos <=> -ss, part_dura <=> -t
        '''
        section = self.cb_formats.get_active_text()
        media_type = self.f_file.get(section, 'type')
        
        cmd = ['avconv', '-y']#, '-xerror']
        cmd.extend(["-i", input_file])
        
        # Force format
        if self.f_file.has_option(section, 'ff'):
            cmd.extend(['-f', self.f_file.get(section, 'ff')])
            
        # Extract Audio
        if media_type in ['audio', 'ogg']:
            cmd.append('-vn')
        
        # Use the same quality
        if self.cb_same_qual.get_active():
            cmd.append('-same_quant')
        else:
        
                
            # Video opts
            if media_type == 'video':
                # Video bitrate
                if self.c_vbitrate.get_text() != 'default':
                    cmd.extend(['-vb', self.c_vbitrate.get_text()])
                # Video FPS
                if self.c_vfps.get_text() != 'default':
                    cmd.extend(['-r', self.c_vfps.get_text()])
                # Video codec
                if self.c_vcodec.get_text() != 'default':
                    cmd.extend(['-vcodec', self.c_vcodec.get_text()])
                # Video size
                if self.c_vsize.get_text() != 'default':
                    cmd.extend(['-s', self.c_vsize.get_text()])
                # Video aspect ratio    
                if self.c_vratio.get_text() == 'default':
                    #-- force aspect ratio
                    if self.c_vcodec.get_text() in ['libxvid', 'mpeg4', 'h263']:
                        cmd.extend(['-aspect', get_aspect_ratio(input_file)])
                else:
                    cmd.extend(['-aspect', self.c_vratio.get_text()])
    
            # Audio
            if media_type in ['audio', 'video', 'ogg', 'ogv']:
                # Audio bitrate
                if self.c_abitrate.get_text() != 'default':
                    cmd.extend(['-ab', self.c_abitrate.get_text()])
                # Audio Freq.
                if self.c_afreq.get_text() != 'default':
                    cmd.extend(['-ar', self.c_afreq.get_text()])
                # Audio channel
                if self.c_ach.get_text() != 'default':
                    cmd.extend(['-ac', self.c_ach.get_text()])
                
                # Audio codec
                if self.c_acodec.get_text() != 'default':
                    cmd.extend(['-acodec', self.c_acodec.get_text()])

            # Ogg format
            if media_type in ['ogg', 'ogv']:
                cmd.extend(['-aq', str(self.a_scale.get_value())])
            
            # ogv format
            if media_type == 'ogv':
                cmd.extend(['-qscale', str(self.v_scale.get_value())])
            
            #--- Extra options (add other specific options if exist)
            if self.cb_other.get_active():
                cmd.extend(self.e_other.get_text().split())
        
        
        # Fixed opts
        if media_type == 'fixed':
            target = self.f_file.get(section, 'target')
            cmd.extend(['-target', target])
        
        # Presets formats
        elif media_type == 'presets':
            cmd.extend(self.presets_cmd)
            
        
        # Split file
        if start_pos != -1 and part_dura != -1:
            cmd.extend(['-ss', start_pos])
            cmd.extend(['-t', part_dura])
            
        #--- Last
        cmd.append(out_file)
        print(' '.join(cmd)) # print command line
        return cmd
    
    
    #--- MEncoder cmd
    def build_mencoder_cmd(self, input_file, out_file):
        section = self.cb_formats.get_active_text()
        
        cmd = ['mencoder']
        
        #--- input and output files
        cmd.append(input_file)
        cmd.extend(['-o', out_file])
        cmd.append('-noskip')
        
        #--- Sub font
        if self.cb_sub.get_active():
            cmd.extend(['-sub', self.entry_sub.get_text()]) # subtitle file
            cmd.append('-fontconfig') # configure font
            font_name = extract_font_name(self.b_font.get_font_name())
            cmd.extend(['-subfont', font_name])
            cmd.extend(['-subfont-text-scale',
                        str(self.spin_size.get_value_as_int())])
            cmd.extend(['-subpos', str(self.spin_pos.get_value_as_int())])
            cmd.extend(['-subcp', self.combo_enc.get_active_text()])
            # RTL language (Arabic)
            cmd.append('-flip-hebrew') 
            cmd.append('-noflip-hebrew-commas')
        
        #--- Audio codec and opts
        cmd.extend(['-oac', self.c_acodec.get_text()])
        # No more audio options with 'copy'
        if self.c_acodec.get_text() == 'copy':
            pass
        else:
            a_opts = []
            #--- for mp3lame codec
            if self.c_acodec.get_text() == 'mp3lame':
                cmd.append('-lameopts')
                # Use constant bitrate
                a_opts.append('cbr') 
                # Audio channels
                a_opts.append('mode={}'.format(self.c_ach.get_text())) 
                # Audio bitrate
                a_opts.append('br={}'.format(self.c_abitrate.get_text()))
            #--- for faac audio codec
            elif self.c_acodec.get_text() == 'faac':
                cmd.append('-faacopts')
                # bitrate
                a_opts.append('br={}'.format(self.c_abitrate.get_text()))
            #--- for libavcodec
            elif self.c_acodec.get_text() == 'lavc':
                cmd.append('-lavcopts')
                a_opts.append('abitrate={}'.format(self.c_abitrate.get_text()))
                a_opts.append('acodec=aac')
                
            #--- append cmd with audio opts
            cmd.append(':'.join(a_opts))
            
        #--- Video codec and opts
        cmd.extend(['-ovc', self.c_vcodec.get_text()])
        #--- for xvid video codec
        if self.c_vcodec.get_text() == 'xvid':
            cmd.append('-xvidencopts')
            v_opts = []
            v_opts.append('bitrate={}'.format(self.c_vbitrate.get_text()))
            cmd.append(':'.join(v_opts))
        
        
        #--- for libavcodec video opts
        elif self.c_vcodec.get_text() == 'lavc':
            cmd.append('-lavcopts')
            v_opts = []
            v_opts.append('vbitrate={}'.format(self.c_vbitrate.get_text()))
            cmd.append(':'.join(v_opts))
            if self.f_file.has_option(section, 'opts'):
                cmd.extend(self.f_file.get(section, 'opts').split())
        
        #--- split file (encode part of file)
        if self.cb_split.get_active():
            # begin time
            cmd.extend(['-ss', self.tl_begin.get_time_str()])
            # duration
            cmd.extend(['-endpos', self.tl_duration.get_time_str()])
        
        #--- video size
        if self.c_vsize.get_text() != 'default':
            cmd.append('-vf')
            cmd.append('scale={},harddup'.format(self.c_vsize.get_text()))
        
        #print(' '.join(cmd))
        return cmd

    #--- Convert funtcion
    def convert_cb(self, widget):
        if len(self.store) == 0 or self.is_converting:
            return
        
        if self.f_file.get(self.cb_formats.get_active_text(), 'encoder') == 'None':
            return
        
        # Return if invalid path or inaccessible
        Accessible = os.access(self.e_dest.get_text(), os.W_OK)
        ValidDir = isdir(self.e_dest.get_text())
        if not ValidDir:
            show_message(self, _('Destination path is not valid.'),
                              Gtk.MessageType.ERROR)
            return
        if not Accessible:
            show_message(self, _('Destination path is not accessible.'),
                              Gtk.MessageType.ERROR)
            return
        
        self.Iter = self.store.get_iter_first()
        self.output_details = ''
        self.is_converting = True
        self.convert_file()
        

    def convert_file(self):
        ext = self.f_file.get(self.cb_formats.get_active_text(), 'ext')
        encoder_type = self.f_file.get(self.cb_formats.get_active_text(),
                                       'encoder')
        
        #--- Check
        if self.Iter != None:
            
            #--- Do not convert this file
            if self.store[self.Iter][0] == False:
                self.store[self.Iter][5] = _("Skipped!")
                # Jump to next file
                self.Iter = self.store.iter_next(self.Iter)
                self.convert_file()
                return
                     
            #--- get input and output files
            input_file = self.store[self.Iter][1]
            part = splitext(basename(input_file))[0] + '.' + ext
            
            # Same destination as source file
            if self.cb_same_dest.get_active():
                out_file = join(os.path.dirname(input_file), part)
            # Use entry destination path
            else:
                out_file = join(self.e_dest.get_text(), part)
            
            #--- Rename output file if has the same name as input file
            if input_file == out_file:
                out_file = out_file[:-4] + '~.' + ext
                
            self.out_file = out_file
            
            #--- If output file already exist
            if os.path.exists(out_file):
                res = show_message(self,
                                   _("File: <b>{}</b> already exist.\nOverwrite it?".format(out_file)),
                                   Gtk.MessageType.WARNING,
                                   Gtk.ButtonsType.YES_NO)
                
                # Overwrite this file
                if res == Gtk.ResponseType.YES:
                    # delete existed file first
                    self.force_delete_file(out_file)
                #--- Skipped this file
                else:
                    self.store[self.Iter][5] = _('Skipped!')
                    # Jump to next file
                    self.Iter = self.store.iter_next(self.Iter)
                    self.convert_file()
                    return
        
            #--- which encoder use (avconv of mencoder)
            if encoder_type == 'f':
                if self.cb_split.get_active():
                    full_cmd = self.build_avconv_cmd(input_file, out_file,
                                                 self.tl_begin.get_time_str(),
                                                 self.tl_duration.get_time_str())
                else:
                    full_cmd = self.build_avconv_cmd(input_file, out_file)
                    
            elif encoder_type == 'm':
                full_cmd = self.build_mencoder_cmd(input_file, out_file)
            
            #--- Total file duration
            self.total_duration = self.get_duration(input_file)
            
            #---  To be converted duration
            if self.cb_split.get_active():
                self.total_duration = self.tl_duration.get_duration()
            
            # Stored start time
            self.begin_time = time.time() 
            
            #--- Start the process
            self.fp = Popen(full_cmd,
                            stdout=PIPE,
                            stderr=PIPE,
                            universal_newlines=True,
                            bufsize= -1)
            #--- Watch stdout and stderr
            GLib.io_add_watch(self.fp.stdout, GLib.IO_IN | GLib.IO_HUP,
                              self.on_output, encoder_type, out_file)
            GLib.io_add_watch(self.fp.stderr, GLib.IO_IN | GLib.IO_HUP,
                              self.on_output, encoder_type, out_file)
            #--- On end process
            GLib.child_watch_add(self.fp.pid, self.on_end, out_file)
        
        else:
            self.is_converting = False
    
    #--- Stop conversion cb
    def tb_stop_clicked(self, widget):
        if self.is_converting == True:
            resp = show_message(self,
                                _('Do you want to stop conversion process?'),
                                Gtk.MessageType.QUESTION,
                                Gtk.ButtonsType.YES_NO)
            if resp == Gtk.ResponseType.YES and self.is_converting == True:
                try:
                    self.fp.kill()
                    self.fp.terminate()
                except OSError as err:
                    print(err) 
                finally:
                    self.is_converting = False
                    
    
    def get_duration(self, input_file):
        ''' Get duration file in seconds (float)'''
        duration = 0.0
        cmd = ['avconv', '-i', input_file]
        Proc = Popen(cmd, stdout=PIPE, stderr=PIPE)
        out_str = Proc.stderr.read()
        try:
            time_list = self.reg_duration.findall(out_str)[0].split(':')
        except:
            return duration
        duration = int(time_list[0]) * 3600 + int(time_list[1]) * 60 + \
        float(time_list[2])
        return duration
    
    
    #---- Quality callback
    def on_cb_quality_changed(self, widget):
        quality_index = self.cb_quality.get_active()
        section = self.cb_formats.get_active_text()
        self.set_sensitives()
        
        if self.f_file.has_option(section, 'aqual'):
            aqual = self.f_file.get(section, 'aqual').split()
            self.c_abitrate.set_text(aqual[quality_index])
        
        if self.f_file.has_option(section, 'vqual'):
            vqual = self.f_file.get(section, 'vqual').split()
            self.c_vbitrate.set_text(vqual[quality_index])
    
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
        dlg.add_filter(Filter)
        res = dlg.run()
        if res == Gtk.ResponseType.OK:
            self.entry_sub.set_text(dlg.get_filename())
        dlg.destroy()
    
    #--- Remove item
    def tb_remove_clicked(self, widget):
        iters = self.get_selected_iters()
        if not iters:
            return      
        elif self.is_converting:
            for Iter in iters:
                if self.store[Iter][:] != self.store[self.Iter][:]:
                    self.store.remove(Iter)
        else:
            map(self.store.remove, iters)
    
    def get_selected_iters(self):
        ''' Get a list contain selected iters '''
        model, tree_path = self.tree.get_selection().get_selected_rows()
        iters = []
        if not tree_path:
            return iters
        for path in tree_path:
            iters.append(model.get_iter(path))
        return iters
    
    def on_play_cb(self, widget):
        Iter = self.get_selected_iters()[0]
        call(['xdg-open', self.store[Iter][1]])
        
    def on_browse_cb(self, widget):
        if self.cb_same_dest.get_active():
            Iter = self.get_selected_iters()[0]
            call(['xdg-open', dirname(self.store[Iter][1])])
        else:
            call(['xdg-open', self.e_dest.get_text()])

        
    
    def on_preview_cb(self, widget):
        encoder_type = self.f_file.get(self.cb_formats.get_active_text(),
                                       'encoder')
        Iter = self.get_selected_iters()[0]
        input_file = self.store[Iter][1]
        out_file = '/tmp/Preview'
        duration = self.get_duration(input_file)
        preview_begin = str(duration / 10)
        #
        if encoder_type == 'f':
            cmd = (self.build_avconv_cmd(input_file, out_file,
                                         preview_begin, '10'))
        elif encoder_type == 'm':
            cmd = self.build_mencoder_cmd(input_file, out_file)
            cmd.extend(['-ss', preview_begin])
            cmd.extend(['-endpos', '10'])
        
        self.fp = Popen(cmd,
                        stdout=PIPE, stderr=PIPE,
                        universal_newlines=True, bufsize= -1)
        noti = show_notification(APP_NAME, '',
                                 _('Please wait while preparing preview...'),
                                 'dialog-information')
        GLib.child_watch_add(self.fp.pid, self.on_end_preview,
                             (out_file, noti))
        self.set_sensitive(False)
    
    def on_end_preview(self, pid, code, data):
        if code == 0:
            call(['xdg-open', data[0]])
        self.set_sensitive(True)
        data[1].close()
    
    #--- Clear list    
    def tb_clear_clicked(self, widget):
        if not self.is_converting:
            self.store.clear()
        
    def tb_about_clicked(self, widget):
        a_dgl = About(self)
        a_dgl.show()
        
    def cb_sub_toggled(self, widget):
        self.hb_sub.set_sensitive(widget.get_active())
        self.hb_enc.set_sensitive(widget.get_active())
        self.hb_font.set_sensitive(widget.get_active())
        self.hb_pos.set_sensitive(widget.get_active())
        self.hb_size.set_sensitive(widget.get_active())
    
    #--- Remove selected items.
    def on_key_press(self, widget, event):
        if event.keyval == Gdk.KEY_Delete:
            self.tb_remove_clicked(None)
            
    def show_popup(self, widget, event):
        treepath = self.tree.get_selection().get_selected_rows()[1]
        if event.button == 3 and len(treepath) != 0:
            self.popup.show_all()
            self.popup.popup(None, None, None, None, 3,
                             Gtk.get_current_event_time())
        
    
    #---- On end conversion
    def on_end(self, pid, err_code, out_file):
        if self.Iter != None:
            # Converion succeed
            if err_code == 0:
                self.store[self.Iter][0] = False
                self.store[self.Iter][4] = 100.0
                self.store[self.Iter][5] = _("Done!")
                # Convert the next file
                self.Iter = self.store.iter_next(self.Iter)
                self.convert_file()
            
            # Converion failed
            elif err_code == 256:
                self.store[self.Iter][5] = _("Failed!")
                self.force_delete_file(out_file)
                
                # FIXME: write log
                print(self.output_details)
                
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
        
    
    #--- Catch output 
    def on_output(self, source, condition, encoder_type, out_file):
        
        #--- Allow interaction with application widgets.
        while Gtk.events_pending():
            Gtk.main_iteration()
        
        if self.Iter == None:
            return False
        
        #--- Skipped file during conversion (unckecked file during conversion)
        if self.store[self.Iter][0] == False:
            self.store[self.Iter][5] = _("Skipped!")
            self.fp.kill()
            # Delete the file
            self.force_delete_file(out_file)
            # Jump to next file
            self.Iter = self.store.iter_next(self.Iter)
            self.convert_file()
            return False
        
        line = source.readline()
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
                    
                    # Formating estimated size
                    size_str = get_format_size(est_size)
                    
                    #--- Calculate remaining time.
                    cur_time = time.time() - self.begin_time
                    try:
                        rem_dur = ((cur_time * self.total_duration) / elapsed_time) - cur_time
                    except ZeroDivisionError:
                        rem_dur = 0
                    
                    #--- Convert duration (sec) to time (00:00:00)
                    rem_time = duration_to_time(rem_dur)
                    
                    self.store[self.Iter][2] = size_str                        # estimated size
                    self.store[self.Iter][3] = rem_time                        # remaining time
                    self.store[self.Iter][4] = float(time_ratio * 100)         # progress value
                    self.store[self.Iter][5] = '{:.2%}'.format(time_ratio)     # progress text
            
            # mencoder progress
            if encoder_type == 'm':
                begin = line.find('Pos:')
                if begin != -1:
                    self.label_details.set_text(line.strip())
                    
                    #--- File size
                    file_size = self.reg_menc.findall(line)[0][2]
                    self.store[self.Iter][2] = file_size + ' MB'
                    
                    #--- Remaining time
                    dur = self.reg_menc.findall(line)[0][0]
                    rem_dur = self.total_duration - float(dur)
                    rem_time = duration_to_time(rem_dur)
                    self.store[self.Iter][3] = rem_time
                    
                    #--- Progress
                    progress_value = float(self.reg_menc.findall(line)[0][1])
                    self.store[self.Iter][4] = progress_value
                    self.store[self.Iter][5] = '{:.2f}%'.format(progress_value)
            
            #--- Append conversion details 
            self.output_details += line
            return True
        # When len(line) == 0
        return False

    
    #--- Drag and drop callback
    def drop_data_cb(self, widget, dc, x, y, selection_data, info, t):
        for i in selection_data.get_uris():
            if i.startswith('file://'):
                File = unquote(i[7:])
                if os.path.isfile(File):
                    self.store.append([True, File, None, None, 0.0,
                                       _('Ready!')])
                # Save directory from dragged filename.
                self.curr_open_folder = dirname(File)
    
    def cb_same_dest_cb(self, widget):
        Active = not widget.get_active()
        self.e_dest.set_sensitive(Active)
        self.b_dest.set_sensitive(Active)
    
    def force_delete_file(self, file_name):
        ''' Force delete file_name '''
        while os.path.exists(file_name):
            try:
                os.unlink(file_name)
            except OSError:
                continue
    
    def save_options(self):
        conf = ConfigParser()
        conf.read(self.opts_file)
        
        if not conf.has_section('configs'):
            conf.add_section('configs')
        
        conf.set('configs', 'curr_open_folder', self.curr_open_folder)
        conf.set('configs', 'curr_save_folder', self.curr_save_folder)
        conf.set('configs', 'e_dest_text', self.e_dest.get_text())
        conf.set('configs', 'cb_format_ind', self.cb_formats.get_active())
        conf.set('configs', 'cb_same_dest_on', self.cb_same_dest.get_active())
        conf.set('configs', 'cb_same_qual_on', self.cb_same_qual.get_active())
        
        files_list = []
        for i in range(len(self.store)):
            files_list.append(self.store[i][:])
        conf.set('configs', 'files_list', files_list)
        
        with open(self.opts_file, 'w') as configfile:
            conf.write(configfile)
        
        
    
    def load_options(self):
        conf = ConfigParser()
        conf.read(self.opts_file)
        
        try:
            self.curr_open_folder = conf.get('configs', 'curr_open_folder')
        except:
            self.curr_open_folder = HOME
        try:
            self.curr_save_folder = conf.get('configs', 'curr_save_folder')
        except:
            self.curr_save_folder = HOME
        try:
            self.e_dest.set_text(conf.get('configs', 'e_dest_text'))
            self.cb_formats.set_active(conf.getint('configs', 'cb_format_ind'))
            self.cb_same_dest.set_active(conf.getboolean('configs',
                                                         'cb_same_dest_on'))
            self.cb_same_qual.set_active(conf.getboolean('configs',
                                                            'cb_same_qual_on'))
            for r in eval(conf.get('configs', 'files_list')):
                self.store.append(r)
        except NoOptionError as err:
            print(err)
        except NoSectionError as err:
            print(err)


def main():
    Curlew()
    Gtk.main()

if __name__ == '__main__':
    main()
