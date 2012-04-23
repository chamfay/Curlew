#! /usr/bin/python

from distutils.core import setup
from glob import glob

doc_files  = ['LICENSE-ar.txt', 'LICENSE-en', 'AUTHORS', 'ChangeLog', 'README']
data_files = [('share/applications/', ['data/curlew.desktop']),
              ('share/icons/hicolor/scalable/apps', ['curlew.svg']),
              ('share/doc/curlew', doc_files),
              ]

locales = map(lambda i: ('share/'+i, [''+i+'/curlew.mo',]), glob('locale/*/LC_MESSAGES'))
data_files.extend(locales)         


setup(
      name = 'Curlew',
      description  = 'Easy to use multimedia converter in Linux',
      version      = '0.1.3',
      author       = 'Fayssal Chamekh',
      author_email = 'chamfay@gmail.com',
      url          = 'https://github.com/chamfay/Curlew',
      license      = 'Waqf License',
      platforms    = 'Linux',
      py_modules   = ['curlew'],
      scripts      = ['curlew'],
      keywords     = ['convert','audio', 'video', 'ffmpeg', 'mencoder'],
      classifiers  = [
                     'Programming Language :: Python',
                     'Operating System :: POSIX :: Linux',
                     'Development Status :: 4 - Beta',
                     'Environment :: X11 Applications :: Gtk',
                     'Natural Language :: English',
                     'Natural Language :: Arabic',
                     'Intended Audience :: End Users/Desktop',
                     'Topic :: Desktop Environment :: Gnome',
                     'Topic :: Multimedia :: Video :: Conversion',
                     'Topic :: Multimedia :: Sound/Audio :: Conversion',
                     'Topic :: Utilities'],
      data_files   = data_files,
      packages     = [''],
      package_data = {'':['data/*.svg', 'formats.cfg']}
      )
