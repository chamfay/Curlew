#-*- coding:utf-8 -*-

import gettext, sys, os
from os.path import dirname, isdir

#--- localizations
exedir = dirname(sys.argv[0])
Locale = os.path.join(exedir, '..', 'share/locale')
if not isdir(Locale):
    Locale = os.path.join(exedir, '..', 'locale')
gettext.install('curlew', Locale)