from gi.repository import Gtk, Notify

def show_message(parent, message, message_type, button_type=Gtk.ButtonsType.CLOSE):
    ''' Show custom message dialog'''
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
    '''Get the font name only, without style (bold, italic...) from string'''
    font_str = font_str[:-3]
    styles_list = ['Bold', 'Italic', 'Oblique', 'Medium']
    for style in styles_list:
        font_str = font_str.replace(style, '')
    return font_str.strip()


def get_format_size(size):
    ''' formating file size '''
    size_str = ''
    if 0 <= size <= 1024:
        size_str = '{:.2f} KB'.format(size)
    elif 1024 <= size < 1024 * 1024:
        e_size = size / 1024.0
        size_str = '{:.2f} MB'.format(e_size)
    elif size >= 1024 * 1024:
        e_size = size / 1048576.0
        size_str = '{:.2f} GB'.format(e_size)
    return size_str