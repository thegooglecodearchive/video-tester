# coding=UTF8

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
) 