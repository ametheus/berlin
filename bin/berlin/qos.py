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

def create_qos_qdisc( C, file=False ):
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
        rules += [['qdisc','del','dev',I.name,'root']]
    rules += [[]]
    
    # Add a simple priority tree for each QoS-enabled external interface
    for ifc in ifaces:
        if not ifc.qos_bandwidth: continue
        
        # The max available bandwidth
        ceil = ifc.qos_bandwidth
        # The smallest significant unit of bandwidth
        unit = round(ceil/25)
        
        ifn = ifc.name
        
        rules += [
            ['qdisc','add','dev',ifn,'root',         'handle', '1:',  'htb','default','16'],
            
            ['class','add','dev',ifn,'parent','1:',  'classid','1:1', 'htb','rate',k(  ceil),'ceil',k(  ceil )           ],
            
            ['class','add','dev',ifn,'parent','1:1', 'classid','1:11','htb','rate',k(5*unit),'ceil',k(10*unit),'prio','0'],
            ['class','add','dev',ifn,'parent','1:1', 'classid','1:12','htb','rate',k(7*unit),'ceil',k(  ceil ),'prio','1'],
            ['class','add','dev',ifn,'parent','1:1', 'classid','1:13','htb','rate',k(7*unit),'ceil',k(  ceil ),'prio','2'],
            ['class','add','dev',ifn,'parent','1:1', 'classid','1:14','htb','rate',k(2*unit),'ceil',k(  ceil ),'prio','3'],
            ['class','add','dev',ifn,'parent','1:1', 'classid','1:15','htb','rate',k(2*unit),'ceil',k(  ceil ),'prio','3'],
            ['class','add','dev',ifn,'parent','1:1', 'classid','1:16','htb','rate',k(1*unit),'ceil',k(  ceil ),'prio','4'],
            ['class','add','dev',ifn,'parent','1:1', 'classid','1:17','htb','rate',k(3*unit),'ceil',k(  ceil ),'prio','4'],
            
            ['qdisc','add','dev',ifn,'parent','1:13','handle', '130:','sfq','perturb','10'],
            ['qdisc','add','dev',ifn,'parent','1:14','handle', '140:','sfq','perturb','10'],
            ['qdisc','add','dev',ifn,'parent','1:15','handle', '150:','sfq','perturb','10'],
            ['qdisc','add','dev',ifn,'parent','1:16','handle', '160:','sfq','perturb','10'],
            ['qdisc','add','dev',ifn,'parent','1:17','handle', '170:','sfq','perturb','10'],
            
            ['filter','add','dev',ifn,'parent','1:0','protocol','ip','prio','1','handle','1','fw','classid','1:11'],
            ['filter','add','dev',ifn,'parent','1:0','protocol','ip','prio','2','handle','2','fw','classid','1:12'],
            ['filter','add','dev',ifn,'parent','1:0','protocol','ip','prio','3','handle','3','fw','classid','1:13'],
            ['filter','add','dev',ifn,'parent','1:0','protocol','ip','prio','4','handle','4','fw','classid','1:14'],
            ['filter','add','dev',ifn,'parent','1:0','protocol','ip','prio','5','handle','5','fw','classid','1:15'],
            ['filter','add','dev',ifn,'parent','1:0','protocol','ip','prio','6','handle','6','fw','classid','1:16'],
            ['filter','add','dev',ifn,'parent','1:0','protocol','ip','prio','7','handle','7','fw','classid','1:17'],
            ['filter','add','dev',ifn,'parent','1:0','protocol','ip','prio','255','handle','255','fw','classid','1:2'],

            []
        ]
    
    if len(rules) == 0:
        debug( 0, 'No rules to implement; QoS disabled' )
        return
    
    if file:
        file.writelines([ ' '.join(R) + '\n' for R in rules ])
    else:
        for R in rules:
            print ' '.join(R)



if __name__ == '__main__':
    
    import sys
    
    if '--run' in sys.argv:
        from network_config import Config
        from getpass import getuser
        
        C = Config()
        create_qos_qdisc( C )
    else:
        import doctest
        fail, total = doctest.testmod( optionflags = doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE )
        sys.exit( fail )

