#!/usr/bin/env python
#-*- coding:utf-8 -*-


#===============================================================================
# Application : Curlew multimedia converter
# Author: Chamekh Fayssal <chamfay@gmail.com>
# License: Waqf license, see: http://www.ojuba.org/wiki/doku.php/waqf/license
#===============================================================================


#TODO: Add drag and drop function.
#TODO: Add 2 pass encoding.

try:
    import sys, os, string
    import time
    from subprocess import Popen, PIPE
    from os.path import basename, isdir, splitext, join
    from gi.repository import Gtk, Notify, GLib, Gdk
    from user import home
    import gettext
    import commands
    import ConfigParser, re
except Exception, detail:
    print detail
    sys.exit(1)

#--- localizations
gettext.install('curlew', 'locale')

APP_VERSION = '0.1.3'
APP_NAME = _('Curlew')

def show_message(parent, message, message_type, button_type = Gtk.ButtonsType.CLOSE):
    mess_dlg = Gtk.MessageDialog(parent,
                             Gtk.DialogFlags.MODAL,
                             message_type,
                             button_type)
    mess_dlg.set_markup(message)
    resp = mess_dlg.run()
    mess_dlg.destroy()
    return resp

def show_notification(app_name, title, text, icon):
    Notify.init(app_name)
    notification = Notify.Notification.new(title, text, icon)
    notification.show()
    return notification

def extract_font_name(font_str):
    font_str = font_str[:-3]
    styles_list = ['Bold', 'Italic', 'Oblique', 'Medium']
    for style in styles_list:
        font_str = font_str.replace(style, '')
    return font_str.strip()

def get_aspect_ratio(input_file):
    cmd = 'ffmpeg -i "' + input_file + '"'
    out_str = commands.getoutput(cmd)
    reg_aspect = re.compile('''DAR\s+(\d*:\d*)''')
    return reg_aspect.findall(out_str)[0]
        

class About(Gtk.AboutDialog):
    def __init__(self, parent):
        
        Gtk.AboutDialog.__init__(self, parent = parent, wrap_license = True)
        
        self.set_program_name(APP_NAME)
        self.set_authors(['Fayssal Chamekh <chamfay@gmail.com>'])
        self.set_copyright("Copyright © 2012 Fayssal Chamekh <chamfay@gmail.com>")
        self.set_version(APP_VERSION)
        self.set_title(APP_NAME)
        self.set_logo_icon_name('curlew')
        self.set_comments(_('Easy to use Multimedia Converter for Linux'))
        License = """    released under terms on waqf public license.
    this program is free software; you can redistribute it and/or modify it under the terms of the latest version waqf public license as published by ojuba.org.
 
    this program is distributed in the hope that it will be useful, but without any warranty; without even the implied warranty of merchantability or fitness for a particular purpose.
 
    the latest version of the license can be found on
 http://www.ojuba.org/wiki/doku.php/waqf/license"""
        self.set_license(License)
        self.set_website('https://github.com/chamfay/Curlew')
        self.set_translator_credits(_('Fayssal Chamekh <chamfay@gmail.com>'))
        self.run()
        self.destroy()

class LabeledHBox(Gtk.HBox):
    def __init__(self, Label, container = None, CWidth = 12):
        ''' hbox with label'''
        Gtk.HBox.__init__(self, spacing = 8)
        label = Gtk.Label(Label, use_markup = True)
        label.set_alignment(0, 0.5)
        label.set_width_chars(CWidth)
        self.pack_start(label, False, False, 0)
        if container != None:
            container.pack_start(self, False, False, 0)
            

class TimeLayout(Gtk.HBox):
    def __init__(self, container, Label):
        '''    Time widget    '''
        Gtk.HBox.__init__(self)
        self.__duration = 0
        self._spin_h = Gtk.SpinButton().new_with_range(0,5,1)
        self._spin_m = Gtk.SpinButton().new_with_range(0,59,1)
        self._spin_s = Gtk.SpinButton().new_with_range(0,59,1)
        
        label = Gtk.Label(Label, use_markup = True)
        label.set_alignment(0,0.5)
        label.set_width_chars(10)
        
        self.pack_start(label, False, False, 0)
        self.pack_start(self._spin_h, False, False, 0)
        self.pack_start(Gtk.Label(label = ' : '), False, False, 0)
        self.pack_start(self._spin_m, False, False, 0)
        self.pack_start(Gtk.Label(label = ' : '), False, False, 0)
        self.pack_start(self._spin_s, False, False, 0)
        container.pack_start(self, False, False, 0)
    
    def set_duration(self, duration):
        '''    Set duration in seconds    '''
        self.__duration = int(duration)
        h = duration / 3600
        m = (duration % 3600) / 60
        s = (duration % 3600) % 60
        self._spin_h.set_value(h)
        self._spin_m.set_value(m)
        self._spin_s.set_value(s)
    
    def get_duration(self):
        return self._spin_h.get_value()*3600  \
                       + self._spin_m.get_value()*60    \
                       + self._spin_s.get_value()
    
    def get_time_str(self):
        ''' Get time str like 00:00:00'''
        Str =  '%.2i:%.2i:%.2i' % (self._spin_h.get_value(),
                    self._spin_m.get_value(), 
                    self._spin_s.get_value())
        return Str
    
        
        
class LabeledComboEntry(Gtk.ComboBoxText):
    ''' Create custom ComboBoxText with entry'''
    def __init__(self, Container, Label, WithEntry = True):
        Gtk.ComboBoxText.__init__(self, has_entry = WithEntry)
        hbox = Gtk.HBox();
        hbox.set_spacing(5)
        label = Gtk.Label(Label, use_markup = True)
        label.set_alignment(0, 0.5)
        label.set_width_chars(15)
        self.set_entry_text_column(0)
        hbox.pack_start(label, False, False, 0)
        hbox.pack_start(self, False, False, 0)
        Container.pack_start(hbox, False, False, 0)
    
    def set_list(self, List):
        ''' Fill combobox with list directly [] '''
        self.remove_all()
        for i in List:
            self.append_text(i)
        self.set_active(0)
    
    def get_text(self):
        ''' Get active text in combo '''
        return self.get_active_text()
    
    def set_text(self, Text):
        ''' Set text to LabeledComboEntry return its index '''
        entry = self.get_child()
        entry.set_text(Text)

#--- Main class        
class Curlew(Gtk.Window):
     
    #--- Variables
    curr_open_folder = home
    curr_save_folder = home
    is_converting = False
    fp = None
    Iter = None
    output_details = ''
    total_duration = 0.0
    #--- Regex
    reg_ffmpeg   = re.compile('''size=\s+(\d+\.*\d*).*time=(\d+\.*\d*)''')
    reg_mencoder = re.compile('''.(\d+\.*\d*)s.*(.\d+)%.*\s+(\d+)mb''')
    reg_duration = re.compile('''Duration:.*(\d+:\d+:\d+\.\d+)''')
              
    def __init__(self):        
        Gtk.Window.__init__(self)        
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_title('%s %s' % (APP_NAME, APP_VERSION))
        self.set_border_width(6)
        self.set_size_request(680,-1)
        self.set_icon_from_file('/usr/share/icons/curlew.png')
        
        vbox = Gtk.VBox()
        vbox.set_spacing(6)
        self.add(vbox)

        #--- Toolbar
        toolbar = Gtk.Toolbar()
        toolbar.set_style(Gtk.ToolbarStyle.ICONS)
        toolbar.set_icon_size(Gtk.IconSize.DIALOG)
        vbox.pack_start(toolbar, False, True, 0)
        
        self.tb_add = Gtk.ToolButton(icon_widget = Gtk.Image.new_from_file('data/add.svg'))
        self.tb_add.set_tooltip_text(_('Add files'))
        self.tb_add.connect("clicked", self.tb_add_clicked)
        toolbar.insert(self.tb_add,-1)
        
        self.tb_remove = Gtk.ToolButton(icon_widget = Gtk.Image.new_from_file('data/remove.svg'))
        self.tb_remove.set_tooltip_text(_('Remove selected file'))
        self.tb_remove.connect('clicked', self.tb_remove_clicked)
        toolbar.insert(self.tb_remove,-1)
        
        self.tb_clear = Gtk.ToolButton(icon_widget = Gtk.Image.new_from_file('data/clear.svg'))
        self.tb_clear.set_tooltip_text(_('Clear files list'))
        self.tb_clear.connect('clicked', self.tb_clear_clicked)
        toolbar.insert(self.tb_clear,-1)
        
        toolbar.insert(Gtk.SeparatorToolItem(),-1)
        
        self.tb_convert = Gtk.ToolButton(icon_widget = Gtk.Image.new_from_file('data/convert.svg'))
        self.tb_convert.set_tooltip_text(_('Start Conversion'))
        self.tb_convert.connect('clicked', self.convert_cb)
        toolbar.insert(self.tb_convert,-1)
        
        
        self.tb_stop = Gtk.ToolButton(icon_widget = Gtk.Image.new_from_file('data/stop.svg'))
        self.tb_stop.set_tooltip_text(_('Stop Conversion'))
        self.tb_stop.connect('clicked', self.tb_stop_clicked)
        toolbar.insert(self.tb_stop,-1)
        
        toolbar.insert(Gtk.SeparatorToolItem(),-1)
        
        self.tb_about = Gtk.ToolButton(icon_widget = Gtk.Image.new_from_file('data/about.svg'))
        self.tb_about.set_tooltip_text(_('About ') + APP_NAME)
        self.tb_about.connect("clicked", self.tb_about_clicked)
        toolbar.insert(self.tb_about,-1)
        
        toolbar.insert(Gtk.SeparatorToolItem(),-1)
        
        self.tb_quit = Gtk.ToolButton(icon_widget = Gtk.Image.new_from_file('data/close.svg'))
        self.tb_quit.set_tooltip_text(_('Quit application'))
        self.tb_quit.connect("clicked", self.quit_cb)
        toolbar.insert(self.tb_quit,-1)
        
        #--- List of files
        self.store = Gtk.ListStore(bool,    # active 
                                   str,     # file_name
                                   str,     # file_size
                                   str,     # time remaining
                                   float,   # progress
                                   str)     # status (progress txt)         
        self.tree = Gtk.TreeView(self.store)
        self.tree.get_selection().set_mode(Gtk.SelectionMode.MULTIPLE)
        self.tree.set_rubber_banding(True)
        self.tree.connect("button-press-event", self.show_popup)
        self.tree.connect("key-press-event", self.delete_file)
        scroll = Gtk.ScrolledWindow()
        scroll.set_size_request(-1, 180)
        scroll.set_shadow_type(Gtk.ShadowType.IN)
        scroll.add(self.tree)
        vbox.pack_start(scroll, True, True, 0)
        
        #--- Active cell
        cell = Gtk.CellRendererToggle()
        cell.connect('toggled', self.toggled_cb)
        col = Gtk.TreeViewColumn(None, cell, active = 0)
        self.tree.append_column(col)
        
        #--- Files cell
        cell = Gtk.CellRendererText()
        col = Gtk.TreeViewColumn(_("Files"), cell, text = 1)
        col.set_resizable(True)
        col.set_fixed_width(300)
        col.set_sizing(Gtk.TreeViewColumnSizing.FIXED)
        self.tree.append_column(col)
        
        #--- Size cell
        cell = Gtk.CellRendererText()
        col = Gtk.TreeViewColumn(_("Estimated size"), cell, text = 2)
        col.set_fixed_width(60)
        self.tree.append_column(col)
        
        #--- Remaining time cell
        cell = Gtk.CellRendererText()
        col = Gtk.TreeViewColumn(_("Remaining time"), cell, text = 3)
        col.set_resizable(True)
        self.tree.append_column(col)
        
        #--- Progress cell
        cell = Gtk.CellRendererProgress()
        col = Gtk.TreeViewColumn(_("Progress"), cell, value = 4, text = 5)
        col.set_resizable(True)
        col.set_min_width(80)
        self.tree.append_column(col)

        #--- Popup menu
        self.popup = Gtk.Menu()
        remove_item = Gtk.MenuItem(_('Remove'))
        remove_item.connect('activate', self.tb_remove_clicked)
        
        play_item = Gtk.MenuItem(_('Play'))
        play_item.connect('activate', self.on_play_cb)
        
        preview_item = Gtk.MenuItem(_('Preview before converting'))
        preview_item.connect('activate', self.on_preview_cb)
         
        self.popup.append(remove_item)
        self.popup.show_all()
        self.popup.add(Gtk.SeparatorMenuItem())
        self.popup.append(play_item)
        self.popup.append(preview_item)
        
        #--- conversion formats
        self.cb_formats = Gtk.ComboBoxText()
        self.cb_formats.set_entry_text_column(0)
        self.cb_formats.set_wrap_width(3)
        self.cb_formats.connect('changed', self.on_cb_formats_changed)
        hl = LabeledHBox(_("<b>Format:</b>"), vbox)
        hl.pack_start(self.cb_formats, True, True, 0)
        
        #--- destination
        self.e_dest = Gtk.Entry()
        self.e_dest.set_text(home)
        self.b_dest = Gtk.Button(' ... ')
        self.b_dest.connect('clicked', self.on_dest_clicked)     
        hl = LabeledHBox(_('<b>Destination:</b>'), vbox)
        hl.pack_start(self.e_dest, True, True, 0)
        hl.pack_start(self.b_dest, False, True, 0)
        
        #--- quality
        self.cb_quality = Gtk.ComboBoxText()
        for quality in (_("Low Quality"), _("Normal Quality"), _("High Quality")):
            self.cb_quality.append_text(quality)
        self.cb_quality.set_active(1)
        self.cb_quality.connect('changed', self.on_cb_quality_changed)
        hl = LabeledHBox(_('<b>Quality:</b>'), vbox)
        hl.pack_start(self.cb_quality, True, True, 0)
        
        #--- advanced options
        exp_advanced = Gtk.Expander(label = _("<b>Advanced</b>"))
        exp_advanced.set_use_markup(True)
        exp_advanced.set_resize_toplevel(True)
        vbox.pack_start(exp_advanced, False,True,0)
        
        note = Gtk.Notebook()
        exp_advanced.add(note)
        
        #--- audio page
        self.vb_audio = Gtk.VBox()
        self.vb_audio.set_border_width(6)
        self.vb_audio.set_spacing(6)
        note.append_page(self.vb_audio, Gtk.Label(_("Audio")))
       
        self.c_abitrate = LabeledComboEntry(self.vb_audio, _("Audio Bitrate"))
        self.c_afreq = LabeledComboEntry(self.vb_audio, _("Audio Frequency"))
        self.c_ach = LabeledComboEntry(self.vb_audio, _("Audio Channels"))
        self.c_acodec = LabeledComboEntry(self.vb_audio, _("Audio Codec"))
        
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
        
        #--- Subtitle page
        self.vb_sub = Gtk.VBox()
        self.vb_sub.set_border_width(6)
        self.vb_sub.set_spacing(6)
        note.append_page(self.vb_sub, Gtk.Label(_("Subtitle")))
        
        #--- Sub Active/Desactive
        self.check_sub = Gtk.CheckButton(_('Use subtitle'))
        self.check_sub.connect('toggled', self.check_sub_toggled)
        self.vb_sub.pack_start(self.check_sub, False, False, 0)
        
        #--- Subtitle filename
        self.hb_sub = LabeledHBox(_('Subtitle: '), self.vb_sub, 9)
        self.entry_sub = Gtk.Entry()
        self.hb_sub.pack_start(self.entry_sub, True,True,0)
        self.hb_sub.set_sensitive(False)
        
        b_enc = Gtk.Button(' ... ')
        self.hb_sub.pack_start(b_enc, False, False, 0)
        b_enc.connect('clicked', self.b_enc_cb)
        
        #--- Subtitle font
        self.hb_font = LabeledHBox(_('Font: '), self.vb_sub, 9)
        self.b_font = Gtk.FontButton()
        self.hb_font.pack_start(self.b_font, True, True, 0)
        self.b_font.set_font_name('Arial')
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
        enc = ['cp1250','cp1252','cp1253','cp1254','cp1255','cp1256','cp1257','cp1258',
               'iso-8859-1','iso-8859-2','iso-8859-3','iso-8859-4',
               'iso-8859-5','iso-8859-6','iso-8859-7','iso-8859-8',
               'iso-8859-9','iso-8859-10','iso-8859-11','iso-8859-12',
               'iso-8859-13','iso-8859-14','iso-8859-15','utf-7','utf-8',
               'utf-16','utf-32','ASCII']
        self.hb_enc = LabeledHBox(_('Encoding: '), self.vb_sub, 9)
        self.combo_enc = Gtk.ComboBoxText()
        self.combo_enc.set_entry_text_column(0)
        for i in enc:
            self.combo_enc.append_text(i)
        self.combo_enc.set_active(5)
        self.combo_enc.set_wrap_width(4)
        self.hb_enc.pack_start(self.combo_enc, True, True, 0)
        self.hb_enc.set_sensitive(False)
        
        #--- Split page
        self.vb_comm = Gtk.VBox()
        self.vb_comm.set_border_width(6)
        self.vb_comm.set_spacing(6)
        note.append_page(self.vb_comm, Gtk.Label(_("Other")))
        
        self.check_split = Gtk.CheckButton(label = _('Split File'), active = False)
        self.check_split.connect('toggled', self.check_split_cb)
        self.vb_comm.pack_start(self.check_split, False,False,0)
        self.tl_begin = TimeLayout(self.vb_comm, _('Begin time: '))
        self.tl_duration = TimeLayout(self.vb_comm, _('Duration: '))
        self.tl_begin.set_sensitive(False)
        self.tl_duration.set_sensitive(False)
        
        
        #--- output str
        exp_details = Gtk.Expander(label = _("<b>Conversion Details</b>"))
        exp_details.set_use_markup(True)
        exp_details.set_resize_toplevel(True)
        vbox.pack_start(exp_details, False, False, 0)
        
        self.txt_buffer = Gtk.TextBuffer()
        self.view_details = Gtk.TextView(buffer = self.txt_buffer)
        self.view_details.set_editable(False)
        self.view_details.set_cursor_visible(False)
        scroll = Gtk.ScrolledWindow()
        scroll.add(self.view_details)
        scroll.set_shadow_type(Gtk.ShadowType.IN)
        exp_details.add(scroll)
        
        
        #--- Load formats
        self.f_file = ConfigParser.ConfigParser()
        self.f_file.read('formats.cfg')
        for i in self.f_file.sections():
            self.cb_formats.append_text(i)
        self.cb_formats.set_active(0)
        
        #--- Initialisation fcts
        self.fill_options()
        
        self.connect('destroy', Gtk.main_quit)
        self.connect('delete-event', self.on_delete)
        self.show_all()    
    
    def toggled_cb(self, widget, Path):
        self.store[Path][0] = not self.store[Path][0]
    
    def on_delete(self, widget, data):
        self.quit_cb(widget)
        return True
    
    def quit_cb(self, widget):
        if self.is_converting:
            return
        Gtk.main_quit()
    
    #--- add files
    def tb_add_clicked(self, widget):
        open_dlg = Gtk.FileChooserDialog(_("Add file"), self,
                                        Gtk.FileChooserAction.OPEN,
                                        (Gtk.STOCK_OK, Gtk.ResponseType.OK,
                                        Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL))
        open_dlg.set_current_folder(self.curr_open_folder)
        open_dlg.set_select_multiple(True)
        
        #----Filter
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
                
                self.store.append( [True, file_name, None, None, 0.0, _('Ready!')])
                
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
    
    def check_split_cb(self, widget):
        is_checked = widget.get_active()
        self.tl_begin.set_sensitive(is_checked)
        self.tl_duration.set_sensitive(is_checked)
        
    def on_cb_formats_changed(self, widget):
        self.fill_options()
    
    #--- fill options widgets
    def fill_options(self):
        section = self.cb_formats.get_active_text()
        media_type = self.f_file.get(section, 'type')
        
        #--- general audios
        if media_type == 'audio':
            self.vb_audio.set_sensitive(True)
            self.vb_video.set_sensitive(False)
            self.vb_sub.set_sensitive(False)
            self.cb_quality.set_sensitive(True)
            #
            li = string.split(self.f_file.get(section, 'abitrate'), ' ')
            self.c_abitrate.set_list(li)
            li = string.split(self.f_file.get(section, 'afreq'), ' ')
            self.c_afreq.set_list(li)
            li = string.split(self.f_file.get(section, 'ach'), ' ')
            self.c_ach.set_list(li)
            li = string.split(self.f_file.get(section, 'acodec'), ' ')
            self.c_acodec.set_list(li)
            
            aqual = string.split((self.f_file.get(section, 'aqual')), ' ')
            self.c_abitrate.set_text(aqual[self.cb_quality.get_active()])
            
        #--- general videos
        if media_type in ('video','mvideo'):
            self.vb_audio.set_sensitive(True)
            self.vb_video.set_sensitive(True)
            self.vb_sub.set_sensitive(False)
            self.cb_quality.set_sensitive(True)
            #
            li = string.split(self.f_file.get(section, 'abitrate'), ' ')
            self.c_abitrate.set_list(li)
            li = string.split(self.f_file.get(section, 'afreq'), ' ')
            self.c_afreq.set_list(li)
            li = string.split(self.f_file.get(section, 'ach'), ' ')
            self.c_ach.set_list(li)
            li = string.split(self.f_file.get(section, 'acodec'), ' ')
            self.c_acodec.set_list(li)
            
            aqual = string.split((self.f_file.get(section, 'aqual')), ' ')
            self.c_abitrate.set_text(aqual[self.cb_quality.get_active()])
            
            li = string.split(self.f_file.get(section, 'vbitrate'), ' ')
            self.c_vbitrate.set_list(li)
            li = string.split(self.f_file.get(section, 'vfps'), ' ')
            self.c_vfps.set_list(li)
            li = string.split(self.f_file.get(section, 'vcodec'), ' ')
            self.c_vcodec.set_list(li)
            li = string.split(self.f_file.get(section, 'vsize'), ' ')
            self.c_vsize.set_list(li)
            
            li = string.split(self.f_file.get(section, 'vratio'), ' ')
            self.c_vratio.set_list(li)
            
            vqual = string.split((self.f_file.get(section, 'vqual')), ' ')
            self.c_vbitrate.set_text(vqual[self.cb_quality.get_active()])
        
        #--- vcd dvd xvcd .. videos
        if media_type == "fixed":
            self.vb_audio.set_sensitive(False)
            self.vb_video.set_sensitive(False)
            self.vb_sub.set_sensitive(False)
            self.cb_quality.set_sensitive(False)
            # 
        if media_type == "mvideo":
            self.vb_audio.set_sensitive(True)
            self.vb_video.set_sensitive(True)
            self.vb_sub.set_sensitive(True)
            self.cb_quality.set_sensitive(True)
            
        
    def build_ffmpeg_cmd(self, input_file, output_file):
        section = self.cb_formats.get_active_text()
        media_type = self.f_file.get(section, 'type')
        
        cmd = ['ffmpeg', '-y', '-xerror']
        cmd.extend(["-i", input_file])
        
        if media_type == 'audio':
            cmd.append('-vn')
            cmd.extend(['-ab', self.c_abitrate.get_text()])
            cmd.extend(['-ar', self.c_afreq.get_text()])
            cmd.extend(['-ac', self.c_ach.get_text()])
            
            codecs = commands.getoutput("ffmpeg -codecs")
            if string.find(codecs, self.c_acodec.get_text()) != -1:
                cmd.extend(['-acodec', self.c_acodec.get_text()])
            else:
                cmd.extend(['-acodec', 'copy'])
            
        elif media_type == 'video':
            cmd.extend(['-ab', self.c_abitrate.get_text()])
            cmd.extend(['-ar', self.c_afreq.get_text()])
            cmd.extend(['-ac', self.c_ach.get_text()])
            
            codecs = commands.getoutput("ffmpeg -codecs")
            if string.find(codecs, self.c_acodec.get_text()) != -1:
                cmd.extend(['-acodec', self.c_acodec.get_text()])
            else:
                cmd.extend(['-acodec', 'copy'])
            #
            cmd.extend(['-b', self.c_vbitrate.get_text()])
            cmd.extend(['-r', self.c_vfps.get_text()])
            cmd.extend(['-vcodec', self.c_vcodec.get_text()])
            if self.c_vsize.get_text() != 'default':
                cmd.extend(['-s', self.c_vsize.get_text()])
            
            if self.c_vratio.get_text() == 'default':
                cmd.extend(['-aspect', get_aspect_ratio(input_file)])
            else:
                cmd.extend(['-aspect', self.c_vratio.get_text()])

        elif media_type == 'fixed':
            target = self.f_file.get(section, 'target')
            cmd.extend(['-target', target])
        
        ff = self.f_file.get(section, 'ff') # force format
        cmd.extend(['-f', ff])
        
        #--- split file
        if self.check_split.get_active():
            cmd.extend(['-ss', str(self.tl_begin.get_duration())])
            cmd.extend(['-t', str(self.tl_duration.get_duration())])
        
        #--- Keep metadata
        cmd.extend(['-map_metadata', '%s:%s' % (output_file, input_file)])
        
        #--- output file at last
        cmd.append(output_file)
             
        return cmd
    
    
    #--- MEncoder cmd
    def buid_mencoder_cmd(self, input_file, output_file):
        section = self.cb_formats.get_active_text()
        
        cmd = ['mencoder']
        
        #--- input and output files
        cmd.append(input_file)
        cmd.extend(['-o', output_file])
        cmd.append('-noskip')
        
        #--- Sub font
        if self.check_sub.get_active():
            cmd.extend(['-sub', self.entry_sub.get_text()])
            cmd.append('-fontconfig')
            font_name = extract_font_name(self.b_font.get_font_name())
            cmd.extend(['-subfont', font_name])
            cmd.extend(['-subfont-text-scale', str(self.spin_size.get_value_as_int())])
            cmd.extend(['-subpos', str(self.spin_pos.get_value_as_int())])
            cmd.extend(['-subcp', self.combo_enc.get_active_text()])
            cmd.append('-flip-hebrew') # RTL mode
            cmd.append('-noflip-hebrew-commas') # RTL mode
            
        
        #--- Audio codec and opts
        cmd.extend(['-oac', self.c_acodec.get_text()])
        if self.c_acodec.get_text() == 'copy':
            pass
        else:
            a_opts = []
            if self.c_acodec.get_text() == 'mp3lame':
                cmd.append('-lameopts')
                a_opts.append('cbr')
                a_opts.append('mode=%s' % self.c_ach.get_text())
                a_opts.append('br=%s' % self.c_abitrate.get_text())
            elif self.c_acodec.get_text() == 'faac':
                cmd.append('-faacopts')
                a_opts.append('br=%s' % self.c_abitrate.get_text())
            elif self.c_acodec.get_text() == 'lavc':
                cmd.append('-lavcopts')
                a_opts.append('abitrate=%s' % self.c_abitrate.get_text())
                
            cmd.append(':'.join(a_opts))
            
        #--- Video codec and opts
        cmd.extend(['-ovc', self.c_vcodec.get_text()])
        if self.c_vcodec.get_text() == 'xvid':
            cmd.append('-xvidencopts')
            v_opts = []
            v_opts.append('bitrate=%s' % self.c_vbitrate.get_text())
            cmd.append(':'.join(v_opts))
        
        
        if self.c_vcodec.get_text() == 'lavc':
            cmd.append('-lavcopts')
            v_opts = []
            v_opts.append('vbitrate=%s' % self.c_vbitrate.get_text())
            cmd.append(':'.join(v_opts))
            if self.f_file.has_option(section, 'opts'):
                cmd.extend(self.f_file.get(section, 'opts').split())
        
        #--- split file
        if self.check_split.get_active():
            cmd.extend(['-ss',     self.tl_begin.get_time_str()])
            cmd.extend(['-endpos', self.tl_duration.get_time_str()])
        
        #video size
        if self.c_vsize.get_text() != 'default':
            cmd.append('-vf')
            cmd.append('scale=%s,harddup' % self.c_vsize.get_text()) 
        
        print cmd
        return cmd

    #--- Convert funtcion
    def convert_cb(self, widget):
        if len(self.store) == 0 or self.is_converting:
            return
        
        # Return if invalid path or inaccessible
        Accessible = os.access(self.e_dest.get_text(), os.W_OK)
        ValidDir   = isdir(self.e_dest.get_text())
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
        encoder_type = self.f_file.get(self.cb_formats.get_active_text(), 'encoder')
        
        #--- Check
        if self.Iter != None:
            
            #--- Not convert this file
            if self.store[self.Iter][0] == False:
                self.store[self.Iter][5] = _("Skipped!")
                self.Iter = self.store.iter_next(self.Iter)
                self.convert_file()
                return
                     
            #--- get input and output files
            input_file = self.store[self.Iter][1]
            part = splitext(basename(input_file))[0] + '.' + ext
            output_file = join(self.e_dest.get_text(), part)
            
            #--- Rename output file if has the same name as input file
            if input_file == output_file:
                output_file = output_file[:-4] + '_00.' + ext
            
            #--- If output file already exist
            if os.path.exists(output_file):
                res = show_message(self,
                             _('File: <b>%s</b> already exist.\nOverwrite it?') % output_file,
                             Gtk.MessageType.WARNING,
                             Gtk.ButtonsType.YES_NO)
                #--- Skipped convert this file
                if res == Gtk.ResponseType.NO:
                    self.store[self.Iter][5] = _('Skipped!')
                    self.Iter = self.store.iter_next(self.Iter)
                    self.convert_file()
                    return
        
            if encoder_type == 'f':
                full_cmd = self.build_ffmpeg_cmd(input_file, output_file)
            elif encoder_type == 'm':
                full_cmd = self.buid_mencoder_cmd(input_file, output_file)
            self.total_duration = self.get_duration(input_file)
            
            if self.check_split.get_active():
                self.total_duration = self.tl_duration.get_duration()
            
            # Stored start time
            self.begin_time = time.time() 
            
            #--- Start the process
            self.fp = Popen(full_cmd, stdout = PIPE, stderr = PIPE, universal_newlines = True, bufsize = -1)
            GLib.io_add_watch(self.fp.stdout, GLib.IO_IN | GLib.IO_HUP, 
                              self.on_output, encoder_type)
            GLib.io_add_watch(self.fp.stderr, GLib.IO_IN | GLib.IO_HUP, 
                              self.on_output, encoder_type)
            GLib.child_watch_add(self.fp.pid, self.on_end)
        
        else:
            self.is_converting = False
    
    #--- Stop conversion cb
    def tb_stop_clicked(self, widget):
        if self.is_converting == True:
            resp = show_message(self, _('Do you want to stop conversion process?'),
                                Gtk.MessageType.QUESTION,
                                Gtk.ButtonsType.YES_NO)
            if resp == Gtk.ResponseType.YES and self.is_converting == True:
                self.is_converting = False
                self.fp.kill()
                self.fp.terminate()
                
    
    def get_duration(self, input_file):
        ''' Get duration file in seconds (float)'''
        duration = 0.0
        cmd = 'ffmpeg -i "' + input_file + '"'
        out_str = commands.getoutput(cmd)
        try:
            time_list = self.reg_duration.findall(out_str)[0].split(':')
        except:
            return duration
        duration = int(time_list[0]) * 3600 + int(time_list[1]) * 60 + float(time_list[2])  
        return duration
    
    
    #---- Quality callback
    def on_cb_quality_changed(self, widget):
        section = self.cb_formats.get_active_text()
        
        if self.f_file.has_option(section, 'aqual'):
            aqual = string.split((self.f_file.get(section, 'aqual')), ' ')
            self.c_abitrate.set_text(aqual[self.cb_quality.get_active()])
        
        if self.f_file.has_option(section, 'vqual'):
            vqual = string.split((self.f_file.get(section, 'vqual')), ' ')
            self.c_vbitrate.set_text(vqual[self.cb_quality.get_active()])
    
    #--- select subtitle
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
        if self.is_converting:
            for Iter in iters:
                if self.store[Iter][:] != self.store[self.Iter][:]: 
                    self.store.remove(Iter)
        else:
            for Iter in iters:
                self.store.remove(Iter)
    
    def get_selected_iters(self):
        ''' Get a list contain selected iters '''
        model, tree_path = self.tree.get_selection().get_selected_rows()
        iters = []
        for path in tree_path:
            iters.append(model.get_iter(path))
        return iters
    
    def on_play_cb(self, widget):
        Iter = self.get_selected_iters()[0]
        os.system('xdg-open "%s"' % self.store[Iter][1])
        
    def on_preview_cb(self, widget):
        encoder_type = self.f_file.get(self.cb_formats.get_active_text(), 'encoder')
        Iter = self.get_selected_iters()[0]
        input_file = self.store[Iter][1]
        output_file = '/tmp/Preview'
        duration = self.get_duration(input_file)
        preview_begin = str(duration / 10)
        #
        if encoder_type == 'f':
            cmd =  self.build_ffmpeg_cmd(input_file, output_file)
            cmd.extend(['-ss', preview_begin])
            cmd.extend(['-t', '15'])
        elif encoder_type == 'm':
            cmd = self.buid_mencoder_cmd(input_file, output_file)
            cmd.extend(['-ss', preview_begin])
            cmd.extend(['-endpos', '15'])
        
        self.fp = Popen(cmd, 
                        stdout = PIPE, stderr = PIPE, 
                        universal_newlines = True, bufsize = -1)
        noti = show_notification(APP_NAME, '', 
                                 _('Please wait while preparing preview...'), 
                                 'dialog-information')
        GLib.child_watch_add(self.fp.pid, self.on_end_preview, (output_file, noti))
        self.set_sensitive(False)
    
    def on_end_preview(self, pid, code, data):
        if code == 0:
            os.system('xdg-open %s' % data[0])
        self.set_sensitive(True)
        data[1].close()
    
    #--- Clear list    
    def tb_clear_clicked(self, widget):
        if not self.is_converting:
            self.store.clear()
        
    def tb_about_clicked(self, widget):
        About(self)
        
    def check_sub_toggled(self, widget):
        self.hb_sub.set_sensitive(widget.get_active())
        self.hb_enc.set_sensitive(widget.get_active())
        self.hb_font.set_sensitive(widget.get_active())
        self.hb_pos.set_sensitive(widget.get_active())
        self.hb_size.set_sensitive(widget.get_active())
    
    def delete_file(self, widget, event):
        if event.keyval == Gdk.KEY_Delete:
            self.tb_remove_clicked(widget)
            
    def show_popup(self, widget, event):
        treepath =  self.tree.get_selection().get_selected_rows()[1]
        if event.button == 3 and len(treepath) != 0:
            self.popup.show_all()
            self.popup.popup(None, None, None, None, 3, Gtk.get_current_event_time())
        
    
    #---- On end conversion
    def on_end(self, pid, err_code):
        if self.Iter != None:
            if err_code == 0:
                self.store[self.Iter][0] = False
                self.store[self.Iter][4] = 100.0
                self.store[self.Iter][5] = _("Done!")
                self.Iter = self.store.iter_next(self.Iter)
                self.convert_file()
            elif err_code == 256:
                self.store[self.Iter][5] = _("Failed!")
                self.Iter = self.store.iter_next(self.Iter)
                self.convert_file()
            elif err_code == 9:
                pass
                #self.store[self.Iter][5] = _("Stopped!")
        else:
            self.is_converting = False
        #---show all
        self.txt_buffer.set_text(self.output_details)
    
    #--- Catch output 
    def on_output(self, source, condition, encoder_type):
        #--- Allow interaction with the application
        while Gtk.events_pending():
            Gtk.main_iteration()
        
        #--- Stop btn clicked.
        if self.is_converting == False:
            return False
        
        #--- Skipped file during conversion (unckeck during conversion)
        if self.store[self.Iter][0] == False:
            self.store[self.Iter][5] = _("Skipped!")
            self.fp.kill()
            self.Iter = self.store.iter_next(self.Iter)
            self.convert_file()
            #self.fp.returncode = 100
            return False
        
        line = source.readline()
        if len(line) > 0:
            self.txt_buffer.set_text(line, -1)
            # ffmpeg progress
            if encoder_type == 'f':
                begin = line.find('time=')
                if begin != -1:
                    elapsed_time = float(self.reg_ffmpeg.findall(line)[0][1])
                    time_ratio = elapsed_time / self.total_duration
                    if time_ratio > 1:
                        time_ratio = 1;
                    
                    # Get estimated size
                    curr_size = float(self.reg_ffmpeg.findall(line)[0][0])
                    est_size = int((curr_size * self.total_duration) / elapsed_time)
                    
                    # Formating estimated size
                    size_str = ''
                    if 0 <= est_size <= 1024:
                        size_str = ('%.2f' % est_size) + ' KB'
                    elif 1024 <= est_size < 1024*1024:
                        e_size = est_size / 1024.0
                        size_str = ('%.2f' % e_size) + ' MB'
                    elif est_size >= 1024*1024:
                        e_size = est_size / 1048576.0
                        size_str = ('%.2f' % e_size) + ' GB'
                    
                    #--- Calculate remaining time.
                    cur_time = time.time() - self.begin_time
                    rem_dur = ((cur_time * self.total_duration) / elapsed_time) - cur_time
                    if rem_dur < 0: rem_dur = 0
                    h = rem_dur / 3600
                    m = (rem_dur % 3600) / 60
                    s = (rem_dur % 3600) % 60
                    rem_time = '%02i:%02i:%02i' %(h, m, s)
                    
                    self.store[self.Iter][2] = size_str                        # estimated size
                    self.store[self.Iter][3] = rem_time                        # remaining time
                    self.store[self.Iter][4] = float(time_ratio * 100)         # progress value
                    self.store[self.Iter][5] = '%.2f %%' % (time_ratio * 100)  # progress text
            #--------------------------------
            if encoder_type == 'm':
                begin = line.find('Pos:')
                if begin != -1:
                    #--- File size
                    file_size = self.reg_mencoder.findall(line)[0][2]
                    self.store[self.Iter][2] = file_size + ' MB'
                    
                    #--- Remaining time
                    dur   = self.reg_mencoder.findall(line)[0][0]
                    rem_dur = self.total_duration - float(dur)
                    h = rem_dur / 3600
                    m = (rem_dur % 3600) / 60
                    s = (rem_dur % 3600) % 60
                    rem_time = '%02i:%02i:%02i' %(h, m, s)
                    self.store[self.Iter][3] = rem_time
                    
                    #--- progress
                    progress_value = float(self.reg_mencoder.findall(line)[0][1])
                    self.store[self.Iter][4] = progress_value
                    self.store[self.Iter][5] = '%.0f %%' % progress_value
                    
            self.output_details += line
            return True
        return False
    


if __name__ == '__main__':
    Curlew()
    Gtk.main()
