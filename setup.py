# coding=UTF8

from distutils.core import setup

files = ["rtsp-server/server.c", "rtsp-server/i686/server", "rtsp-server/i686/.libs/server", "rtsp-server/x86_64/server", "rtsp-server/x86_64/.libs/server"]

setup(name = "VideoTester",
    version = "0.1",
    description = "Video Quality Assessment Tool",
    author = "Iñaki Úcar",
    author_email = "i.ucar86@gmail.com",
    url = "http://video-tester.googlecode.com",
    packages = ['VideoTester', 'VideoTester.measures'],
    package_data = {'VideoTester' : files },
    scripts = ["VT"],
    #long_description = """Really long text here.""" 
) 