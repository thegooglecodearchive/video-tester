``VideoTester.config`` --- Common constants and functions
=========================================================

.. module:: VideoTester.config

Constants
---------

.. autodata:: VTLOG
.. autodata:: USERPATH
.. autodata:: CONF
.. autodata:: TEMP
.. autodata:: SERVERBIN
.. autodata:: SERVERIFACE
.. autodata:: SERVERIP
.. autodata:: SERVERPORT

.. note::
    :const:`CONF`, :const:`TEMP`, :const:`SERVERBIN` and :const:`SERVERPORT` MAY be replaced by more suitable values.

.. warning::
    :const:`SERVERIFACE` MUST be replaced according to your network configuration, and :const:`SERVERIP` will be set automatically.

Functions
---------

.. autofunction:: makeDir
.. autofunction:: initLogger
.. autofunction:: parseArgs
.. autofunction:: getIpAddress
.. autofunction:: bubbleSort