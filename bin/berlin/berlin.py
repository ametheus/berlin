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

# Kittenwar server
KW = '205.196.209.62'

from ruleset import Ruleset
from output import debug

class Berlin(Ruleset):
    
    malware_blocked = False
    ads_blocked = False
    
    def malware( self, Net ):
        """Apply the 'malware' policy to the subnet."""
        
        if not self.malware_blocked:
            self.create_filter( 'malware_filter', ["malware-hosts"] )
            self.malware_blocked = True
        
        self.append_chain(
            'PREROUTING',
            '-s {0} -p tcp -m tcp --dport 80 -m state --state NEW,RELATED,ESTABLISHED '
                '-g malware_filter'.format( Net.net() ),
            table='nat'
        )
    
    def adblock( self, Net ):
        """Apply the 'adblock' policy to the subnet."""
        
        if not self.ads_blocked:
            self.create_filter( 'ad_filter', ["ad-hosts","malware-hosts"] )
            self.ads_blocked = True
        
        self.append_chain(
            'PREROUTING',
            '-s {0} -p tcp -m tcp --dport 80 -m state --state NEW,RELATED,ESTABLISHED '
                '-g ad_filter'.format( Net.net() ),
            table='nat'
        )
    
    def qos_chains( self ):
        """Generate chains needed for QoS.
        
        There are 7 priority levels in all. They are, in descending order:
        
        1:  Low volume connections that benefit from low delay, such as dns,
            icmp, irc, quake3, minecraft, and packets with the SYN flag.
            These packets have the highest priority, but there's a speed cap
            so as not to smother everything else.
        2:  SSH traffic. Very low latency, unlimited speed.
        3:  Packets with the Maximize-Throughput bit set, and any traffic from
            the local server itself.
        4:  HTTP/HTTPS requests, both from network clients to the internet, 
            and from the internet to a local webserver.
        5:  Network hosts that require special priority treatment.
        6:  E-mail traffic and packets with Minimize-Cost TOS bit set.
        7:  Everything not in any of the above categories."""
        
        self.new_chain('PREROUTING', 'mangle', 'ACCEPT',
                'Assign priorities to different packets according to fixed, simple rules.')
        self.new_chain('OUTPUT', 'mangle', 'ACCEPT',
                'Assign priorities to different packets according to fixed, simple rules.')
        
        
        self.append_chain('PREROUTING','-p icmp -j MARK --set-mark 0x1',                                    table='mangle')
        self.append_chain('PREROUTING','-p icmp -j RETURN',                                                 table='mangle')
        self.append_chain('PREROUTING','-p tcp -m tcp --tcp-flags SYN,RST,ACK SYN -j MARK --set-mark 0x1',  table='mangle')
        self.append_chain('PREROUTING','-p tcp -m tcp --tcp-flags SYN,RST,ACK SYN -j RETURN',               table='mangle')
        self.append_chain('PREROUTING','-m tos --tos Minimize-Delay -j MARK --set-mark 0x1',                table='mangle')
        self.append_chain('PREROUTING','-m tos --tos Minimize-Delay -j RETURN',                             table='mangle')
        self.append_chain('PREROUTING','-p tcp -m multiport --dports 194,25565 -j MARK --set-mark 0x1',     table='mangle')
        self.append_chain('PREROUTING','-p tcp -m multiport --dports 194,25565 -j RETURN',                  table='mangle')
        self.append_chain('PREROUTING','-p tcp -m multiport --sports 194,25565 -j MARK --set-mark 0x1',     table='mangle')
        self.append_chain('PREROUTING','-p tcp -m multiport --sports 194,25565 -j RETURN',                  table='mangle')
        
        self.append_chain('PREROUTING','-p tcp -m tcp --sport 22 -j MARK --set-mark 0x2',                   table='mangle')
        self.append_chain('PREROUTING','-p tcp -m tcp --sport 22 -j RETURN',                                table='mangle')
        self.append_chain('PREROUTING','-p tcp -m tcp --dport 22 -j MARK --set-mark 0x2',                   table='mangle')
        self.append_chain('PREROUTING','-p tcp -m tcp --dport 22 -j RETURN',                                table='mangle')
        
        self.append_chain('PREROUTING','-m tos --tos Maximize-Throughput -j MARK --set-mark 0x3',           table='mangle')
        self.append_chain('PREROUTING','-m tos --tos Maximize-Throughput -j RETURN',                        table='mangle')
        self.append_chain('OUTPUT',    '-j MARK --set-mark 0x3',                                            table='mangle')
        self.append_chain('OUTPUT',    '-j RETURN',                                                         table='mangle')
        
        self.append_chain('PREROUTING','-p tcp -m multiport --dports 80,443,8106 -j MARK --set-mark 0x4',   table='mangle')
        self.append_chain('PREROUTING','-p tcp -m multiport --dports 80,443,8106 -j RETURN',                table='mangle')
        self.append_chain('PREROUTING','-p tcp -m multiport --sports 80,443,8106 -j MARK --set-mark 0x4',   table='mangle')
        self.append_chain('PREROUTING','-p tcp -m multiport --sports 80,443,8106 -j RETURN',                table='mangle')
        
        #  ( Priority 5 is currently not implemented )
        
        self.append_chain('PREROUTING','-m tos --tos Minimize-Cost -j MARK --set-mark 0x6',                 table='mangle')
        self.append_chain('PREROUTING','-m tos --tos Minimize-Cost -j RETURN',                              table='mangle')
        self.append_chain('PREROUTING','-p tcp -m multiport --dports 25,110,465,587,993,994 -j MARK --set-mark 0x6',table='mangle')
        self.append_chain('PREROUTING','-p tcp -m multiport --dports 25,110,465,587,993,994 -j RETURN',     table='mangle')
        self.append_chain('PREROUTING','-p tcp -m multiport --sports 25,110,465,587,993,994 -j MARK --set-mark 0x6',table='mangle')
        self.append_chain('PREROUTING','-p tcp -m multiport --sports 25,110,465,587,993,994 -j RETURN',     table='mangle')
        
        self.append_chain('PREROUTING','-j MARK --set-mark 0x7',                                            table='mangle')
    
    def import_config( self, C ):
        """Create a NAT firewall using the settings from {C}.
        
        Examples:
        
        >>> V = Berlin()
        >>> from network_config import Config
        >>> C = Config()
        >>> V.import_config(C)
        
        """
        
        Ext = [ t for t in C.Interfaces if t.enabled and     t.wan_interface ]
        Int = [ t for t in C.Interfaces if t.enabled and not t.wan_interface ]
        
        debug( 0, "Generating rules..." )
        
        self.reset()
        if len([ I for I in Ext if I.qos_bandwidth ]):
            self.qos_chains()
        
        self.append_chain('INPUT','#Loopback interface is valid' )
        self.append_chain('INPUT','-i lo -j ACCEPT')
        
        self.append_chain('INPUT','# All other internal traffic is limited to the interface' )
        for I in Int:
            for N in I.subnets:
                self.append_chain('INPUT','-s {1} -i {0} -j ACCEPT'.format(I.name,N.net()))
        
        self.append_chain('INPUT','# Remote interface, claiming to be local machines, IP spoofing, get lost!' )
        for I in Int:
            for N in I.subnets:
                for E in Ext:
                    self.append_chain('INPUT','-s {1} -i {0} -j REJECT --reject-with icmp-port-unreachable'.format(
                        E.name, N.net() ))
        
        self.append_chain('INPUT','# External interfaces, from any source, for ICMP traffic is valid.' )
        for E in Ext:
            self.append_chain('INPUT','-d {1}/32 -i {0} -p icmp -j ACCEPT'.format(
                E.name, E.address ))
        
        self.append_chain('INPUT','# Allow any related traffic coming back to the MASQ server in.' )
        for E in Ext:
            self.append_chain('INPUT','-d {1}/32 -i {0} -m state '
                    '--state RELATED,ESTABLISHED -j ACCEPT'.format(
                        E.name, E.address
                    ))
        
        
        self.append_chain('INPUT','# Allow internal DHCP/DNS traffic.' )
        for I in Int:
            self.append_chain('INPUT','-i {0} -p tcp -m tcp --sport 68 --dport 67 -j ACCEPT'.format(I.name))
            self.append_chain('INPUT','-i {0} -p udp -m udp --sport 68 --dport 67 -j ACCEPT'.format(I.name))
            
            self.append_chain('INPUT','-i {0} -p tcp -m tcp --dport 53 -j ACCEPT'.format(I.name))
            self.append_chain('INPUT','-i {0} -p udp -m udp --dport 53 -j ACCEPT'.format(I.name))
        
        self.append_chain('INPUT','# Internal appliances (not implemented)' )
        for I in Int:
         for N in I.subnets:
          for P in N.services:
            self.append_chain('INPUT','-i {0} -p tcp --dport {1} -s {2} -j ACCEPT'.format(
                    I.name, P, N.net() ))
        
        self.append_chain('INPUT','# Remote services' )
        for P in C.local_services:
            for E in Ext:
                self.append_chain('INPUT','-d {1}/32 -i {0} -p tcp -m state --state '
                             'NEW,RELATED,ESTABLISHED -m tcp --dport {2} -j ACCEPT'.format(
                    E.name, E.address, P
                ))
            debug( -2, '     TCP port {0} is open for business.'.format(P) )
        
        self.append_chain('INPUT','# Active FTP' )
        self.append_chain('INPUT','-m helper --helper "ftp" -j ACCEPT')
        
        self.append_chain('INPUT','# Reject everything else.' )
        self.append_chain('INPUT','-j REJECT --reject-with icmp-port-unreachable')
        
        self.append_chain('OUTPUT','# Workaround bug in netfilter' )
        self.append_chain('OUTPUT','-p icmp -m state --state INVALID -j DROP')
        
        self.append_chain('OUTPUT','# Loopback interface is valid' )
        self.append_chain('OUTPUT','-o lo -j ACCEPT')
        
        self.append_chain('OUTPUT','# Local interfaces, any source going to local net is valid' )
        for E in Ext:
            for I in Int:
                for N in I.subnets:
                    self.append_chain('OUTPUT','-s {1}/32 -d {2} -o {0} -j ACCEPT'.format(
                        I.name, E.address, N.net() ))
        
        self.append_chain('OUTPUT','# Local interface, MASQ server source going to a local net is valid' )
        for I in Int:
            for N in I.subnets:
                self.append_chain('OUTPUT','-s {1}/32 -d {2} -o {0} -j ACCEPT'.format(
                    I.name, N.gw(), N.net() ))
        
        self.append_chain('OUTPUT','# Outgoing to local net on remote interface, stuffed routing, deny' )
        for E in Ext:
            for I in Int:
                for N in I.subnets:
                    self.append_chain('OUTPUT','-d {1} -o {0} -j REJECT --reject-with icmp-port-unreachable'.format(
                        E.name, N.net() ))
        
        self.append_chain('OUTPUT','# Anything else outgoing on remote interface is valid.' )
        for E in Ext:
            self.append_chain('OUTPUT','-s {1}/32 -o {0} -j ACCEPT'.format(
                E.name, E.address ))
        
        self.append_chain('OUTPUT','# Internal interface, DHCP traffic accepted' )
        for I in Int:
            for N in I.subnets:
                self.append_chain('OUTPUT','-s {1}/32 -d 255.255.255.255/32 '
                             '-o {0} -p tcp -m tcp '
                             '--sport 67 --dport 68 -j ACCEPT'.format(
                    I.name, N.gw() ))
                self.append_chain('OUTPUT','-s {1}/32 -d 255.255.255.255/32 '
                             '-o {0} -p udp -m udp '
                             '--sport 67 --dport 68 -j ACCEPT'.format(
                    I.name, N.gw() ))
        
        debug( -1, 'Catch all rule, all other outgoing is denied and logged.' )
        self.append_chain('OUTPUT','-j REJECT --reject-with icmp-port-unreachable')
        
        
        
        
        
        self.append_chain('FORWARD','# Reject all SMTP traffic save for a few trusted destinations' )
        self.create_filter( 'smtp_filter', ["smtp-hosts"], table='filter',
                      action='-j ACCEPT')
        self.append_chain( 'smtp_filter', '-j LOG --log-prefix "  [SMTP] "' )
        self.append_chain( 'smtp_filter', '-j REJECT --reject-with icmp-port-unreachable' )
        for E in Ext:
            for I in Int:
                self.append_chain('FORWARD',' -p tcp -m tcp --dport 25  '
                             '-j LOG --log-prefix "  [SMTP] "'.format(
                    E.name, I.name ))
                self.append_chain('FORWARD',' -p tcp -m tcp --dport 25  '
                             '-j REJECT --reject-with icmp-port-unreachable'.format(
                    E.name, I.name ))
                self.append_chain('FORWARD',' -p tcp -m tcp --dport 587  '
                             '-g smtp_filter'.format(
                    E.name, I.name ))
                self.append_chain('FORWARD',' -p tcp -m tcp --dport 465  '
                             '-g smtp_filter'.format(
                    E.name, I.name ))
        
        
        self.append_chain('FORWARD','-m state --state RELATED,ESTABLISHED -j ACCEPT')
        
        self.append_chain('FORWARD','# Network services' )
        for E in Ext:
            for port,host in C.network_services:
                self.append_chain(
                    'PREROUTING',
                    '-d {1}/32 -i {0} -p tcp -m tcp --dport {2} -j DNAT --to-destination {3}'.format(
                        E.name, E.address, port, host ),
                    table='nat')
                self.append_chain('FORWARD','-i {0} -p tcp -m state --state NEW -m tcp --dport {1} -j ACCEPT'.format(
                    E.name, port ))
        
        self.append_chain('PREROUTING','# Redirect traffic to wan address to this gateway',table='nat')
        for E in Ext:
            if E.wan_address == E.address: continue
            for I in Int:
                for N in I.subnets:
                    self.append_chain(
                        'PREROUTING',
                        '-p tcp -s {0} -d {1} -m state --state NEW,ESTABLISHED,RELATED '
                        '-j DNAT --to {2}'.format(
                            N.net(), E.wan_address, N.gw() ),
                        table='nat')
        
        self.append_chain('FORWARD','# Accept solicited tcp packets' )
        for E in Ext:
            for I in Int:
                self.append_chain('FORWARD','-i {0} -o {1} '
                             '-m state --state RELATED,ESTABLISHED -j ACCEPT'.format(
                    E.name, I.name ))
        
        self.append_chain('FORWARD','# Allow packets within subnet' )
        for I in Int:
            self.append_chain('FORWARD','-i {0} -o {0} -j ACCEPT'.format(I.name))
        
        self.append_chain('FORWARD','# Forward packets from the internal network to the Internet.' )
        for I in Int:
            for E in Ext:
                self.append_chain('FORWARD','-i {0} -o {1} -j ACCEPT'.format(I.name,E.name))
        
        self.append_chain('FORWARD','# Catch-all REJECT rule' )
        self.append_chain('FORWARD','-j REJECT --reject-with icmp-port-unreachable')
        
        self.append_chain('POSTROUTING','# IP-Masquerade',table='nat')
        for E in Ext:
            self.append_chain(
                'POSTROUTING',
                '-o {0} -j SNAT --to-source {1}'.format(E.name,E.address),
                table='nat')
        
        debug( 0, 'done.' )
        
        debug( 0, '' )
        debug( 0, 'Applying policies:' )
        
        
        debug( -1, 'Creating "to Gateway" chain.' )
        self.new_chain( 'to_gateway', table='nat', policy='-' )
        self.append_chain('PREROUTING','# Local nat traffic is allowed',table='nat')
        for I in Int:
            for N in I.subnets:
                self.append_chain( 
                    'PREROUTING',
                    '-s {0} -d {0} -p tcp -m tcp --dport 80 -m state --state '
                        'NEW,RELATED,ESTABLISHED -j ACCEPT'.format(N.net()),
                    table='nat'
                )
                self.append_chain(
                    'to_gateway',
                    '-s {0} -j DNAT --to-destination {1}'.format( N.net(), N.gw() ),
                    table='nat'
                )
        self.append_chain('to_gateway', '-j LOG --log-prefix "   [impossible]"', table='nat')
        
        
        for I in Int:
            for N in I.subnets:
                if 'adblock' in N.policies:
                    self.adblock( N )
                elif 'malware' in N.policies:
                    self.malware( N )


if __name__ == '__main__':
    import doctest
    fail, total = doctest.testmod( optionflags = doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE )
    import sys
    sys.exit( fail )
