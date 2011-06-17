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


if [ "$(whoami)" != "root" ]
then
    echo "You are not root."
    exit
    echo "If you can read this, it means the 'exit' command doesn't work the way I thought it does."
fi

# Change into berlin's root directory
cd $(dirname $0)/..

# Make sure required packages are installed
apt-get install -qq \
    apache2 \
    libapache2-mod-php5 \
    dhcp3-server \
    mysql-server \
    git-core

# Remove links from previous versions
rm -f /etc/firewall.d /usr/share/vuurmuur /usr/share/berlin
rm -f /sbin/firewall /sbin/restore-firewall

# Link this directory in a default location
ln -s $(pwd) /usr/share/berlin

# Create the config directory, and link the initial content
mkdir -p /etc/berlin
rm -f /etc/berlin/{apache,ad-hosts,malware-hosts,smtp-hosts}
ln -s /usr/share/berlin/apache                /etc/berlin/apache
ln -s /usr/share/berlin/config/ad-hosts       /etc/berlin/ad-hosts
ln -s /usr/share/berlin/config/malware-hosts  /etc/berlin/malware-hosts
ln -s /usr/share/berlin/config/smtp-hosts     /etc/berlin/smtp-hosts

# Link the binaries
ln -s /usr/share/berlin/helper-scripts/recreate-firewall.sh   /sbin/firewall
ln -s /usr/share/berlin/helper-scripts/restore-firewall.sh    /sbin/restore-firewall




# Enable the apache configuration
# Link adblock.conf as an available site
ln -s /etc/berlin/apache/adblock.conf   /etc/apache2/sites-available/adblock

# Remove the default virtualhost.
# If this causes serious problems, there was something wrong with the config to begin with.
rm -f /etc/apache2/sites-enabled/000-default

# Enable the virtualhosts
ln -s ../sites-available/adblock            /etc/apache2/sites-enabled/000-adblock

# Create a new log file for the adblock CGI
touch /var/log/adblock.log
chown www-data:www-data /var/log/adblock.log

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
mv /tmp/firewall/if-config /etc/berlin/if-config
rm -rf /etc/firewall.d /etc/vuurmuur /etc/berlin/networks
mv /tmp/firewall/{networks,ports} /etc/berlin/
rmdir /tmp/firewall


# Execute the scripts
/sbin/firewall
/etc/init.d/networking restart
service dhcp3-server restart


