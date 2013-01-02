#-*- coding:utf-8 -*-

import gettext, os
from os.path import dirname, isdir

#--- localizations
exedir = dirname(__file__)
Locale = os.path.join(exedir, '..', 'share/locale')
if not isdir(Locale):
    Locale = os.path.join(exedir, '..', 'locale')
gettext.install('curlew', Locale)