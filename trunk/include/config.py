# coding=UTF8

import logging

CONF = 'VT.conf'
TEMP = 'temp/'
SERVERBIN = 'rtsp-server/x64/server'
SERVERPORT = 8000
SERVERIFACE = 'eth0'

vtLog = logging.getLogger("VT")

def createDir(dir):
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
    vtLog.addHandler(fh)
    if not hasattr(args, 'gui') or not args.gui:
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch.setFormatter(formatter)
        vtLog.addHandler(ch)
    vtLog.setLevel(logging.DEBUG)

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

SERVERIP = getIpAddress(SERVERIFACE)