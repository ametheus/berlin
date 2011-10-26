#!/usr/bin/env python
"""

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

"""

import subprocess
from output import debug

def create_qos_qdisc( C, fake=False ):
    """Create a QoS qdisc
    
    Create a qdisc (Queueing Discipline) capable of simple rule-based Quality of 
    Service.
    
    """
    
    # The external interfaces
    ifaces = [ I for I in C.Interfaces if I.wan_interface ]
    
    if len(ifaces) == 0:
        debug( 0, 'No external interfaces found' )
    
    def k( x ):
        """Format a bandwidth of x kbit/s"""
        
        return '{0}kbit'.format(int(x))
    
    rules = []
    
    # Remove tc rules for all interfaces
    for I in C.Interfaces:
        rules += [['tc','qdisc','del','dev',I.name,'root']]
    
    # Add a simple priority tree for each QoS-enabled external interface
    for ifc in ifaces:
        if not ifc.qos_bandwidth: continue
        
        # The max available bandwidth
        ceil = ifc.qos_bandwidth
        # The smallest significant unit of bandwidth
        unit = round(ceil/25)
        
        ifn = ifc.name
        
        rules += [
            ['tc','qdisc','add','dev',ifn,'root',         'handle', '1:',  'htb','default','15'],
            
            ['tc','class','add','dev',ifn,'parent','1:',  'classid','1:1', 'htb','rate',k(  ceil),'ceil',k(ceil)           ],
            ['tc','class','add','dev',ifn,'parent','1:1', 'classid','1:10','htb','rate',k(8*unit),'ceil',k(ceil),'prio','0'],
            ['tc','class','add','dev',ifn,'parent','1:1', 'classid','1:11','htb','rate',k(8*unit),'ceil',k(ceil),'prio','1'],
            ['tc','class','add','dev',ifn,'parent','1:1', 'classid','1:12','htb','rate',k(2*unit),'ceil',k(ceil),'prio','2'],
            ['tc','class','add','dev',ifn,'parent','1:1', 'classid','1:13','htb','rate',k(2*unit),'ceil',k(ceil),'prio','2'],
            ['tc','class','add','dev',ifn,'parent','1:1', 'classid','1:14','htb','rate',k(1*unit),'ceil',k(ceil),'prio','3'],
            ['tc','class','add','dev',ifn,'parent','1:1', 'classid','1:15','htb','rate',k(3*unit),'ceil',k(ceil),'prio','3'],
            
            ['tc','qdisc','add','dev',ifn,'parent','1:12','handle', '120:','sfq','perturb','10'],
            ['tc','qdisc','add','dev',ifn,'parent','1:13','handle', '130:','sfq','perturb','10'],
            ['tc','qdisc','add','dev',ifn,'parent','1:14','handle', '140:','sfq','perturb','10'],
            ['tc','qdisc','add','dev',ifn,'parent','1:15','handle', '150:','sfq','perturb','10']
        ]
    
    if len(rules) == 0:
        debug( 0, 'No rules to implement; QoS disabled' )
        return
    
    if not fake:
        for R in rules:
            subprocess.call( R, stderr = subprocess.PIPE )
    else:
        for R in rules:
            print ' '.join(R)



if __name__ == '__main__':
    
    import sys
    
    if '--run' in sys.argv:
        from network_config import Config
        from getpass import getuser
        
        C = Config()
        create_qos_qdisc( C, (getuser() != 'root') )
    else:
        import doctest
        fail, total = doctest.testmod( optionflags = doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE )
        sys.exit( fail )

