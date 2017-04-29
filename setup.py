from distutils.core import setup
from glob import glob
from subprocess import call
import sys
from os.path import splitext, split

# IMPORTANT!
# You MUST have this packages installed in your system:
#     "librsvg2-bin" to use rsvg-convert command.
#     "intltool-debian" or "intltool" to use intltool-update command.

VERSION = '0.2.4'
SVG_CONVERT = 'rsvg-convert'
UPDATE = 'intltool-update'
UPDATE_DEBIAN = '/usr/share/intltool-debian/intltool-update'

doc_files  = ['LICENSE-ar.txt', 'LICENSE-en.txt', 'AUTHORS', 'THANKS', 'ChangeLog', 'README']
data_files = [('share/applications/', ['curlew.desktop']),
              ('share/icons/hicolor/scalable/apps', ['curlew.svg']),
              ('share/pixmaps', ['curlew.svg']),
              ('share/doc/curlew', doc_files),
              ('share/curlew', ['formats.cfg', 'done.ogg']),
              #('share/curlew', ['formats.cfg', 'ffmpeg']), # Portable version
              ('share/curlew/modules', glob("modules/*.py"))
              ]

# Prepare curlew icons
def generate_icons():
    # Generate curlew.png icons
    for i in [16, 22, 24, 32, 36, 48, 64, 72, 96, 128]:
        call("mkdir -p hicolor/{0}x{0}/apps/".format(i), shell=True)
        if call("{0} curlew.svg -w {1} -h {1} -o hicolor/{1}x{1}/apps/curlew.png".format(SVG_CONVERT, i), shell=True) > 0:
            return 1
    
    icons = map(lambda i: ('share/icons/'+i, [i+'/curlew.png', ]), glob("hicolor/*/apps"))
    data_files.extend(icons)
    return 0
    
    
# Update locales
def update_locale():
    # Make curlew.pot file from python source files.
    py_files = " ".join(glob("modules/*.py"))
    call("xgettext --keyword=_ -o po/curlew.pot {}".format(py_files), shell=True)
    
    po_files = glob("po/*.po")
    for po_file in po_files:
        lang = splitext(split(po_file)[1])[0]
        mo_path = "locale/{}/LC_MESSAGES/curlew.mo".format(lang)
        
        # Update po files
        if call("{} -x -g po/curlew -d po/{}".format(UPDATE, lang), shell=True) > 0:
            return 1
        
        # Make locale directories
        call("mkdir -p locale/{}/LC_MESSAGES/".format(lang), shell=True)
        
        # Generate mo files
        call("msgfmt {} -o {}".format(po_file, mo_path), shell=True)
    
    locales = map(lambda i: ('share/curlew/'+i, [i+'/curlew.mo', ]), glob('locale/*/LC_MESSAGES'))
    data_files.extend(locales)
    
    return 0


def clean_all():
    print("Clean...")
    
    call("rm -rfv hicolor dist locale build", shell=True)
    call("rm -rfv dist locale build", shell=True)
    call("rm -fv MANIFEST po/*.mo", shell=True)
    call("rm -fv modules/icons/*/*.png", shell=True)
    call("rm -fv modules/*.pyc *.pyc", shell=True)
    call("rm -rfv modules/__pycache__", shell=True)
    exit(0)



def uninstall_all():
    print("Uninstall...")
    
    # Remove icons
    call("rm -rfv /usr/share/icons/hicolor/*/apps/curlew*", shell=True)
    call("rm -rfv /usr/*/share/icons/hicolor/*/apps/curlew*", shell=True)
    call("rm -rfv /usr/share/pixmaps/curlew*", shell=True)
    call("rm -rfv /usr/*/share/pixmaps/curlew*", shell=True)
    
    # Remove packages
    call("rm -rfv /usr/lib/python*/*-packages/[cC]urlew*", shell=True)
    call("rm -rfv /usr/*/lib/python*/*-packages/[cC]urlew*", shell=True)
    
    # Remove Docs
    call("rm -rfv /usr/share/doc/curlew", shell=True)
    call("rm -rfv /usr/*/share/doc/curlew", shell=True)
    
    # Remove .desktop file
    call("rm -rfv /usr/share/applications/curlew*", shell=True)
    call("rm -rfv /usr/*/share/applications/curlew*", shell=True)
    
    # Remove data files
    call("rm -rfv /usr/share/curlew", shell=True)
    call("rm -rfv /usr/*/share/curlew", shell=True)
    
    # Remove script
    call("rm -rfv /usr/bin/curlew", shell=True)
    call("rm -rfv /usr/*/bin/curlew", shell=True)
    
    # Remove configurations
    call("rm -rfv ~/.curlew/curlew.cfg", shell=True)
    call("rm -rfv ~/.curlew/fav.list", shell=True)
    
    exit(0)


# Begin
if len(sys.argv) < 2: exit(1)

# Check intltool
if call('which /usr/share/intltool-debian/intltool-update > /dev/null', shell=True) == 0:
    UPDATE = UPDATE_DEBIAN

if sys.argv[1] in ['bdist', 'bdist_rpm', 'build', 'install']:
    if (generate_icons() > 0 ) or (update_locale() > 0):
        exit(1)
elif sys.argv[1] == 'clean':     clean_all()
elif sys.argv[1] == 'uninstall': uninstall_all()


setup(
      name="curlew",
      description='Easy to use multimedia converter in Linux',
      long_description='''Curlew written in python and GTK3 and it depends on (ffmpeg/avconv).

Main Features:
- Easy to use and clean user interface.
- Hide the advanced options with the ability to show them.
- Convert to more than 100 different formats.
- Allow to edit formats.
- Shutdown or suspend PC after a conversion process.
- Show file informations (duration, remaining time, estimated size, progress value).
- Show file details using mediainfo.
- Allow to skip or remove file during conversion process.
- Preview file before conversion.
- Show video thumbnail.
- Convert a specified portion of file.
- Combine subtitle with video.
- Allow to crop and pad video.
- Show error details if exist.
- And more ...''',
      version=VERSION,
      author='Fayssal Chamekh',
      author_email='chamfay@gmail.com',
      url='http://sourceforge.net/projects/curlew',
      license='Waqf License',
      platforms='Linux',
      scripts=['curlew'],
      keywords=['convert', 'audio', 'video', 'ffmpeg', 'avconv'],
      classifiers=[
                     'Programming Language :: Python :: 3',
                     'Operating System :: POSIX :: Linux',
                     'Development Status :: 5 - Production/Stable',
                     'Environment :: X11 Applications :: GTK',
                     'Natural Language :: English',
                     'Natural Language :: Arabic',
                     'Natural Language :: French',
                     'Intended Audience :: End Users/Desktop',
                     'Topic :: Desktop Environment :: Gnome',
                     'Topic :: Multimedia :: Sound/Audio :: Conversion',
                     'Topic :: Utilities'],
      data_files=data_files
      )
