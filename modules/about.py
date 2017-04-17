# -*- coding: utf-8 -*-

# Curlew - Easy to use multimedia converter
#
# Copyright (C) 2012-2016 Fayssal Chamekh <chamfay@gmail.com>
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

PROGRAMMER = 'Fayssal Chamekh <chamfay@gmail.com>'
WEBSITE = 'http://sourceforge.net/projects/curlew'
VERSION = '0.2.3'


class About(Gtk.AboutDialog):
    def __init__(self, parent):
        Gtk.AboutDialog.__init__(self, parent=parent, wrap_license=True)
        self.set_program_name(_('Curlew'))
        self.set_authors([PROGRAMMER, 'Ehab El-Gedawy <ehabsas@gmail.com>', 'Andrej Kvasnica <andrej@gmail.com>'])
        self.set_copyright("Copyright © 2012-2016 Fayssal Chamekh <chamfay@gmail.com>")
        self.set_version(VERSION)
        self.set_title(_('About Curlew'))
        self.set_logo_icon_name('curlew')
        self.set_icon_name('curlew')
        self.set_comments(_('Easy to use Multimedia Converter for Linux'))
        self.set_license("""
Released under terms on waqf public license.

This program is free software; you can redistribute it and/or modify it under the terms of the latest version waqf public license as published by ojuba.org.

This program is distributed in the hope that it will be useful, but without any warranty; without even the implied warranty of merchantability or fitness for a particular purpose.
        
The latest version of the license can be found on:
http://waqf.ojuba.org/license
""")
        self.set_website(WEBSITE)
        self.set_website_label(WEBSITE)
        self.set_translator_credits(_("translator-credits"))
        self.set_artists([PROGRAMMER, 'Smail <kungfu07mail@gmail.com>'])
    
    def show(self):
        self.run()
        self.destroy()
