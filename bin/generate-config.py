#!/usr/bin/env python
"""

    Copyright (C) 2011  Thijs van Dijk

    This file is part of berlin.

    Berlin is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Berlin is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    file "COPYING" for details.

"""

import berlin
import sys


C = berlin.Config()

if '--print' in sys.argv:
    C.Display()
    sys.exit(0)

UI = berlin.ConfigUI(C)
UI.loop()


if '--blind-faith' in sys.argv:
    C.Export()

