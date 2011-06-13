#!/usr/bin/env python

import network_config
import sys


C = network_config.Config()
C.UI_loop()


if '--blind-faith' in sys.argv:
    C.Export()

