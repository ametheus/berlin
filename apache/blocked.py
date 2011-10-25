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

import os

print "Status: HTTP/1.1 200 OK"
print "Content-type: text/html"
print ""

# Open the default html content
f = open( '/etc/berlin/apache/default.html', 'r' )
cnt = f.read()
f.close()


# Find the http host, referer's host, and client IP
http_host = os.environ['SERVER_NAME']  if 'SERVER_NAME'  in os.environ else 'berlin-firewall'
referer   = os.environ['HTTP_REFERER'] if 'HTTP_REFERER' in os.environ else ''
client_ip = os.environ['REMOTE_ADDR']  if 'REMOTE_ADDR'  in os.environ else '--.--.--.--'

# Place these variables at set locations in the document, ...
cnt = cnt.replace( 'HTTP_HOST',   http_host );
cnt = cnt.replace( 'REFERER',     referer );
cnt = cnt.replace( 'REMOTE_ADDR', client_ip );
# ... and send them to output.
print cnt


# Place a log entry:
lf = open( '/var/log/adblock.log', 'a' )
if lf:
    lf.writelines([
            '{0:<15} {1:<35} ({2})\n'.format( client_ip, '['+http_host+']', referer )
    ])
    lf.close()
