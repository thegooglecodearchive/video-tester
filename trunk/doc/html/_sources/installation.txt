Installation
============

Video Tester has the following dependencies:

* Python 2.7.
* GStreamer 0.10 with bindings for Python.
* GStreamer plugins: base, good, ugly, bad.
* GStreamer FFmpeg plugins.
* GStreamer RTSP server 0.10.8 (at least). 
* Scapy 2.0.
* Matplotlib 1.0.1.
* Numpy 1.4.1.
* WxPython 2.8.11 with backend for Matplotlib.
* OpenCV 2.1 with bindings for Python.

This dependencies can be installed with the following command (only for Fedora)::

	$ yum install gstreamer gstreamer-plugins-base gstreamer-plugins-good gstreamer-plugins-ugly \
		gstreamer-plugins-bad-free gstreamer-plugins-bad-nonfree gstreamer-python gstreamer-ffmpeg \
		gstreamer-rtsp scapy numpy python-matplotlib python-matplotlib-wx wxpython opencv-python

You can download the latest version of Video Tester from the project download page at Google Code: <https://code.google.com/p/video-tester/>. Then, follow this steps (the last command, with root privileges)::

	$ tar -xvf VideoTester-0.2.tar.gz
	$ cd VideoTester-0.2
	$ python setup.py install

During the installation, you'll be asked for two configuration parameters:

* The server interface (default: ``eth0``).
* The server port (default: ``8000``).

After the installation, Video Tester will be located in ``/usr/lib/python2.7/site-packages/VideoTester``, and this documentation, in ``/usr/share/doc/VideoTester-0.2``. You'll be able to launch the application with the command ``VT``.