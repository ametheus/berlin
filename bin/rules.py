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

from getpass import getuser
from vuurmuur import Config, debug, Vuurmuur

if getuser() == 'root':
    debug( -1, "Restarting BIND" )
    subprocess.call([ 'service', 'bind9', 'start' ])
    
    debug( -1, "Enabling IP forwarding" )
    subprocess.call([ 'sh', '-c',
        'echo 1 > /proc/sys/net/ipv4/ip_forward' ])
    
    subprocess.call(['/sbin/modprobe', 'ip_conntrack_ftp'])
    subprocess.call(['/sbin/modprobe', 'ip_nat_ftp'])
else:
    debug( 1, "Note: you are not root." )

debug( 0, "Detecting configuration... ", False )
C = Config()
debug( 0, "done." )

debug( 0, "Constructing iptables rules..." )
V = Vuurmuur()
V.import_config( C )
V.output_chains( '/etc/vuurmuur/rules' if getuser() == 'root' else '/tmp/rules' )
debug( 0, "Done." )
