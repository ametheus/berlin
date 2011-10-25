<?php
/*

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

*/

$adfly = file_get_contents( "http://" . $_SERVER["HTTP_HOST"] . $_SERVER["REQUEST_URI"] );

if ( preg_match( "/            var url = '(http[^']+)';/", $adfly, $A ) )
{
    $URL = $A[1];
    
    header( "301 Moved Permanently" );
    header( "Location: $URL" );
    
    ?><!DOCTYPE html>
<html>
    <head>
        <title>Omleiding</title>
    </head>
    <body>
        <h1>Jemig de pemig.</h1>
        <p>Wauw.</p>
        <p>Welke browser gebruik je in hemelsnaam?</p>
        <p>
            Ik doe mijn uiterste best om je om te leiden naar
            <a href="<?=$URL?>"><?=$URL?></a>,
            maar je browser negeert me volkomen.
        </p>
    </body>
</html><?php
}
else
{
    ?><!DOCTYPE html>
<html>
    <head>
        <title>Oops</title>
    </head>
    <body>
        <p>Helaas, de adfly-link kon niet worden gevonden.</p>
    </body>
</html><?php
}