#!/bin/bash

pip3.11 download \
	--requirement requirements.txt \
	--dest dependencies/ \
	--only-binary=:all: \
	--platform x86_64 \
	--platform linux_x86_64 \
	--platform manylinux_x86_64 \
	--platform manylinux1_x86_64 \
	--platform manylinux2014_x86_64 \
	--platform manylinux2010_x86_64

sha256sum dependencies/* > CHECKSUMS.sha256sum

