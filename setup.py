from distutils.core import setup
from glob import glob

doc_files  = ['LICENSE-ar.txt', 'LICENSE-en', 'AUTHORS', 'ChangeLog', 'README']
data_files = [('share/applications/', ['curlew.desktop']),
              ('share/icons/hicolor/scalable/apps', ['curlew.svg']),
              ('share/doc/curlew', doc_files),
              ]

locales = map(lambda i: ('share/' + i, ['' + i + '/curlew.mo', ]), glob('locale/*/LC_MESSAGES'))
data_files.extend(locales)


setup(
      name="curlew",
      description='Easy to use multimedia converter in Linux',
      long_description='''Curlew written in python and GTK3 and it depends on (ffmpeg/avconv, mencoder).

Main Features:
- Easy to use with simple user interface.
- Hide the advanced options with the ability to show them.
- Convert to more than 100 different formats.
- Show file informations (duration, remaining time, estimated size, progress value).
- Allow to skip or remove file during conversion process.
- Preview file before conversion.
- Convert a specified portion of file.
- Combine subtitle with video file.
- Show error details if exist.
- And more ...''',
      version="0.1.16.2",
      author='Fayssal Chamekh',
      author_email='chamfay@gmail.com',
      url='https://github.com/chamfay/Curlew',
      license='Waqf License',
      platforms='Linux',
      scripts=['curlew'],
      keywords=['convert', 'audio', 'video', 'ffmpeg', 'mencoder','avconv'],
      classifiers=[
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
      data_files=data_files,
      packages=['Curlew'],
      package_data={'':['icons/*/*.png', 'formats.cfg']}
      )
