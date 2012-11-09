from gi.repository import Gtk


class CustomHScale(Gtk.HScale):
    def __init__(self, container, def_value, min_value, max_value):
        Gtk.HScale.__init__(self)
        container.add(self)
        adj = Gtk.Adjustment(def_value, min_value, max_value, 1)
        self.set_adjustment(adj)
        self.set_value_pos(Gtk.PositionType.RIGHT)
        

class LabeledHBox(Gtk.HBox):
    def __init__(self, Label, container=None, CWidth=12):
        ''' hbox with label'''
        Gtk.HBox.__init__(self, spacing=4)
        label = Gtk.Label(Label, use_markup=True)
        label.set_alignment(0, 0.5)
        label.set_width_chars(CWidth)
        self.pack_start(label, False, False, 0)
        if container != None:
            container.pack_start(self, False, False, 0)


class TimeLayout(Gtk.HBox):
    def __init__(self, container, Label):
        '''    Time widget    '''
        Gtk.HBox.__init__(self)
        self._spin_h = Gtk.SpinButton().new_with_range(0, 5, 1)
        self._spin_m = Gtk.SpinButton().new_with_range(0, 59, 1)
        self._spin_s = Gtk.SpinButton().new_with_range(0, 59, 1)
        
        label = Gtk.Label(Label, use_markup=True)
        label.set_alignment(0, 0.5)
        label.set_width_chars(10)
        self.pack_start(label, False, False, 0)
        self.pack_start(self._spin_h, False, False, 3)
        self.pack_start(Gtk.Label(label=_('hr')), False, False, 0)
        self.pack_start(self._spin_m, False, False, 3)
        self.pack_start(Gtk.Label(label=_('min')), False, False, 0) 
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
        ''' Return time str like 00:00:00'''
        return '{:02.0f}:{:02.0f}:{:02.0f}'.format(self._spin_h.get_value(), 
                                                   self._spin_m.get_value(), 
                                                   self._spin_s.get_value())


class LabeledComboEntry(Gtk.ComboBoxText):
    ''' Create custom ComboBoxText with entry'''
    def __init__(self, Container, Label, WithEntry=True):
        Gtk.ComboBoxText.__init__(self, has_entry=WithEntry)
        self.connect('changed', self.on_combo_changed)
        hbox = Gtk.HBox()
        hbox.set_spacing(4)
        label = Gtk.Label(Label, use_markup=True)
        label.set_alignment(0, 0.5)
        label.set_width_chars(15)
        self.set_entry_text_column(0)
        hbox.pack_start(label, False, False, 0)
        hbox.pack_start(self, False, False, 0)
        Container.pack_start(hbox, False, False, 0)
    
    def set_list(self, list_of_elements):
        ''' Fill combobox with list directly [] '''
        self.remove_all()
        map(self.append_text, list_of_elements)
        self.set_active(0)
    
    def get_text(self):
        return self.get_active_text()
    
    def set_text(self, Text):
        ''' Set text to Entry '''
        entry = self.get_child()
        entry.set_text(Text)
    
    def on_combo_changed(self, *args):
        enabled = self.get_text() == 'default' and len(self.get_model()) < 2
        self.set_sensitive(not enabled)
            
            
            