#!/bin/sh

#
#   Copyright (C) 2011  Thijs van Dijk
#
#   This file is part of berlin.
#
#   Berlin is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   Berlin is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   file "COPYING" for details.
#

set -e


# Restart BIND, just for the heck of it
service bind9 restart  >/dev/null

# Enable IP forwarding in the kernel
echo 1 > /proc/sys/net/ipv4/ip_forward

# Load appropriate kernel modules (if not present already)
modprobe ip_conntrack_ftp
modprobe ip_nat_ftp

# Load the iptables rules
iptables-restore /etc/berlin/rules

# Load the tc trees, if present
if [ -f /etc/berlin/qos-qdisc ]
then
    tc -b /etc/berlin/qos-qdisc
fi
