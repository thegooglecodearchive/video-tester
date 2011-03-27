# coding=UTF8
## This file is part of VideoTester
## See http://video-tester.googlecode.com for more information
## Copyright 2011 Iñaki Úcar <i.ucar86@gmail.com>
## This program is published under a GPLv3 license

from distutils.core import setup

setup(name = "VideoTester",
    version = "0.1",
    description = "Video Quality Assessment Tool",
    author = "Iñaki Úcar",
    author_email = "i.ucar86@gmail.com",
    url = "http://video-tester.googlecode.com",
    packages = ['VideoTester', 'VideoTester.measures'],
    scripts = ["VT"],
    #long_description = """Really long text here.""" 
    platforms = ['i686', 'x86_64'],
    license = "GPLv3"
) 