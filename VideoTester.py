#! /usr/bin/env python
# coding=UTF8

from include.config import parseArgs, initLogger, vtLog

if __name__ == '__main__':
    args = parseArgs()
    initLogger(args)
    if args.mode == "server":
        from include.config import SERVERIP, SERVERPORT
        from include.core import Server
        from SimpleXMLRPCServer import SimpleXMLRPCServer
        server = SimpleXMLRPCServer((SERVERIP, SERVERPORT), logRequests=False)
        server.register_instance(Server())
        try:
            print 'Use Control-C to exit'
            server.serve_forever()
        except KeyboardInterrupt:
            vtLog.info("Exiting...")
    else:
        from os import getuid
        if getuid() != 0:
            vtLog.error("You need administrator privileges to run this program as client")
            exit()
        if args.gui:
            from include.gui import ClientGUI
            client = ClientGUI(0)
            client.MainLoop()
        else:
            from include.config import CONF
            from include.core import Client
            if args.conf:
                CONF = args.conf
            client = Client(CONF)
            client.run()
        vtLog.info("Exiting...")