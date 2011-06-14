#!/bin/sh

#
#   Copyright (C) 2011  Thijs van Dijk
#
#   This file is part of vuurmuur.
#
#   Vuurmuur is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   Vuurmuur is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   file "COPYING" for details.
#


# debug "Restarting BIND"
service bind9 restart

# debug "Enabling IP forwarding"
echo 1 > /proc/sys/net/ipv4/ip_forward


iptables-restore /etc/firewall.d/rules
