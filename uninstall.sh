#!/bin/bash

if [ $UID -eq 0 ]; then
	python3 setup.py uninstall
else
	echo "Run me as root!"
fi

