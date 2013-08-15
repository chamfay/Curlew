from distutils.core import setup
from glob import glob
from subprocess import call
import sys
from os.path import splitext, split

#NOTE: You must install imagemagick, intltool packages.

doc_files  = ['LICENSE-ar.txt', 'LICENSE-en.txt', 'AUTHORS', 'ChangeLog', 'README']
data_files = [('share/applications/', ['curlew.desktop']),
              ('share/icons/hicolor/scalable/apps', ['curlew.svg']),
              ('share/doc/curlew', doc_files),
              ]

# Prepare curlew icons
def generate_icons():
    # Generate curlew.png icons
    for i in [16, 22, 24, 32, 36, 48, 64, 72, 96, 128]:
        call("mkdir -p hicolor/{0}x{0}/apps/".format(i), shell=True)
        call("convert -background none curlew.svg -resize {0}x{0} hicolor/{0}x{0}/apps/curlew.png".format(i), shell=True)
    
    # List all svg files
    svg_files = glob('Curlew/icons/*/*.svg')
    for svg_file in svg_files:
        png_file = splitext(svg_file)[0] + ".png"
        ret = call("convert -background none {} -resize 48x48 {}".format(svg_file, png_file), shell=True)
    
    icons = map(lambda i: ('share/icons/'+i, [i+'/curlew.png', ]), glob("hicolor/*/apps"))
    data_files.extend(icons)
    
    return ret
    
    
# Update locales
def update_locale():
    # Make curlew.pot file from python source files.
    py_files = " ".join(glob("Curlew/*.py"))
    call("xgettext --keyword=_ -o po/curlew.pot {}".format(py_files), shell=True)
    
    po_files = glob("po/*.po")
    for po_file in po_files:
        lang = splitext(split(po_file)[1])[0]
        mo_path = "locale/{}/LC_MESSAGES/curlew.mo".format(lang)
        
        # Update po files
        ret = call("intltool-update -g po/curlew -d po/{}".format(lang), shell=True)
        
        # Make locale directories
        call("mkdir -p locale/{}/LC_MESSAGES/".format(lang), shell=True)
        
        # Generate mo files
        call("msgfmt {} -o {}".format(po_file, mo_path), shell=True)
    
    locales = map(lambda i: ('share/'+i, [i+'/curlew.mo', ]), glob('locale/*/LC_MESSAGES'))
    data_files.extend(locales)
    
    return ret


def clean_all():
    print("Clean...")
    
    call("rm -rfv hicolor dist locale build", shell=True)
    call("rm -rfv dist locale build", shell=True)
    call("rm -fv MANIFEST po/*.mo", shell=True)
    call("rm -fv Curlew/icons/*/*.png", shell=True)
    call("rm -fv Curlew/*.pyc *.pyc", shell=True)
    exit(0)



def uninstall():
    print("Uninstall...")
    # Remove icons
    call("rm -rfv /usr/share/icons/hicolor/*/apps/curlew*", shell=True)
    call("rm -rfv /usr/*/share/icons/hicolor/*/apps/curlew*", shell=True)
    
    # Remove mos
    call("rm -rfv /usr/share/locale/*/LC_MESSAGES/curlew.mo", shell=True)
    call("rm -rfv /usr/*/share/locale/*/LC_MESSAGES/curlew.mo", shell=True)
    
    # Remove packages
    call("rm -rfv /usr/lib/python*/*-packages/[cC]urlew*", shell=True)
    call("rm -rfv /usr/*/lib/python*/*-packages/[cC]urlew*", shell=True)
    
    # Remove Docs
    call("rm -rfv /usr/share/doc/curlew", shell=True)
    call("rm -rfv /usr/*/share/doc/curlew", shell=True)
    
    # Remove .desktop file
    call("rm -rfv /usr/share/applications/curlew*", shell=True)
    call("rm -rfv /usr/*/share/applications/curlew*", shell=True)
    
    # Remove script
    call("rm -rfv /usr/bin/curlew", shell=True)
    call("rm -rfv /usr/*/bin/curlew", shell=True)
    
    # Remove configurations
    call("rm -rfv ~/.curlew/curlew.cfg", shell=True)
    call("rm -rfv ~/.curlew/fav.list", shell=True)
    
    exit(0)



# Begin
if len(sys.argv) < 2: exit(1)

if sys.argv[1] in ['bdist', 'bdist_rpm', 'build', 'install']:
    if generate_icons() + update_locale() > 0: exit(1)
elif sys.argv[1] == 'clean':
    clean_all()
elif sys.argv[1] == 'uninstall':
    uninstall()


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
      version="0.1.20.3",
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
