from gi.repository import Gtk, Pango

class LogDialog(Gtk.Dialog):
    def __init__(self, prnt, log_file):
        self._log_file = log_file
        Gtk.Dialog.__init__(self, parent=prnt)
        self.set_size_request(550, 450)
        self.set_border_width(6)
        self.set_title(_('Errors detail'))
        scroll = Gtk.ScrolledWindow()
        scroll.set_shadow_type(Gtk.ShadowType.IN)
        text_log = Gtk.TextView()
        text_log.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        text_log.set_border_width(6)
        text_log.set_editable(False)
        text_log.set_cursor_visible(False)
        
        font_desc = Pango.FontDescription('Monospace')
        text_log.override_font(font_desc)
        
        text_buffer = Gtk.TextBuffer()
        text_log.set_buffer(text_buffer)
        
        scroll.add(text_log)
        self.vbox.pack_start(scroll, True, True, 0)
        
        button = self.add_button(Gtk.STOCK_CLOSE, Gtk.ResponseType.CLOSE)
        self.set_default(button)
        
        with open(log_file, 'r') as log:
            text_buffer.set_text(log.read())
    
    def show_dialog(self):
        self.show_all()
        self.run()
        self.destroy()
        
        
        
        
        