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

from output import debug

def net( iface ):
    """Return the network of a given interface.
    
    Examples:
    
    >>> class IF:
    ...     address = '1.1.1.1'
    >>> A = IF()
    >>> net(A)
    '1.1.1.0/24'
    >>> A.address = '192.168.192.168'
    >>> net(A)
    '192.168.192.0/24'
    
    Invalid interfaces:
    
    >>> net( 4 )
    Traceback (most recent call last):
    ...
    AttributeError: 'int' object has no attribute 'address'
    >>> net( [] )
    Traceback (most recent call last):
    ...
    AttributeError: 'list' object has no attribute 'address'
    
    Interfaces with an invalid IP address:
    
    >>> A.address = '1.2.3.4.5'
    >>> net(A)
    Traceback (most recent call last):
    ...
    Exception: Invalid address "1.2.3.4.5"
    >>> A.address = '2001:4860:a002::68'
    >>> net(A)
    Traceback (most recent call last):
    ...
    Exception: Invalid address "2001:4860:a002::68"
    
    """
    
    addr = iface.address.split('.')
    if len(addr) != 4:
        if hasattr(iface,'name'):
            raise Exception('Invalid address "' + iface.address + '" for interface ' + iface.name + '.')
        raise Exception('Invalid address "' + iface.address + '"')
    
    return '.'.join(iface.address.split('.')[0:3]) + '.0/24'
def gw( iface ):
    """Return the gateway address of a given interface.
    
    Examples:
    
    >>> class IF:
    ...     address = '1.1.1.1'
    >>> A = IF()
    >>> gw(A)
    '1.1.1.1'
    >>> A.address = '192.168.192.168'
    >>> gw(A)
    '192.168.192.1'
    
    Invalid interfaces:
    
    >>> gw( 4 )
    Traceback (most recent call last):
    ...
    AttributeError: 'int' object has no attribute 'address'
    >>> gw( [] )
    Traceback (most recent call last):
    ...
    AttributeError: 'list' object has no attribute 'address'
    
    Interfaces with an invalid IP address:
    
    >>> A.address = '1.2.3.4.5'
    >>> gw(A)
    Traceback (most recent call last):
    ...
    Exception: Invalid address "1.2.3.4.5"
    >>> A.address = '2001:4860:a002::68'
    >>> gw(A)
    Traceback (most recent call last):
    ...
    Exception: Invalid address "2001:4860:a002::68"
    
    """
    
    addr = iface.address.split('.')
    if len(addr) != 4:
        if hasattr(iface,'name'):
            raise Exception('Invalid address "' + iface.address + '" for interface ' + iface.name + '.')
        raise Exception('Invalid address "' + iface.address + '"')
    
    return '.'.join(iface.address.split('.')[0:3]) + '.1'

def ip_batch( C, file=False ):
    """Generate a batch file to perform load balancing
    
    In order to share outgoing traffic between multiple ISP's, a batch file is
    produced for the  ip  utility.
    
    Examples:
    
    >>> class X(object):
    ...     def __init__(self,_d={},**kwargs):
    ...         kwargs.update(_d)
    ...         self.__dict__=kwargs
    
    >>> N1 = X(net=lambda:'192.168.10.0/24')
    >>> N2 = X(net=lambda:'192.168.20.0/24')
    >>> N3 = X(net=lambda:'192.168.30.0/24')
    
    >>> I1 = X(wan_interface=False,name='int-1',subnets=[N1,N2])
    >>> I2 = X(wan_interface=False,name='int-2',subnets=[N3])
    >>> I3 = X(wan_interface=False,name='int-3',subnets=[N1,N2,N3])
    >>> I4 = X(wan_interface=False,name='int-4',subnets=[])
    
    >>> E1 = X(wan_interface=True,name='ext-1',address='12.34.56.78',load_balance=1)
    >>> E2 = X(wan_interface=True,name='ext-2',address='34.56.78.12',load_balance=2)
    >>> E3 = X(wan_interface=True,name='ext-3',address='56.78.12.34',load_balance=3)
    
    >>> C1 = X(Interfaces=[I3, E1])
    >>> C2 = X(Interfaces=[I2, E1,E2])
    >>> C3 = X(Interfaces=[I1,I4, E1,E2,E3])
    
    >>> ip_batch(C1)
    route flush table main
    route flush table RTint-3
    route flush table RText-1
    <BLANKLINE>
    route add 12.34.56.0/24 dev ext-1 src 12.34.56.78 table RText-1
    route add 192.168.10.0/24 dev int-3 table RText-1
    route add 192.168.20.0/24 dev int-3 table RText-1
    route add 192.168.30.0/24 dev int-3 table RText-1
    route add 127.0.0.0/8 dev lo table RText-1
    route add default via 12.34.56.1 table RText-1
    <BLANKLINE>
    route add 12.34.56.0/24 dev ext-1 src 12.34.56.78
    route add default via ext-1
    <BLANKLINE>
    route add default scope global nexthop via 12.34.56.1 dev ext-1 weight 1
    <BLANKLINE>
    rule add from 12.34.56.78 table RText-1
    
    >>> ip_batch(C2)
    route flush table main
    route flush table RTint-2
    route flush table RText-1
    route flush table RText-2
    <BLANKLINE>
    route add 12.34.56.0/24 dev ext-1 src 12.34.56.78 table RText-1
    route add 34.56.78.0/24 dev ext-2 table RText-1
    route add 192.168.30.0/24 dev int-2 table RText-1
    route add 127.0.0.0/8 dev lo table RText-1
    route add default via 12.34.56.1 table RText-1
    <BLANKLINE>
    route add 34.56.78.0/24 dev ext-2 src 34.56.78.12 table RText-2
    route add 12.34.56.0/24 dev ext-1 table RText-2
    route add 192.168.30.0/24 dev int-2 table RText-2
    route add 127.0.0.0/8 dev lo table RText-2
    route add default via 34.56.78.1 table RText-2
    <BLANKLINE>
    route add 12.34.56.0/24 dev ext-1 src 12.34.56.78
    route add 34.56.78.0/24 dev ext-2 src 34.56.78.12
    route add default via ext-1
    <BLANKLINE>
    route add default scope global nexthop via 12.34.56.1 dev ext-1 weight 1 nexthop via 34.56.78.1 dev ext-2 weight 2
    <BLANKLINE>
    rule add from 12.34.56.78 table RText-1
    rule add from 34.56.78.12 table RText-2

    >>> ip_batch(C3)
    route flush table main
    route flush table RTint-1
    route flush table RTint-4
    route flush table RText-1
    route flush table RText-2
    route flush table RText-3
    <BLANKLINE>
    route add 12.34.56.0/24 dev ext-1 src 12.34.56.78 table RText-1
    route add 34.56.78.0/24 dev ext-2 table RText-1
    route add 56.78.12.0/24 dev ext-3 table RText-1
    route add 192.168.10.0/24 dev int-1 table RText-1
    route add 192.168.20.0/24 dev int-1 table RText-1
    route add 127.0.0.0/8 dev lo table RText-1
    route add default via 12.34.56.1 table RText-1
    <BLANKLINE>
    route add 34.56.78.0/24 dev ext-2 src 34.56.78.12 table RText-2
    route add 12.34.56.0/24 dev ext-1 table RText-2
    route add 56.78.12.0/24 dev ext-3 table RText-2
    route add 192.168.10.0/24 dev int-1 table RText-2
    route add 192.168.20.0/24 dev int-1 table RText-2
    route add 127.0.0.0/8 dev lo table RText-2
    route add default via 34.56.78.1 table RText-2
    <BLANKLINE>
    route add 56.78.12.0/24 dev ext-3 src 56.78.12.34 table RText-3
    route add 12.34.56.0/24 dev ext-1 table RText-3
    route add 34.56.78.0/24 dev ext-2 table RText-3
    route add 192.168.10.0/24 dev int-1 table RText-3
    route add 192.168.20.0/24 dev int-1 table RText-3
    route add 127.0.0.0/8 dev lo table RText-3
    route add default via 56.78.12.1 table RText-3
    <BLANKLINE>
    route add 12.34.56.0/24 dev ext-1 src 12.34.56.78
    route add 34.56.78.0/24 dev ext-2 src 34.56.78.12
    route add 56.78.12.0/24 dev ext-3 src 56.78.12.34
    route add default via ext-1
    <BLANKLINE>
    route add default scope global nexthop via 12.34.56.1 dev ext-1 weight 1 nexthop via 34.56.78.1 dev ext-2 weight 2 nexthop via 56.78.12.1 dev ext-3 weight 3
    <BLANKLINE>
    rule add from 12.34.56.78 table RText-1
    rule add from 34.56.78.12 table RText-2
    rule add from 56.78.12.34 table RText-3

    """
    
    # The network interfaces
    Ext = [ I for I in C.Interfaces if     I.wan_interface ]
    Int = [ I for I in C.Interfaces if not I.wan_interface ]
    
    
    routes = [['flush','table','main']]
    lb_route = ['add','default','scope','global']
    rules = []
    main = []
    
    # Clear all  ip  routes for now
    routes += [ ['flush','table','RT'+I.name] for I in C.Interfaces ]
    routes += [[]]
    
    
    
    if len(Ext) == 0:
        debug( 0, 'No interfaces to balance any load. Exiting.' )
        return
    
    for ifc in Ext:
        T = 'RT'+ifc.name
        routes += [['add',net(ifc),'dev',ifc.name,'src',ifc.address,'table',T]]
        main   += [['add',net(ifc),'dev',ifc.name,'src',ifc.address]]
        
        routes += [ ['add',net(E), 'dev',E.name,'table',T] for E in Ext if E != ifc ]
        routes += [ ['add',N.net(),'dev',I.name,'table',T] for I in Int for N in I.subnets ]
        
        routes += [
                ['add','127.0.0.0/8','dev','lo','table',T],
                ['add','default','via',gw(ifc),'table',T],
                []
        ]
        
        lb_route += ['nexthop','via',gw(ifc),'dev',ifc.name,'weight',str(ifc.load_balance)]
        
        rules += [['add','from',ifc.address,'table',T]]
    
    routes += main
    routes += [['add','default','via',Ext[0].name],
        [], lb_route, []]
    
    
    
    output = [ 'route ' + ' '.join(R) if len(R) > 0 else '' for R in routes ] + \
            [ 'rule ' + ' '.join(R) if len(R) > 0 else '' for R in rules ]
    
    if file:
        file.writelines([ R + '\n' for R in output ])
    else:
        for R in output:
            print R



if __name__ == '__main__':
    
    import sys
    
    if '--run' in sys.argv:
        from network_config import Config
        from getpass import getuser
        
        C = Config()
        ip_batch( C )
    else:
        import doctest
        fail, total = doctest.testmod( optionflags = doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE )
        sys.exit( fail )

