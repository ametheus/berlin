#!/bin/bash

echo "Status: HTTP/1.1 200 OK"
echo "Content-type: text/html"
echo ""

replace HTTP_HOST "$SERVER_NAME" < /etc/firewall.d/apache/default.html


REF=$(echo "$HTTP_REFERER" | cut -d/ -f3)

echo "[$SERVER_NAME] ($REF)" >> /var/log/adblock.log
