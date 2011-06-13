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

import network_config
from getpass import getuser

import os,sys
import shlex, subprocess

# Kittenwar server
KW = '205.196.209.62'


# Debug level
#  2 = Nothing, not even errors
#  1 = Just errors
#  0 = Helpful status messages
# -1 = Chatty
# -2 = Blabbermouth
debuglevel = 1


def debug( importance, str, newline=True ):
    """Send {str} to stdout. Maybe.
    
    If {importance} is high enough, send {str} to stdout."""
    
    if importance >= debuglevel:
        sys.stdout.write( "{0}{1}".format( str, "\n" if newline else "" ) )

all_chains = dict({})

def initialize_chains():
    """Create default empty tables and chains."""
    
    global all_chains
    global malware_blocked, ads_blocked
    
    all_chains = dict({})
    for tb in ['nat','filter']:
        all_chains[tb] = dict()
    
    # Initialize default chains
    new_chain('PREROUTING', 'nat',      'ACCEPT')
    new_chain('POSTROUTING','nat',      'ACCEPT')
    new_chain('OUTPUT',     'nat',      'ACCEPT')
    new_chain('INPUT',      'filter',   'DROP')
    new_chain('FORWARD',    'filter',   'DROP')
    new_chain('OUTPUT',     'filter',   'DROP')
    
    
    malware_blocked = False
    ads_blocked = False

def new_chain(chain,table='filter',policy='DROP'):
    """Add a new chain.
    
    Add a new chain {chain} to {table} with default policy {policy}."""
    
    global all_chains
    
    if not table in all_chains:
        raise Exception("Invalid table {0}. Keys: {1}".format(table,all_chains.keys()))
    if not chain in all_chains[table]:
        all_chains[table][chain] = dict({
            'policy': policy,
            'rules': []
        })
    else:
        raise Exception("Chain {0} in table {1} already exists.")

def append_chain( chain, rule, table='filter', comments=False ):
    """Append a rule to a chain.
    
    Append {rule} to {chain} in {table}."""
    
    global all_chains
    if not chain in all_chains[table]:
        raise Exception("Chain '{0}' does not yet exist. Try creating it explicitly.")
    
    all_chains[table][chain]['rules'].append(rule)
    
    
    




malware_blocked = False
ads_blocked = False

def malware( Net ):
    """Apply the 'malware' policy to the subnet."""
    
    global malware_blocked
    
    if not malware_blocked:
        create_filter( 'malware_filter', ["config/malware-hosts"] )
        malware_blocked = True
    append_chain(
        'PREROUTING',
        '-s {0} -p tcp -m tcp --dport 80 -m state --state NEW,RELATED,ESTABLISHED '
            '-g malware_filter'.format( Net.net() ),
        table='nat'
    )
def adblock( Net ):
    """Apply the 'adblock' policy to the subnet."""
    
    global ads_blocked
    
    if not ads_blocked:
        create_filter( 'ad_filter', ["config/ad-hosts","config/malware-hosts"] )
        ads_blocked = True
    append_chain(
        'PREROUTING',
        '-s {0} -p tcp -m tcp --dport 80 -m state --state NEW,RELATED,ESTABLISHED '
            '-g ad_filter'.format( Net.net() ),
        table='nat'
    )

def IP_addresses_from_files( filenames ):
    """Return all valid IPv4 addresses """
    
    f = subprocess.Popen( ['cat'] + filenames, stdout = subprocess.PIPE )
    gr = subprocess.Popen(
        ['sh','-c','grep -oP "([0-9]{1,3}\.){3}[0-9]{1,3}" | sort | uniq'],
        stdin = f.stdout, stdout = subprocess.PIPE
    )
    f.stdout.close()
    s = gr.stdout.read()
    gr.stdout.close()
    return s.split()

def create_filter( name, files, table='nat', action='-g to_gateway' ):
    """Create an outbound filter.
    
    Create a separate filter chain called {name}. As soon as a tcp packet is
    detected to an IP address in any one of the files in {files}, the {action}
    is performed."""
    
    global anything_blocked
    
    addresses = IP_addresses_from_files( files )
    new_chain( name, table=table, policy='-' )
    
    for IP in addresses:
        append_chain(
            name,
            '-d {0}/32 -p tcp {1}'.format(IP,action),
            table=table
        )






def output_chains():
    """Export all chains in iptables-restore format."""
    
    global all_chains
    
    counters = dict({
        'filter': ['INPUT','FORWARD','OUTPUT'],
        'nat': ['PREROUTING','POSTROUTING','OUTPUT']
    })
    
    fn = '/etc/firewall.d/rules' if getuser() == 'root' else '/tmp/rules'
    f = open(fn,'w')
    
    for tb in ['nat','filter']:
        table = all_chains[tb]
        f.write('*{0}\n'.format(tb))
        
        # Write the chain declarations for all buitin chains
        for ch in counters[tb]:
            f.write(':{0} {1} [0:0]\n'.format(ch,table[ch]['policy']))
        
        # Write the chain declarations for all user-defined chains
        for ch,chain in table.items():
            if ch in counters[tb]: continue
            f.write('-N {0}\n'.format(ch))
            if chain['policy'] != '-':
                f.write('-P {0} {1}\n'.format(ch,chain['policy']))
        
        # Write all the rules for the user-defined chains
        for ch,chain in table.items():
            for r in chain['rules']:
                if not r:
                    f.write('\n')
                elif r[0] == '#':
                    f.write( '{0}\n'.format(r) )
                else:
                    f.write('-A {0} {1}\n'.format(ch,r))
        
        # Commit everything.
        f.write('COMMIT\n')
    
    f.close()







if __name__ == '__main__':
    
    if '-d' in sys.argv:
        x = sys.argv.index('-d')+1
        if len(sys.argv) > x:
            debuglevel = int(sys.argv[x])
    
    if getuser() == 'root':
        debug( -1, "Restarting BIND" )
        subprocess.call([ 'service', 'bind9', 'start' ])
        
        debug( -1, "Enabling IP forwarding" )
        subprocess.call([ 'sh', '-c',
            'echo 1 > /proc/sys/net/ipv4/ip_forward' ])
    else:
        debug( 1, "Note: you are not root." )
    debug( 0, "Detecting configuration... ", False )
    C = network_config.Config()
    
    Ext = [ t for t in C.Interfaces if t.enabled and     t.wan_interface ]
    Int = [ t for t in C.Interfaces if t.enabled and not t.wan_interface ]
    
    debug( 0, "done." )
    
    debug( 0, "Generating rules..." )
    
    initialize_chains()
    
    append_chain('INPUT',None)
    append_chain('INPUT',None)
    append_chain('INPUT','#   INPUT: Incoming traffic from various interfaces')
    append_chain('INPUT',None)
    
    append_chain('INPUT','#Loopback interface is valid' )
    append_chain('INPUT','-i lo -j ACCEPT')
    
    append_chain('INPUT','# All other internal traffic is limited to the interface' )
    for I in Int:
        for N in I.subnets:
            append_chain('INPUT','-s {1} -i {0} -j ACCEPT'.format(I.name,N.net()))
    
    append_chain('INPUT','# Remote interface, claiming to be local machines, IP spoofing, get lost!' )
    for I in Int:
        for N in I.subnets:
            for E in Ext:
                append_chain('INPUT','-s {1} -i {0} -j REJECT --reject-with icmp-port-unreachable'.format(
                    E.name, N.net() ))
    
    append_chain('INPUT','# External interfaces, from any source, for ICMP traffic is valid.' )
    for E in Ext:
        append_chain('INPUT','-d {1}/32 -i {0} -p icmp -j ACCEPT'.format(
            E.name, E.address ))
    
    append_chain('INPUT','# Allow any related traffic coming back to the MASQ server in.' )
    for E in Ext:
        append_chain('INPUT','-d {1}/32 -i {0} -m state '
                '--state RELATED,ESTABLISHED -j ACCEPT'.format(
                    E.name, E.address
                ))
    
    
    append_chain('INPUT','# Allow internal DHCP/DNS traffic.' )
    for I in Int:
        append_chain('INPUT','-i {0} -p tcp -m tcp --sport 68 --dport 67 -j ACCEPT'.format(I.name))
        append_chain('INPUT','-i {0} -p udp -m udp --sport 68 --dport 67 -j ACCEPT'.format(I.name))
        
        append_chain('INPUT','-i {0} -p tcp -m tcp --dport 53 -j ACCEPT'.format(I.name))
        append_chain('INPUT','-i {0} -p udp -m udp --dport 53 -j ACCEPT'.format(I.name))
    
    append_chain('INPUT','# Internal appliances (not implemented)' )
    for I in Int:
     for N in I.subnets:
      for P in N.services:
        append_chain('INPUT','-i {0} -p tcp --dport {1} -s {2} -j ACCEPT'.format(
            I.name, P, N.net()
        ))
    
    append_chain('INPUT','# Remote services' )
    for P in C.local_services:
        for E in Ext:
            append_chain('INPUT','-d {1}/32 -i {0} -p tcp -m state --state '
                         'NEW,RELATED,ESTABLISHED -m tcp --dport {2} -j ACCEPT'.format(
                E.name, E.address, P
            ))
        debug( -2, '     TCP port {0} is open for business.'.format(P) )
    
    append_chain('INPUT','# Active FTP' )
    if getuser() == 'root':
        subprocess.call(['/sbin/modprobe', 'ip_conntrack_ftp'])
        subprocess.call(['/sbin/modprobe', 'ip_nat_ftp'])
    else:
        debug( 0, 'You are not root; therefore unable to load module ip_conntrack_ftp' )
    append_chain('INPUT','-m helper --helper "ftp" -j ACCEPT')
    
    append_chain('INPUT','# Reject everything else.' )
    append_chain('INPUT','-j REJECT --reject-with icmp-port-unreachable')
    
    append_chain('OUTPUT',None)
    append_chain('OUTPUT',None)
    append_chain('OUTPUT','#   OUTPUT: Outgoing traffic from various interfaces #' )
    append_chain('OUTPUT',None)
    
    append_chain('OUTPUT','# Workaround bug in netfilter' )
    append_chain('OUTPUT','-p icmp -m state --state INVALID -j DROP')
    
    append_chain('OUTPUT','# Loopback interface is valid' )
    append_chain('OUTPUT','-o lo -j ACCEPT')
    
    append_chain('OUTPUT','# Local interfaces, any source going to local net is valid' )
    for E in Ext:
        for I in Int:
            for N in I.subnets:
                append_chain('OUTPUT','-s {1}/32 -d {2} -o {0} -j ACCEPT'.format(
                    I.name, E.address, N.net() ))
    
    append_chain('OUTPUT','# Local interface, MASQ server source going to a local net is valid' )
    for I in Int:
        for N in I.subnets:
            append_chain('OUTPUT','-s {1}/32 -d {2} -o {0} -j ACCEPT'.format(
                I.name, N.gw(), N.net() ))
    
    append_chain('OUTPUT','# Outgoing to local net on remote interface, stuffed routing, deny' )
    for E in Ext:
        for I in Int:
            for N in I.subnets:
                append_chain('OUTPUT','-d {1} -o {0} -j REJECT --reject-with icmp-port-unreachable'.format(
                    E.name, N.net() ))
    
    append_chain('OUTPUT','# Anything else outgoing on remote interface is valid.' )
    for E in Ext:
        append_chain('OUTPUT','-s {1}/32 -o {0} -j ACCEPT'.format(
            E.name, E.address ))
    
    append_chain('OUTPUT','# Internal interface, DHCP traffic accepted' )
    for I in Int:
        for N in I.subnets:
            append_chain('OUTPUT','-s {1}/32 -d 255.255.255.255/32 '
                         '-o {0} -p tcp -m tcp '
                         '--sport 67 --dport 68 -j ACCEPT'.format(
                I.name, N.gw() ))
            append_chain('OUTPUT','-s {1}/32 -d 255.255.255.255/32 '
                         '-o {0} -p udp -m udp '
                         '--sport 67 --dport 68 -j ACCEPT'.format(
                I.name, N.gw() ))
    
    debug( -1, 'Catch all rule, all other outgoing is denied and logged.' )
    append_chain('OUTPUT','-j REJECT --reject-with icmp-port-unreachable')
    
    
    
    
    
    append_chain('FORWARD',None)
    append_chain('FORWARD',None)
    append_chain('FORWARD','# Packet Forwarding / NAT' )
    append_chain('FORWARD',None)
    
    
    
    append_chain('FORWARD','# Reject all SMTP traffic save for a few trusted destinations' )
    create_filter( 'smtp_filter', ["config/smtp-hosts"], table='filter',
                  action='-j ACCEPT')
    append_chain( 'smtp_filter', '-j LOG --log-prefix "  [SMTP] "' )
    append_chain( 'smtp_filter', '-j REJECT --reject-with icmp-port-unreachable' )
    for E in Ext:
        for I in Int:
            append_chain('FORWARD',' -p tcp -m tcp --dport 25  '
                         '-j LOG --log-prefix "  [SMTP] "'.format(
                E.name, I.name ))
            append_chain('FORWARD',' -p tcp -m tcp --dport 25  '
                         '-j REJECT --reject-with icmp-port-unreachable'.format(
                E.name, I.name ))
            append_chain('FORWARD',' -p tcp -m tcp --dport 587  '
                         '-g smtp_filter'.format(
                E.name, I.name ))
            append_chain('FORWARD',' -p tcp -m tcp --dport 465  '
                         '-g smtp_filter'.format(
                E.name, I.name ))
    
    
    append_chain('FORWARD','-m state --state RELATED,ESTABLISHED -j ACCEPT')
    
    append_chain('FORWARD','# Network services' )
    for E in Ext:
        for port,host in C.network_services:
            append_chain(
                'PREROUTING',
                '-d {1}/32 -i {0} -p tcp -m tcp --dport {2} -j DNAT --to-destination {3}'.format(
                    E.name, E.address, port, host ),
                table='nat')
            append_chain('FORWARD','-i {0} -p tcp -m state --state NEW -m tcp --dport {1} -j ACCEPT'.format(
                E.name, port ))
    
    append_chain('PREROUTING','# Redirect traffic to wan address to this gateway',table='nat')
    for E in Ext:
        if E.wan_address == E.address: continue
        for I in Int:
            for N in I.subnets:
                append_chain(
                    'PREROUTING',
                    '-p tcp -s {0} -d {1} -m state --state NEW,ESTABLISHED,RELATED '
                    '-j DNAT --to {2}'.format(
                        N.net(), E.wan_address, N.gw() ),
                    table='nat')
    
    append_chain('FORWARD','# Accept solicited tcp packets' )
    for E in Ext:
        for I in Int:
            append_chain('FORWARD','-i {0} -o {1} '
                         '-m state --state RELATED,ESTABLISHED -j ACCEPT'.format(
                E.name, I.name ))
    
    append_chain('FORWARD','# Allow packets within subnet' )
    for I in Int:
        append_chain('FORWARD','-i {0} -o {0} -j ACCEPT'.format(I.name))
    
    append_chain('FORWARD','# Forward packets from the internal network to the Internet.' )
    for I in Int:
        for E in Ext:
            append_chain('FORWARD','-i {0} -o {1} -j ACCEPT'.format(I.name,E.name))
    
    append_chain('FORWARD','# Catch-all REJECT rule' )
    append_chain('FORWARD','-j REJECT --reject-with icmp-port-unreachable')
    
    append_chain('POSTROUTING','# IP-Masquerade',table='nat')
    for E in Ext:
        append_chain(
            'POSTROUTING',
            '-o {0} -j SNAT --to-source {1}'.format(E.name,E.address),
            table='nat')
    
    debug( 0, 'done.' )
    
    debug( 0, '' )
    debug( 0, 'Applying policies:' )
    
    
    debug( -1, 'Creating "to Gateway" chain.' )
    new_chain( 'to_gateway', table='nat', policy='-' )
    append_chain('PREROUTING','# Local nat traffic is allowed',table='nat')
    for I in Int:
        for N in I.subnets:
            append_chain( 
                'PREROUTING',
                '-s {0} -d {0} -p tcp -m tcp --dport 80 -m state --state '
                    'NEW,RELATED,ESTABLISHED -j ACCEPT'.format(N.net()),
                table='nat'
            )
            append_chain(
                'to_gateway',
                '-s {0} -j DNAT --to-destination {1}'.format( N.net(), N.gw() ),
                table='nat'
            )
    append_chain('to_gateway', '-j LOG --log-prefix "   [impossible]"', table='nat')
    
    
    for I in Int:
        for N in I.subnets:
            if 'adblock' in N.policies:
                adblock( N )
            elif 'malware' in N.policies:
                malware( N )
    
    output_chains()
    
    
