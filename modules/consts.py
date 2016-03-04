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

import os
from os.path import join, dirname, realpath

HOME = os.getenv("HOME")
CONF_PATH = join(HOME, '.curlew')

CONF_FILE = join(CONF_PATH, 'curlew.cfg')

PKG_DIR = dirname(realpath(__file__))
DTA_DIR = join(PKG_DIR, '../')

ORG_FFILE = join(DTA_DIR, 'formats.cfg')
USR_FFILE = join(CONF_PATH, 'formats.cfg')

