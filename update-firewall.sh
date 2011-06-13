#!/bin/sh

cd /etc/firewall.d

GITOUT="$(git pull origin master 2>/dev/null)"

FW="rules.py|config/ad-hosts|config/malware-hosts|config/smtp-hosts|update-firewall.sh"
AP="apache"

if [ "$(echo "$GITOUT" | grep -P " ($FW)[ ]+\|")" != "" ]; then
    echo "Recreating firewall rules."
    /sbin/firewall
fi
if [ "$(echo "$GITOUT" | grep -P "$AP")" != "" ]; then
    service apache2 reload
fi

git fetch --all >/dev/null

