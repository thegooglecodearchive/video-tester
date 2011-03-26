# coding=UTF8

import logging
from platform import processor
from sys import exit
import os

def createDir(dir):
    """
    asdfas
    """
    from os import mkdir
    try:
        mkdir(dir)
    except OSError:
        pass

def initLogger(args):
    if args.mode == "server":
        formatter = logging.Formatter("[%(asctime)s VTServer] %(levelname)s : %(message)s")
    else:
        logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
        formatter = logging.Formatter("[%(asctime)s VTClient] %(levelname)s : %(message)s")
    createDir(TEMP)
    fh = logging.FileHandler(TEMP + 'client.log')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    VTLOG.addHandler(fh)
    if not hasattr(args, 'gui') or not args.gui:
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch.setFormatter(formatter)
        VTLOG.addHandler(ch)
    VTLOG.setLevel(logging.DEBUG)

def parseArgs():
    import textwrap
    import argparse
    parser = argparse.ArgumentParser(
            formatter_class=argparse.RawDescriptionHelpFormatter,
            description=textwrap.dedent('''\
                Video Tester, by Iñaki Úcar (june 2011), mailto:i.ucar86@gmail.com
                ------------------------------------------------------------------
                '''))
    subparsers = parser.add_subparsers(title='subcommands', dest='mode')
    parser_server = subparsers.add_parser('server', help='launch VT as server')
    parser_client = subparsers.add_parser('client', help='launch VT as client')
    parser_client.add_argument('-g', '--gui', dest='gui', action='store_true', help='launch graphical interface')
    parser_client.add_argument('-c', '--conf', dest='conf', nargs=1, help='client configuration file')
    return parser.parse_args()

def getIpAddress(ifname):
    import socket
    import fcntl
    import struct
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15])
    )[20:24])

#: VT logger.
VTLOG = logging.getLogger("VT")
#: Current working path (result of ``os.getcwd()`` function).
USERPATH = os.getcwd()
#: Path to the configuration file (relative to ``USERPATH``).
CONF = USERPATH + '/VT.conf'
#: Path to the temporal directory (relative to ``USERPATH``).
TEMP = USERPATH + '/temp/'
#: Path to the RTSP server binaries (relative to ``USERPATH``).
SERVERBIN = USERPATH + '/rtsp-server/' + processor() + '/server'
#: Server interface.
SERVERIFACE = 'eth0'
#: Server IP.
SERVERIP = getIpAddress(SERVERIFACE)
#: Base port.
SERVERPORT = 8000