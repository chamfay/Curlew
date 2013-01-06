#-*- coding:utf-8 -*-

import gettext
import sys
from os.path import dirname, isdir, join

exedir = dirname(sys.argv[0])

localdir = ''

# Curlew script (default locale)
if isdir(join(exedir, '..', 'share/locale')):
    localdir = join(exedir, '..', 'share/locale')

# Curlew script (test)
elif isdir(join(exedir, 'locale')):
    localdir = join(exedir, 'locale')

# curlew.py
else:
    localdir = join(exedir, '..', 'locale')

gettext.install('curlew', localdir)