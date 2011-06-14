#!/usr/bin/env python
"""

    Copyright (C) 2011  Thijs van Dijk

    This file is part of vuurmuur.

    Vuurmuur is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Vuurmuur is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    file "COPYING" for details.

"""

import sys

# Debug level
#  2 = Nothing, not even errors
#  1 = Just errors
#  0 = Helpful status messages
# -1 = Chatty
# -2 = Blabbermouth
debuglevel = 1


def debug( importance, str, newline=True ):
    """Send {str} to stdout. Maybe.
    
    If {importance} is high enough, send {str} to stdout."""
    
    if importance >= debuglevel:
        sys.stdout.write( "{0}{1}".format( str, "\n" if newline else "" ) )

if '--silence' in sys.argv:
    x = sys.argv.index('--silence')+1
    if len(sys.argv) > x:
        debuglevel = int(sys.argv[x])

