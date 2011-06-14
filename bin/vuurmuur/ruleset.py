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

import subprocess

# Kittenwar server
KW = '205.196.209.62'

class Ruleset:
    """A collection of iptables rules.
    
    A collection of iptables rules that will hopefully make a complete firewall
    stack."""
    
    all_chains = dict({})
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        """Create default empty tables and chains."""
        
        self.all_chains = dict({})
        for tb in ['nat','filter']:
            self.all_chains[tb] = dict()
        
        # Initialize default chains
        self.new_chain('PREROUTING', 'nat',      'ACCEPT')
        self.new_chain('POSTROUTING','nat',      'ACCEPT')
        self.new_chain('OUTPUT',     'nat',      'ACCEPT')
        self.new_chain('INPUT',      'filter',   'DROP')
        self.new_chain('FORWARD',    'filter',   'DROP')
        self.new_chain('OUTPUT',     'filter',   'DROP')
    
    def new_chain(self,chain,table='filter',policy='DROP'):
        """Add a new chain.
        
        Add a new chain {chain} to {table} with default policy {policy}."""
        
        if not table in self.all_chains:
            raise Exception("Invalid table {0}. Keys: {1}".format(table,all_chains.keys()))
        if not chain in self.all_chains[table]:
            self.all_chains[table][chain] = dict({
                'policy': policy,
                'rules': []
            })
        else:
            raise Exception("Chain {0} in table {1} already exists.")
    
    def append_chain( self, chain, rule, table='filter', comments=False ):
        """Append a rule to a chain.
        
        Append {rule} to {chain} in {table}."""
        
        if not chain in self.all_chains[table]:
            raise Exception("Chain '{0}' does not yet exist. Try creating it explicitly.")
        
        self.all_chains[table][chain]['rules'].append(rule)
        
        
        
    
    @staticmethod
    def IP_addresses_from_files( filenames ):
        """Return all valid IPv4 addresses from every file in {filenames}"""
        
        locations = ['/etc/vuurmuur/','/etc/firewall.d/config/','']
        files = sum([[L+F for F in filenames] for L in locations],[])
        f = subprocess.Popen(
                ['cat'] + files,
                stdout = subprocess.PIPE, stderr = open('/dev/null','w')
        )
        gr = subprocess.Popen(
                ['sh','-c','grep -oP "([0-9]{1,3}\.){3}[0-9]{1,3}" | sort | uniq'],
                stdin = f.stdout, stdout = subprocess.PIPE
        )
        f.stdout.close()
        s = gr.stdout.read()
        gr.stdout.close()
        return s.split()
    
    def create_filter( self, name, files, table='nat', action='-g to_gateway' ):
        """Create an outbound filter.
        
        Create a separate filter chain called {name}. As soon as a tcp packet is
        detected to an IP address in any one of the files in {files}, the {action}
        is performed."""
        
        addresses = Ruleset.IP_addresses_from_files( files )
        self.new_chain( name, table=table, policy='RETURN' )
        
        for IP in addresses:
            self.append_chain(
                name,
                '-d {0}/32 -p tcp {1}'.format(IP,action),
                table=table
            )
    
    
    
    
    
    
    def output_chains(self, filename):
        """Export all chains in iptables-restore format to {filename}."""
        
        counters = dict({
            'filter': ['INPUT','FORWARD','OUTPUT'],
            'nat': ['PREROUTING','POSTROUTING','OUTPUT']
        })
        
        f = open(filename,'w')
        
        for tb in ['nat','filter']:
            table = self.all_chains[tb]
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
    
    
