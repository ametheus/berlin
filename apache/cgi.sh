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


echo "Status: HTTP/1.1 200 OK"
echo "Content-type: text/html"
echo ""

replace HTTP_HOST "$SERVER_NAME" < /etc/vuurmuur/apache/default.html


REF=$(echo "$HTTP_REFERER" | cut -d/ -f3)

echo "[$SERVER_NAME] ($REF)" >> /var/log/adblock.log
