``VideoTester.config`` --- Common constants and functions
=========================================================

Constants
---------

.. automodule:: VideoTester.config
    :members: VTLOG, USERPATH, CONF, TEMP, SERVERBIN, SERVERIFACE, SERVERIP, SERVERPORT

.. note::
    :const:`VideoTester.config.CONF`, :const:`VideoTester.config.TEMP`, :const:`VideoTester.config.SERVERBIN` and :const:`VideoTester.config.SERVERPORT` MAY be replaced by more suitable values.

.. warning::
    :const:`VideoTester.config.SERVERIFACE` MUST be replaced according to your network configuration, and :const:`VideoTester.config.SERVERIP` will be set automatically.

Functions
---------

.. automodule:: VideoTester.config
    :members: makeDir, initLogger, parseArgs, getIpAddress