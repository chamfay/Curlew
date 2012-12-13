from gi.repository import Gtk

def show_message(parent, 
                 message, 
                 message_type, 
                 button_type=Gtk.ButtonsType.CLOSE):
    ''' Show custom message dialog'''
    mess_dlg = Gtk.MessageDialog(parent,
                             Gtk.DialogFlags.MODAL,
                             message_type,
                             button_type)
    mess_dlg.set_markup(message)
    resp = mess_dlg.run()
    mess_dlg.destroy()
    return resp

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


def duration_to_time(duration):
    ''' Convert duration (sec) to time 0:00:00 '''
    if duration < 0: duration = 0
    return '{:.0f}:{:02.0f}:{:02.0f}'.format(
                                             duration/3600,
                                             (duration%3600)/60,
                                             (duration%3600)%60
                                             )
def time_to_duration(time):
    ''' Convert time like 0:00:00.00 to duration (sec)'''
    times = time.split(':')
    return int(times[0])*3600 + int(times[1])*60 + float(times[2])
