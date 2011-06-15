#!/usr/bin/env python
"""

    Copyright (C) 2011  Thijs van Dijk

    This file is part of vuurmuur.

    Vuurmuur is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Vuurmuur is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    file "COPYING" for details.

"""

import termios, sys, os
import subprocess
from collections import *
from getpass import getuser

def open_file( filename, mode ):
    """Does the same as open(), only transparently checks multiple locations."""
    
    if filename[0] == '/':
        # This is an absolute path, so just open that file.
        return open( filename, mode )
    
    locations = ['/etc/vuurmuur/','/etc/firewall.d/config/']
    
    for L in locations:
        fn = L + filename
        try:
            f = open(fn,mode)
            return f
        except IOError:
            pass
    
    raise IOError("File not found, or permission denied.")

def list_directory( dir ):
    """Does the same as os.listdir, only it transparently checks multiple
    locations."""
    
    if dir[0] == '/':
        try:
            return os.listdir(dir)
        except OSError:
            return []
    
    locations = ['/etc/vuurmuur/','/etc/firewall.d/config/']
    
    for L in locations:
        dn = L + dir
        try:
            return os.listdir(dn)
        except OSError:
            pass
    
    return []

def file_put_contents( filename, data ):
    """Write str({data}) to the file {filename}."""
    f = open_file( filename, 'w' )
    f.write( data )
    f.close()

def file_put_data( filename, data ):
    """Perform the opposite of parse_file().
    
    Create a file at {filename} parsable by parse_file(), using {data}.
    
    Examples:
    
    >>> D = dict({'test': ['a', 'b', 'c']})
    >>> file_put_data('/tmp/doctest_file_put_data',D)
    >>> E = parse_file('/tmp/doctest_file_put_data')
    >>> E['test']
    ['a', 'b', 'c']
    >>> E['test another value']
    ['undefined']"""
    
    file_put_contents( filename, unparse_file( data ) )

def parse_file( filename ):
    """Parse a simple config file.
    
    Parse a file in the form
    key: val1 val2  val3 val4
    to a defauktdict in the form
    dict({'key': ['val1','val2','val3','val4']})
    
    Examples:
    
    >>> P = parse_file('/dev/null')
    >>> P['key']
    ['undefined']
    
    >>> Q = dict({'key': ['val1','val2','val3','val4']})
    >>> file_put_data('/tmp/doctest_parse_file',Q)
    >>> R = parse_file('/tmp/doctest_parse_file')
    >>> R['key']
    ['val1', 'val2', 'val3', 'val4']
    
    """
    
    rv = defaultdict(lambda:['undefined'])
    try:
        f = open_file( filename, 'r' )
    except(OSError, IOError):
        pass
    else:
        s = f.read()
        l = [ t.split(':',1) for t in s.splitlines() ]
        for i in l:
            if len(i) < 2: continue
            rv[i[0].strip()] = [t.strip() for t in i[1].split(None)]
        f.close()
    return rv

def unparse_file( data ):
    """String-format a configuration file.
    
    Re-casts a dict as returned by parse_file() to a string.
    
    Examples:
    >>> unparse_file(dict({'key':['val'],'key1':['val1','val2']}))
    'key1: val1 val2\\nkey: val\\n\\n'
    >>> unparse_file(None)
    Traceback (most recent call last):
    ...
    AttributeError: 'NoneType' object has no attribute 'items'
    >>> unparse_file(dict())
    '\\n\\n'
    
    """
    
    return "\n".join(
        [ ': '.join(r) for r in
            [ (t[0], ' '.join(t[1]) ) for t in data.items() ]]
    ) + "\n\n"

def null_callback(s,o):
    """An empty callback function for a Display() method."""
    print s

class Config:
    """Complete network configuration for vuurmuur."""
    
    Interfaces = None
    ifconfig = None
    
    local_services = [ 22, 80, 443, 19360 ] # TODO: implement
    network_services = [ (22222,'192.168.144.2:22') ] # TODO: implement
    
    def __init__( self, network_devices=None ):
        """Parses the config directories into a Config class."""
        
        self.Interfaces = []
        self.ifconfig = parse_file("if-config")
        
        if network_devices == None:
            #print "   detecting network devices..."
            P = subprocess.Popen( ['/bin/sh', '-c',
                '/sbin/ifconfig -a -s 2>/dev/null | grep -v Iface '
                    '| cut -d\  -f1 | cut -d: -f1 | grep -v lo | sort | uniq'],
                stdout=subprocess.PIPE )
            s = P.stdout.read()
        else:
            s = network_devices
        
        # Parse local services
        if not 'undefined' in self.ifconfig['local services']:
            self.local_services = [ int(p) for p in self.ifconfig['local services'] ]
        
        # Get a list of subnets
        nets = list_directory('networks')
        
        gb = None
        for ifx in s.splitlines():
            I = Iface( ifx.strip(), self.ifconfig, nets )
            
            if gb is None and I.enabled and not I.wan_interface:
                gb = I
            
            self.Interfaces.append( I )
        
        for N in nets:
            gb.subnets.append(Subnet(N))
        
        self.tion = ( self.Interfaces[0], None, None )
    
    def Export( self ):
        """Writes back all config files into /tmp/firewall/."""
        
        ifaces_file = self.interfaces_file()
        
        subprocess.call([
            'rm', '-rf', '/tmp/firewall'
        ])
        os.mkdir( '/tmp/firewall' )
        os.mkdir( '/tmp/firewall/networks' )
        file_put_contents( '/tmp/firewall/if-config', self.if_config_file() )
        file_put_contents( '/tmp/firewall/interfaces', self.interfaces_file() )
        file_put_contents( '/tmp/firewall/dhcpd.conf', self.dhcp_conf() )
        
        for I in self.Interfaces:
            I.Export( '/tmp/firewall/networks' )
    
    
    def if_config_file( self ):
        """Creates a new if-config file based on current settings.
        
        Returns the contents of the new if-config file in a string."""
        
        rv = dict()
        rv['wan address'] = \
            [ d.wan_address for d in self.Interfaces if d.wan_interface and d.enabled ]
        rv['external address'] = \
            [ d.address     for d in self.Interfaces if d.wan_interface and d.enabled ]
        rv['external interface'] = \
            [ d.name        for d in self.Interfaces if d.wan_interface and d.enabled ]
        rv['internal interface'] = \
            [ d.name        for d in self.Interfaces if not d.wan_interface and d.enabled ]
        rv['local services'] = [ str(i) for i in self.local_services ]
        
        return unparse_file( rv )
    
    
    def interfaces_file( self ):
        """Creates a new /etc/network/interfaces file.
        
        Returns the contents of the /etc/network/interfaces file in a string."""
        
        s = "# This file describes the network interfaces available on your system\n" + \
            "# and how to activate them. For more information, see interfaces(5).\n" + \
            "\n" + \
            "# The loopback network interface\n" + \
            "auto lo\n" + \
            "iface lo inet loopback\n\n"
        return s + "\n\n".join(
            [ t.interfaces_file() for t in self.Interfaces ]
        )
    
    def dhcp_conf( self ):
        """Creates a new /etc/dhcp3/dhcpd.conf file.
        
        Returns the contents of the /etc/dhcp3/dhcpd.conf file in a string."""
        
        rv = "ddns-updates off;" + "\n" + \
            "ddns-update-style interim;" + "\n" + \
            "authoritative;" + "\n" + \
            "shared-network local" + "\n" + \
            "{" + "\n" + \
            "\t" + "" + "\n"
        for I in self.Interfaces:
            rv += I.subnet_decl()
        rv += "\t\n\t\n"
        for I in self.Interfaces:
            rv += I.host_decl()
        
        return rv + "\t\n\t\n}\n\n"
    
    
    @staticmethod
    def sort_iface( a, b ):
        """A sorting function for Iface's"""
        
        if ( not a.enabled ) and ( b.enabled ):
            return -1
        if ( a.enabled ) and ( not b.enabled ):
            return 1
        if ( not a.wan_interface ) and ( b.wan_interface ):
            return -1
        if ( a.wan_interface ) and ( not b.wan_interface ):
            return 1
        return 0
    
    
    def Display( self, cb=null_callback ):
        """Print a graphic representation of the network topology to stdout.
        
        Examples:
        
        >>> C = Config()
        >>> C.Interfaces = [Iface()]
        >>> C.local_services = [1,2,3]
        >>> print '.', C.Display()
        .      \\
             /   Open ports: [1, 2, 3]
             \\
          I  /  --    ##    --   () 
          N  \\            
          T  /
          E  \\
        None
        
        """
        
        cnt = [0]
        def pr(s,o):
            """Display the jagged line and the word 'INTERNET.' """
            
            S = '  {intc} {intsep}{string}'.format(
                    intc = ('   INTERNET'[cnt[0]] if cnt[0] < 11 else ' '),
                    intsep = ( s[0:2] if s[0:2].strip() != '' else
                        (' \\' if cnt[0] % 2 == 0 else ' /')),
                    string = s[2:]
            )
            cb(S,o)
            cnt[0] = cnt[0] + 1
        
        pr('',self)
        
        self.Interfaces.sort( Config.sort_iface )
        self.local_services.sort()
        
        pr("     Open ports: {0}".format(str(self.local_services)),self)
        pr('',self)
        for i in self.Interfaces:
            i.Display( pr )
        pr('',self)
        pr('',self)
        








class Iface:
    """Network interface"""
    
    name = '##'
    
    wan_interface = False
    wan_address = '0.0.0.0'
    
    address = '0.0.0.0'
    dhcp = False
    enabled = False
    
    subnets = None
    
    def __init__( self, name='##', ifconfig=defaultdict(lambda:'undefined'), nets=[] ):
        """Create a new Iface object.
        
        Create a new Iface object, adding all appropriate subnets to its own
        collection."""
        
        self.name = name
        self.subnets = []
        if name in ifconfig['external interface']:
            self.enabled = True
            self.wan_interface = True
            self.wan_address = ' '.join(ifconfig['wan address'])
        elif name in ifconfig['internal interface']:
            self.enabled = True
            for net in nets:
                N = Subnet( net )
                if N.interface != self.name: continue
                self.subnets.append( N )
                nets.remove( net )
        
        ifc = subprocess.Popen( ['/sbin/ifconfig', name], stdout = subprocess.PIPE )
        pipe = subprocess.Popen( [ '/bin/sh', '-c',
            'grep -oP "inet addr:(([0-9]+\.){3}[0-9]+)" | cut -d: -f2'
        ], stdin = ifc.stdout, stdout = subprocess.PIPE )
        ifc.stdout.close()
        self.address = pipe.stdout.read().strip()
        
    def __repr__( self ):
        return "ifx{{name}}".format( name=self.name )
    
    def Display( self, cb ):
        """Create a graphic representation.
        
        Create a graphic representation, calling  cb(S)  for each line  S  to
        be printed."""
        
        cb( '{intsep}{og}{iface:^10s}{fg}   ({addr}){dhcp}'.format(
            intsep = '====' if self.wan_interface else '    ',
            iface = self.name,
            
            og = '[[' if self.enabled else '--',
            fg = ']]' if self.enabled else '--',
            addr = self.address,
            dhcp = 'D' if self.dhcp else ' '
        ), self )
        
        if self.enabled and self.wan_interface:
            cb( '                     <{wan}>'.format(
                wan = self.wan_address
            ), self )
        
        if self.enabled and not self.wan_interface:
            prn = lambda s, o: cb( '         ||   ' + s, o )
        else:
            prn = lambda s, o: cb( '              ' + s, o )
        
        for n in self.subnets:
            n.Display( prn )
        prn('', self)
    
    def new_subnet( self, identifier ):
        try:
            sn = str(int(identifier))
        except ValueError:
            print "Error: Network identifier must be an integer between 1 and 255."
            return None
        SN = Subnet(sn)
        self.subnets.append(SN)
        return SN
    
    def Export( self, dir ):
        """For each subnet, write config files to disk."""
        
        if self.wan_interface or not self.enabled:
            return
        for S in self.subnets:
            S.Export( dir, self.name )
    
    def interfaces_file( self ):
        """Represent itself in a /etc/network/interfaces file."""
        
        if not self.enabled:
            return ""
        if self.wan_interface:
            if self.dhcp:
                s  = "auto {name}\n"
                s += "iface {name} inet dhcp\n"
                s += "name External network interface\n"
                s += "\n"
                return s.format( name = self.name )
            s  = "auto {name}\n"
            s += "iface {name} inet static\n"
            s += "name External network interface\n"
            s += "address   {addr}\n"
            s += "gateway   {pref}.1\n"
            s += "network   {pref}.0\n"
            s += "netmask   255.255.255.0\n"
            s += "broadcast {pref}.255\n"
            s += "\n"
            return s.format(
                    name = self.name,
                    addr = self.address,
                    pref = '.'.join(self.address.split('.')[0:3])
            )
        else:
            rv = "\n\n# Interface {name}\n\n".format(name=self.name)
            c = -1
            for S in self.subnets:
                d = self.name if c == -1 else "{a}:{b}".format(a = self.name, b = c)
                rv += S.interfaces_file( d )
                c += 1
            return rv
    
    
    def subnet_decl( self ):
        """For each subnet, create a representation for the DHCP config file."""
        
        if self.wan_interface or not self.enabled:
            return ""
        
        return "".join(
            [ t.subnet_decl() for t in self.subnets ]
        )
    
    def host_decl( self ):
        """For each host in each subnet, create a representation for the DHCP
        config file."""
        
        return "\t\n".join(
            [ t.host_decl() for t in self.subnets ]
        )


class Subnet:
    """Network subnet"""
    
    name = '##'
    address = '0'
    interface = None
    
    public = False
    
    showhosts = False
    
    hosts = None
    policies = None
    services = [] # TODO: implement
    
    def __init__(self, net):
        nc = parse_file( 'networks/{net}/netconf'.format( net=net ) )
        self.name = ' '.join(nc['friendly name'])
        self.address = net
        self.policies = nc['policies']
        while 'undefined' in self.policies:
            self.policies.remove('undefined')
        hf = list_directory( 'networks/{net}/hosts'.format( net=net ) )
        self.hosts = [Host(t,net) for t in hf]
        self.interface = ' '.join(nc['interface'])
    
    def net( self ):
        """Return the subnet address in the form 192.168.x.0/24."""
        
        return '192.168.{net}.0/24'.format(net=self.address)
    def gw( self ):
        """Return the default gateway, in the form 192.168.x.1."""
        
        return '192.168.{net}.1'.format(net=self.address)
    
    def Export( self, dir, iface ):
        """Write the appropriate config files into {dir}.
        
        Write the appropriate config files into {dir}, ising {iface} as its
        parent Iface object."""
        
        os.mkdir( dir + "/" + self.address )
        os.mkdir( dir + "/" + self.address + '/hosts' )
        
        rv = dict()
        rv['friendly name'] = [self.name]
        rv['interface'] = [iface]
        rv['policies'] = self.policies
        file_put_data( dir + "/" + self.address + '/netconf', rv )
        
        for H in self.hosts:
            H.Export( dir + "/" + self.address + '/hosts' )
    
    
    @staticmethod
    def sort_host( a, b ):
        """Sort function for Host's"""
        
        return a.addr - b.addr
    
    
    def toggle_policy( self, policy ):
        """Add or remove {policy} from the policy list."""
        
        if policy in self.policies:
            i = self.policies.index( policy )
            self.policies.pop(i)
            return False
        else:
            self.policies.append( policy )
            return True
    
    def new_host( self, hostname, mac, ip ):
        try:
            ip = int(ip)
        except ValueError:
            return None
        
        H = Host( hostname, self )
        H.addr = ip
        H.mac = mac
        self.hosts.append(H);
        self.showhosts = True
        
        return H

    def Display( self, cb ):
        """Create a graphic representation.
        
        Create a graphic representation, calling  cb(S)  for each line  S  to
        be printed."""
        
        cb( '{{{{ {name:<30s} ({addr:>3s}) }}}}'.format(
            name = self.name,
            addr = self.address
        ), self )
        cb( '{{{{ {pub:<7s}: {pol:<27s} }}}}'.format(
            pub = 'public' if self.public else 'private',
            pol = ', '.join(self.policies)
        ), self )
        call = lambda s, o: cb( '   ' + s, o )
        self.hosts.sort( Subnet.sort_host )
        if self.showhosts:
            for h in self.hosts:
                h.Display( call )
        cb( '', self )
    
    def interfaces_file( self, iface ):
        """Return an entry for /etc/network/interfaces.
        
        Return an entry for /etc/network/interfaces as a string, using {iface}
        as the network interface name."""
        
        s  = "auto {iface}\n"
        s += "iface {iface} inet static\n"
        s += "name {desc}\n"
        s += "address 192.168.{net}.1\n"
        s += "network 192.168.{net}.0\n"
        s += "netmask 255.255.255.0\n"
        s += "broadcast 192.168.{net}.255\n"
        s += "\n"
        return s.format(
                iface = iface,
                desc = self.name,
                net = self.address
        )
    
    
    def subnet_decl( self ):
        """Return an entry in /etc/dhcp3/dhcpd.conf as a string."""
        
        rv = "\t" + "# Subnet '{desc}'" + "\n" + \
            "\t" + "subnet 192.168.{net}.0 netmask 255.255.255.0 {{" + "\n" + \
            "\t\t" + "range 192.168.{net}.100 192.168.{net}.200;" + "\n" + \
            "\t\t" + "option routers 192.168.{net}.1;" + "\n" + \
            "\t\t" + "option subnet-mask 255.255.255.0;" + "\n" + \
            "\t\t" + "option broadcast-address 192.168.{net}.255;" + "\n" + \
            "\t\t" + "option domain-name \"{sd}\";" + "\n" + \
            "\t\t" + "option domain-name-servers 192.168.{net}.1;" + "\n" + \
            "\t\t" + "" + "\n" + \
            "\t\t" + "{allow} unknown-clients;" + "\n" + \
            "\t" + "}}" + "\n" + \
            "\t" + "" + "\n"
        
        return rv.format(
            desc = self.name,
            net = self.address,
            sd = "todo.inurbanus.nl",
            allow = 'allow' if self.public else 'deny'
        )
    
    def host_decl( self ):
        """Return a string of all host declarations."""
        
        return "".join(
            [ t.host_decl( self.address ) for t in self.hosts ]
        )



class Host:
    """A single network host."""
    
    mac = '';
    addr = '';
    name = '';
    comment = '';
    
    def __init__( self, name, net ):
        self.name = name
        fn = 'networks/{net}/hosts/{name}'.format(
            net=net, name=name
        )
        hf = parse_file( fn )
        self.mac = ' '.join(hf['hardware ethernet'])
        ipaddr = ' '.join(hf['fixed address']).strip().split('.')
        if ipaddr[0] == 'undefined':
            sys.stderr.write( "Invalid file {fn}\n".format(fn=fn) )
        else:
            self.addr = int( ipaddr[3] if len(ipaddr) > 3 else ipaddr[0] )
        cc = ' '.join(hf['comment'])
        self.comment = cc if cc != 'undefined' else ''
    
    def Display( self, cb ):
        """Create a graphic representation.
        
        Create a graphic representation, calling  cb(S)  for each line  S  to
        be printed."""
        
        cb( '* ({ext:>3d}): {mac}  {name}'.format(
            ext = self.addr,
            mac = self.mac,
            name = self.name
        ), self )
        #if len(self.comment) > 0:
        #    cb( '     "{comment}"'.format( comment = self.comment ), self )
    
    def Export( self, dir ):
        """Export a host file to {dir}."""
        
        rv = dict()
        rv['comment'] = [self.comment]
        rv['hardware ethernet'] = [self.mac]
        rv['fixed address'] = [str(self.addr)]
        file_put_data( dir + "/" + self.name, rv )
    
    def host_decl( self, net ):
        """Export a host declaration for dhcpd.conf"""
        
        rv = \
            "\t" + "# {desc}" + "\n" + \
            "\t" + "host {name} {{" + "\n" + \
            "\t\t" + "hardware ethernet {mac};" + "\n" + \
            "\t\t" + "fixed-address 192.168.{net}.{adr};" + "\n" + \
            "\t" + "}}" + "\n"
        
        return rv.format(
            desc = self.comment,
            name = self.name,
            mac = self.mac,
            net = net,
            adr = self.addr
        )



if __name__ == '__main__':
    
    import doctest
    doctest.testmod( optionflags = doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE )
