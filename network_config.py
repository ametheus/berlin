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

def getkey():
    """Capture a single key press.
    
    Capture a key press event, and return the appropriate data in a tuple
    (c,(x,x,x,x)), where c denotes the character value of the key pressed,
    while the (x,x,x,x) tuple contains the numeric value of the 4 original
    bytes. This can be useful if the key pressed has no visible form.
    
    Examples:
    
    Pressing <c>     results in  ('c',(99,0,0,0))
    Pressing <enter> results in  ('\n',(10,0,0,0))
    Pressing <up>    results in  ('', (27,91,65,0))
    Pressing <F12>   results in  ('', (27, 91, 50, 52))"""
    
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    new = termios.tcgetattr(fd)
    new[3] = new[3] & ~termios.ICANON & ~termios.ECHO
    new[6][termios.VMIN] = 1
    new[6][termios.VTIME] = 0
    termios.tcsetattr(fd, termios.TCSANOW, new)
    c = None
    try:
            c = os.read(fd,4)
    finally:
            termios.tcsetattr(fd, termios.TCSAFLUSH, old)
    return (
        c,
        (
            ord(c[0]),
            ord(c[1]) if len(c) > 1 else 0,
            ord(c[2]) if len(c) > 2 else 0,
            ord(c[3]) if len(c) > 3 else 0
        )
    )

def file_put_contents( filename, data ):
    """Write str({data}) to the file {filename}."""
    f = open( filename, 'w' )
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
        f = open( filename, 'r' )
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
    return "\n".join(
        [ ': '.join(r) for r in
            [ (t[0], ' '.join(t[1]) ) for t in data.items() ]]
    ) + "\n\n"


class Config:
    
    Interfaces = None
    ifconfig = None
    
    tion = ( None, None, None )
    drawn = 0
    
    local_services = [ 22, 80, 443, 19360 ] # TODO: implement
    network_services = [ (22222,'192.168.144.2:22') ] # TODO: implement
    
    def __init__( self, network_devices=None ):
        
        self.Interfaces = []
        self.ifconfig = parse_file("config/if-config")
        
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
        try:
            nets = os.listdir('config/networks')
        except(OSError):
            nets = []
        
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
        s = """# This file describes the network interfaces available on your system
# and how to activate them. For more information, see interfaces(5).

# The loopback network interface
auto lo
iface lo inet loopback
"""
        return s + "\n\n".join(
            [ t.interfaces_file() for t in self.Interfaces ]
        )
    
    
    def dhcp_conf( self ):
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
    
    
    
    
    def arrow_key( self, hm ):
        if self.tion[1] == None:
            i = self.Interfaces.index( self.tion[0] ) + hm
            i = i if i >= 0 else 0
            i = i if i < len(self.Interfaces) else len(self.Interfaces) - 1
            self.tion = ( self.Interfaces[i], None, None )
        elif self.tion[2] == None:
            sli = self.tion[0]
            i = sli.subnets.index( self.tion[1] ) + hm
            i = i if i >= 0 else 0
            i = i if i < len(sli.subnets) else len(sli.subnets) - 1
            self.tion = ( sli, sli.subnets[i], None )
        else: 
            sn = self.tion[1]
            i = sn.hosts.index( self.tion[2] ) + hm
            i = i if i >= 0 else 0
            i = i if i < len(sn.hosts) else len(sn.hosts) - 1
            self.tion = ( self.tion[0], sn, sn.hosts[i] )
    
    def UI_loop( self ):
        self.Display( UI_options=True )
        quit = False
        while not quit:
            c = getkey()
            
            if c[1] == (27,91,65,0): # Up arrow
                self.arrow_key( -1 )
            elif c[1] == (27,91,66,0): # Down arrow
                self.arrow_key( 1 )
            
            elif self.tion[1] == None:
                
                # A network interface is selected, but nothing else.
                
                if c[1] == (27,0,0,0): # Escape
                    quit = True
                elif c[1] == (10,0,0,0): # Enter
                    if len(self.tion[0].subnets) > 0:
                        self.tion = ( self.tion[0], self.tion[0].subnets[0], None )
                elif c[0] == '+':
                    self.tion[0].enabled = True
                elif c[0] == '-':
                    self.tion[0].enabled = False
                elif c[0] == 'w':
                    self.tion[0].wan_interface = not self.tion[0].wan_interface
                    if not self.tion[0].wan_interface:
                        self.tion[0].dhcp = False
                    self.tion[0].enabled = True
                elif c[0] == 'd':
                    if self.tion[0].wan_interface:
                        self.tion[0].dhcp = not self.tion[0].dhcp
                elif c[0] == 'a':
                    print "Enter subnet identifier: ",
                    sn = str(int(sys.stdin.readline().strip()))
                    SN = Subnet(sn)
                    self.tion[0].subnets.append(SN)
                    self.tion = ( self.tion[0], SN, None )
                elif c[0] == 'r':
                    print "Enter WAN address: ",
                    self.tion[0].wan_address = sys.stdin.readline().strip()
                elif c[0] == 's':
                    print "Enter port number: ",
                    port = int(sys.stdin.readline().strip())
                    if port in self.local_services:
                        self.local_services.remove(port)
                    else:
                        self.local_services.append(port)
                elif c[1] == (27, 91, 50, 52): # F12
                    self.Export()
                    print """Export complete.
If you blindly trust this script, run the following commands:

sudo mv /tmp/firewall/dhcpd.conf /etc/dhcp3/dhcpd.conf
sudo mv /tmp/firewall/interfaces /etc/network/interfaces
sudo mv /tmp/firewall/if-config /etc/firewall.d/config/if-config
sudo rm -rf /etc/firewall.d/config/networks
sudo mv /tmp/firewall/networks /etc/firewall.d/config
rmdir /tmp/firewall"""
                    sys.stdin.readline()
                else:
                    continue
            
            elif self.tion[2] == None:
                
                # An interface and a subnet are selected
                
                if c[1] == (27,0,0,0): # Escape
                    self.tion = ( self.tion[0], None, None )
                elif c[1] == (10,0,0,0): # Enter
                    if len(self.tion[1].hosts) > 0:
                        self.tion[1].showhosts = True
                        self.tion = ( self.tion[0], self.tion[1], self.tion[1].hosts[0] )
                elif c[0] == 'p':
                    self.tion[1].public = not self.tion[1].public
                elif c[0] == 'n':
                    print "Enter new prefix: ",
                    self.tion[1].address = '192.168.{net}.0'.format(
                        net = sys.stdin.readline().strip()
                    )
                elif c[0] == '+':
                    print " Enter hostname: ",
                    host = sys.stdin.readline().strip()
                    print "Enter MAC address: ",
                    mac = sys.stdin.readline().strip()
                    print "Enter IP extension: ",
                    ip = int(sys.stdin.readline().strip())
                    
                    H = Host( host, self.tion[1] )
                    H.addr = ip
                    H.mac = mac
                    self.tion[1].hosts.append(H);
                    self.tion[1].showhosts = True
                    self.tion = ( self.tion[0], self.tion[1], H )
                elif c[0] == 'c':
                    print "Enter description: ",
                    self.tion[1].name = sys.stdin.readline().strip()
                elif c[0] == '1':
                    self.tion[1].toggle_policy( 'malware' )
                elif c[0] == '2':
                    self.tion[1].toggle_policy( 'adblock' )
                elif c[0] == '3':
                    self.tion[1].toggle_policy( 'kittenwar' )
                elif c[0] == '4':
                    self.tion[1].toggle_policy( 'roberts' )
                else:
                    continue
            
            
            else:
                
                # An interface, subnet, and host are selected
                
                if c[1] == (27,0,0,0): # Escape
                    self.tion[1].showhosts = False
                    self.tion = ( self.tion[0], self.tion[1], None )
                else:
                    continue
            if not quit:
                self.Display( UI_options=True )
    
    def UI_optns( self ):
        print "\n"*( 30 - self.c if self.c < 30 else 1 )
        if self.tion[1] == None:
            print " [+]   Enable interface    [-]   Disable interface   [w]   Toggle WAN interface"
            print " [a]   Add subnet          [d]   Toggle DHCP         [r]   Edit WAN address"
            print " [s]   Add/remove local service"
            print " [F12] Write config                                  [Esc] Exit"
        elif self.tion[2] == None:
            print " [p]   Toggle private      [n]   Set network prefix  [c]   Edit friendly name"
            print " [1]   Toggle 'malware'    [2]   Toggle 'adblock'    [3]   Toggle 'kittenwar'"
            print " [+]   Add host"
            print "                                                     [Esc] Back"
        else:
            print " [c]   Edit IP address     [m]   Edit MAC address   "
            print " [n]   Edit hostname       [d]   Delete host        "
            print ""
            print "                                                     [Esc] Back"
    
    
    
    
    @staticmethod
    def sort_iface( a, b ):
        if ( not a.enabled ) and ( b.enabled ):
            return -1
        if ( a.enabled ) and ( not b.enabled ):
            return 1
        if ( not a.wan_interface ) and ( b.wan_interface ):
            return -1
        if ( a.wan_interface ) and ( not b.wan_interface ):
            return 1
        return 0
    
    
    
    
    c = 0
    def display_line( self, str, obj ):
        
        curs = -1
        if obj == self.tion[0] and self.tion[0] != None and self.drawn < 1:
            curs = 0
            self.drawn = 1
        elif obj == self.tion[1] and self.tion[1] != None and self.drawn < 2:
            curs = 1
            self.drawn = 2
        elif obj == self.tion[2] and self.tion[2] != None and self.drawn < 3:
            curs = 2
            self.drawn = 3
        
        print '  {intc} {intsep}{string:<65s} {cursor:>3s}'.format(
            intc = ('INTERNET'[self.c] if self.c < 8 else ' '),
            intsep = ( str[0:2] if str[0:2] != '  ' else
                (' \\' if self.c % 2 == 0 else ' /')),
            string = str[2:],
            cursor = ('<','<<','<<<')[curs] if curs >= 0 else ''
        )
        self.c += 1
    
    def Display( self, UI_options=False ):
        
        self.c = 0
        self.drawn = 0
        print '\n     /'
        
        self.Interfaces.sort( Config.sort_iface )
        self.local_services.sort()
        
        print "     \\  Open ports: {op}".format(op=str(self.local_services))
        print '     /'
        for i in self.Interfaces:
            i.Display( lambda s, o: self.display_line(s, o) )
        print ('     \\' if self.c % 2 == 0 else '     /')
        if UI_options:
            self.UI_optns()








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
    
    def Export( self, dir ):
        if self.wan_interface or not self.enabled:
            return
        for S in self.subnets:
            S.Export( dir, self.name )
    
    def interfaces_file( self ):
        if not self.enabled:
            return ""
        if self.wan_interface:
            if self.dhcp:
                return """auto {name}
iface {name} inet dhcp
name External network interface

""".format( name = self.name )
            return """auto {name}
iface {name} inet static
name External network interface
address   {addr}
gateway   {pref}.1
network   {pref}.0
netmask   255.255.255.0
broadcast {pref}.255

""".format(
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
        if self.wan_interface or not self.enabled:
            return ""
        
        return "".join(
            [ t.subnet_decl() for t in self.subnets ]
        )
    
    def host_decl( self ):
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
        nc = parse_file( 'config/networks/{net}/netconf'.format( net=net ) )
        self.name = ' '.join(nc['friendly name'])
        self.address = net
        self.policies = nc['policies']
        while 'undefined' in self.policies:
            self.policies.remove('undefined')
        try:
            hf = os.listdir( 'config/networks/{net}/hosts'.format( net=net ) )
        except (IOError, OSError):
            self.hosts = []
        else:
            self.hosts = [Host(t,net) for t in hf]
        self.interface = ' '.join(nc['interface'])
    
    def net( self ):
        return '192.168.{net}.0/24'.format(net=self.address)
    def gw( self ):
        return '192.168.{net}.1'.format(net=self.address)
    
    def Export( self, dir, iface ):
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
        return a.addr - b.addr
    
    
    def toggle_policy( self, policy ):
        if policy in self.policies:
            i = self.policies.index( policy )
            self.policies.pop(i)
            return False
        else:
            self.policies.append( policy )
            return True

    def Display( self, cb ):
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
        return """auto {iface}
iface {iface} inet static
name {desc}
address 192.168.{net}.1
network 192.168.{net}.0
netmask 255.255.255.0
broadcast 192.168.{net}.255


""".format(
            iface = iface,
            desc = self.name,
            net = self.address
        )
    
    
    def subnet_decl( self ):
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
        return "".join(
            [ t.host_decl( self.address ) for t in self.hosts ]
        )



class Host:
    
    mac = '';
    addr = '';
    name = '';
    comment = '';
    
    def __init__( self, name, net ):
        self.name = name
        fn = 'config/networks/{net}/hosts/{name}'.format(
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
        cb( '* ({ext:>3d}): {mac}  {name}'.format(
            ext = self.addr,
            mac = self.mac,
            name = self.name
        ), self )
        #if len(self.comment) > 0:
        #    cb( '     "{comment}"'.format( comment = self.comment ), self )
    
    def Export( self, dir ):
        rv = dict()
        rv['comment'] = [self.comment]
        rv['hardware ethernet'] = [self.mac]
        rv['fixed address'] = [str(self.addr)]
        file_put_data( dir + "/" + self.name, rv )
    
    def host_decl( self, net ):
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
    doctest.testmod()
