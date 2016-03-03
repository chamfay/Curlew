#!/bin/bash
# python3-stdeb package needed.

python3 setup.py --command-packages=stdeb.command debianize

#
sed -i 's|Package: python3-curlew|Package: curlew|g' $PWD/debian/control

# Make deb
#debuild -b
