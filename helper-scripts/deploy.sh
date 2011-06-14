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

# Change into vuurmuur's root directory
cd $(dirname $0)/..

# Make sure required packages are installed
apt-get install -qq \
    apache2 \
    libapache2-mod-php5 \
    dhcp3-server \
    mysql-server \
    git-core

# Remove links from previous versions
rm -f /etc/firewall.d /usr/share/vuurmuur
rm -f /sbin/firewall /sbin/restore-firewall

# Link this directory in a default location
ln -s $(pwd) /usr/share/vuurmuur

# Create the config directory, and link the initial content
mkdir -p /etc/vuurmuur
rm -f /etc/vuurmuur/{apache,ad-hosts,malware-hosts,smtp-hosts}
ln -s /usr/share/vuurmuur/apache                /etc/vuurmuur/apache
ln -s /usr/share/vuurmuur/config/ad-hosts       /etc/vuurmuur/ad-hosts
ln -s /usr/share/vuurmuur/config/malware-hosts  /etc/vuurmuur/malware-hosts
ln -s /usr/share/vuurmuur/config/smtp-hosts     /etc/vuurmuur/smtp-hosts

# Link the binaries
ln -s /usr/share/vuurmuur/helper-scripts/recreate-firewall.sh   /sbin/firewall
ln -s /usr/share/vuurmuur/helper-scripts/restore-firewall.sh    /sbin/restore-firewall




# Enable the apache configuration
# Link adblock.conf as an available site
ln -s /etc/vuurmuur/apache/adblock.conf   /etc/apache2/sites-available/adblock

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
cd bin
./generate-config.py --blind-faith



# Yes, I blindly trust the deploy script.
mv /tmp/firewall/dhcpd.conf /etc/dhcp3/dhcpd.conf
mv /tmp/firewall/interfaces /etc/network/interfaces
mv /tmp/firewall/if-config /etc/vuurmuur/if-config
rm -rf /etc/firewall.d/config/networks /etc/vuurmuur/networks
mv /tmp/firewall/networks /etc/vuurmuur
rmdir /tmp/firewall


# Execute the scripts
/sbin/firewall
/etc/init.d/networking restart
service dhcp3-server restart


