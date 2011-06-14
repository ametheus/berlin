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


if [ "$(whoami)" != "root" ]
then
    echo "You are not root."
    exit
    echo "If you can read this, it means the 'exit' command doesn't work the way I thought it does."
fi


# Make sure required packages are installed
apt-get install -qq \
    apache2 \
    libapache2-mod-php5 \
    dhcp3-server \
    mysql-server \
    git-core

# Link the default (hard-coded) config dir
ln -s "$(pwd)" /etc/firewall.d 2>/dev/null

# Link the binaries
ln -s /etc/firewall.d/helper-scripts/recreate-firewall.sh   /sbin/firewall
ln -s /etc/firewall.d/helper-scripts/restore-firewall.sh    /sbin/restore-firewall




# Enable the apache configuration
# Link adblock.conf as an available site
ln -s /etc/firewall.d/apache/adblock.conf   /etc/apache2/sites-available/adblock

# Remove the default virtualhost.
# If this causes serious problems, there was something wrong with the config to begin with.
rm -f /etc/apache2/sites-enabled/000-default

# Enable the virtualhosts
ln -s ../sites-available/adblock            /etc/apache2/sites-enabled/000-adblock

# Enable required modules
a2enmod rewrite
a2enmod proxy
a2enmod proxy_http

# Restart apache
service apache2 restart




# Generate configuration files
cd /etc/firewall.d/bin
./generate-config.py --blind-faith



# Yes, I blindly trust the deploy script.
mv /tmp/firewall/dhcpd.conf /etc/dhcp3/dhcpd.conf
mv /tmp/firewall/interfaces /etc/network/interfaces
mv /tmp/firewall/if-config /etc/firewall.d/config/if-config
rm -rf /etc/firewall.d/config/networks
mv /tmp/firewall/networks /etc/firewall.d/config
rmdir /tmp/firewall


# Execute the scripts
/sbin/firewall
/etc/init.d/networking restart
service dhcp3-server restart


