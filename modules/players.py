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

from shutil import which

from gi.repository import Gtk
from modules.customwidgets import ComboWithEntry
from modules.configs import set_s_config

PLAYERS_LIST = [
    'mpv',
    'vlc',
    'ffplay',
    'avplay',
    'mplayer',
    'smplayer',
    'totem',
    'kplayer',
    'kmplayer',
    'parole'
    ]

class Players(Gtk.Dialog):
    def __init__(self, prnt):
        Gtk.Dialog.__init__(self, use_header_bar=True, parent=prnt)
        self.set_border_width(4)
        self.set_size_request(300, 1)
        self.set_resizable(False)
        self.set_title(('Players list'))
        self.vbox.set_spacing(6)
        
        label = Gtk.Label(_("<b>Select your favorite player: </b>"), use_markup=True)
        label.set_alignment(0.0, 0.5)
        self.vbox.pack_start(label, False, False, 0)
        
        cmb_players = ComboWithEntry()
        self.vbox.pack_start(cmb_players, False, False, 0)
        
        self.entry_player = cmb_players.get_child()
        self.entry_player.connect('changed', self.on_entry_player_changed)
        
        # Load available players
        cmb_players.remove_all()
        for player in PLAYERS_LIST:
            if which(player):
                cmb_players.append_text(player)
        cmb_players.set_active(0)
    
    
    def on_entry_player_changed(self, e):
        e.set_icon_from_icon_name(Gtk.EntryIconPosition.PRIMARY, e.get_text())
    
    def show_dialog(self):
        self.show_all()
        self.run()
        
        plyr = self.entry_player.get_text()
        set_s_config('player', plyr)
        
        self.destroy()
        return plyr
