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

import os,subprocess
from collections import defaultdict

class Ruleset:
    """A collection of iptables rules.
    
    A collection of iptables rules that will hopefully make a complete firewall
    stack."""
    
    all_chains = dict({})
    table_description = defaultdict(lambda s: \
            'I have no idea what the table `{0}` does.'.format(s))
    
    def __init__(self):
        
        # Initialize descriptions for default tables.
        self.table_description['nat'] = \
                'The nat table is used mainly for Network Address Translation.\n' + \
                'Packets get their IP addresses altered according to these rules.'
        self.table_description['filter'] = \
                'The `filter` table is the main venue for deciding whether or not\n' + \
                'a packet is desired.'
        
        self.reset()
    
    def reset(self):
        """Create empty tables and chains.
        
        Create a set of tables containing the default chains, without any addi-
        tional rules.
        
        Examples:
        
        >>> R = Ruleset()
        >>> R.reset()
        >>> len(R.all_chains.items())
        2
        >>> len(R.all_chains['filter'].items())
        3
        >>> len(R.all_chains['mangle'].items())
        Traceback (most recent call last):
        ...
        KeyError: 'mangle'
        >>> len(R.all_chains['filter']['INPUT']['rules'])
        0
        >>> R.all_chains['filter']['OUTPUT']['policy']
        'DROP'
        
        """
        
        self.all_chains = dict({})
        for tb in ['nat','filter']:
            self.all_chains[tb] = dict()
        
        # Initialize default chains
        self.new_chain('PREROUTING', 'nat',      'ACCEPT',
                'The PREROUTING chain is used to alter packets as soon as\n' + \
                'they get in to the berlin firewall.')
        self.new_chain('OUTPUT',     'nat',      'ACCEPT',
                'The OUTPUT chain is used for altering locally generated\n' + \
                'packets before they get to the routing decision.')
        self.new_chain('POSTROUTING','nat',      'ACCEPT',
                'the POSTROUTING chain is used to alter packets just as\n' + \
                'they are about to leave the berlin firewall.')
        
        self.new_chain('FORWARD',    'filter',   'DROP',
                'The FORWARD chain is used on all non-locally generated\n' + \
                'packets that are not destined for the berlin firewall itself.')
        self.new_chain('INPUT',      'filter',   'DROP',
                'The INPUT chain is used on all packets that are destined\n' + \
                'for the berlin wall, both from the internal network and the\n' + \
                'public internet.')
        self.new_chain('OUTPUT',     'filter',   'DROP',
                'The OUTPUT chain is used for locally generated packets.')
    
    def new_chain(self,chain,table='filter',policy='DROP', description=None):
        """Add a new chain.
        
        Add a new chain {chain} to {table} with default policy {policy}.
        
        Examples:
        
        >>> R = Ruleset()
        >>> R.new_chain('godfather')
        >>> R.new_chain('godfather',table='robert deniro')
        Traceback (most recent call last):
        ...
        Exception: Invalid table robert deniro. Keys: ...
        >>> len(R.all_chains['filter'].items())
        4
        >>> len(R.all_chains['filter']['godfather']['rules'])
        0
        >>> len(R.all_chains['filter']['part II']['rules'])
        Traceback (most recent call last):
        ...
        KeyError: 'part II'
        
        """
        
        if not table in self.all_chains:
            raise Exception( "Invalid table {0}. Keys: {1}".format(
                    table,self.all_chains.keys()) )
        
        if not description:
            # No description given, so set a default one.
            description = ('The function of the chain `{0}` is thought to be\n' + \
                    'self-explanatory.').format(chain)
        
        if not chain in self.all_chains[table]:
            self.all_chains[table][chain] = dict({
                    'policy': policy,
                    'rules': [],
                    'description': description
            })
        else:
            raise Exception("Chain {0} in table {1} already exists.")
    
    def append_chain( self, chain, rule, table='filter', comments=False ):
        """Append a rule to a chain.
        
        Append {rule} to {chain} in {table}.
        
        Examples:
        
        >>> R = Ruleset()
        >>> R.new_chain('godfather')
        >>> len(R.all_chains['filter'].items())
        4
        >>> len(R.all_chains['filter']['godfather']['rules'])
        0
        >>> R.append_chain( 'godfather', 'part II' )
        >>> R.append_chain( 'godfather', 'part III' )
        >>> R.append_chain( 'matrix', 'part II' )
        Traceback (most recent call last):
        ...
        Exception: Chain 'matrix' does not yet exist. ...
        >>> 'part II' in R.all_chains['filter']['godfather']['rules']
        True
        >>> 'part III' in R.all_chains['filter']['godfather']['rules']
        True
        >>> 'part IV' in R.all_chains['filter']['godfather']['rules']
        False
        
        """
        
        if not chain in self.all_chains[table]:
            raise Exception("Chain '{0}' does not yet exist. Try creating it explicitly.".format(chain))
        
        self.all_chains[table][chain]['rules'].append(rule)
        
        
        
    
    @staticmethod
    def IP_addresses_from_files( filenames ):
        """Return all valid IPv4 addresses from every file in {filenames}
        
        Examples:
        
        >>> f = open('/tmp/doctest_IP_addresses_from_files','w')
        >>> f.write('127.0.0.1\\n\\n')
        >>> f.close()
        
        >>> Ruleset.IP_addresses_from_files( [] )
        []
        >>> Ruleset.IP_addresses_from_files( ['/tmp/doctest_IP_addresses_from_files'] )
        ['127.0.0.1']
        
        """
        
        locations = ['/etc/berlin/','/etc/vuurmuur/','/etc/firewall.d/config/','']
        files = sum([[L+F for F in filenames] for L in locations],[])
        f = subprocess.Popen(
                ['cat', '/dev/null'] + files,
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
        is performed.
        
        >>> R = Ruleset()
        
        >>> f = open('/tmp/doctest_create_filter','w')
        >>> f.write('127.0.0.1\\n10.0.0.138\\n')
        >>> f.close()
        
        >>> R.create_filter( 'doctest', ['/tmp/doctest_create_filter'] )
        >>> R.create_filter( 'another_doctest', [], table='filter' )
        
        >>> len(R.all_chains['nat']['doctest']['rules'])
        2
        >>> len(R.all_chains['filter']['another_doctest']['rules'])
        0
        
        """
        
        addresses = Ruleset.IP_addresses_from_files( files )
        self.new_chain( name, table=table, policy='RETURN' )
        
        for IP in addresses:
            self.append_chain(
                name,
                '-d {0}/32 -p tcp {1}'.format(IP,action),
                table=table
            )
    
    
    
    
    
    
    def output_chains(self, filename):
        """Export all chains in iptables-restore format to {filename}.
        
        Examples:
        
        >>> R = Ruleset()
        >>> R.output_chains( '/tmp/doctest_output_chains' )
        
        >>> f = open( '/tmp/doctest_output_chains', 'r' )
        >>> print f.read()
        <BLANKLINE>
        <BLANKLINE>
        <BLANKLINE>
        #  
        ...
        #  
        *nat
        :PREROUTING ACCEPT [0:0]
        :POSTROUTING ACCEPT [0:0]
        :OUTPUT ACCEPT [0:0]
        COMMIT
        <BLANKLINE>
        <BLANKLINE>
        <BLANKLINE>
        #  
        ...
        #  
        *filter
        :INPUT DROP [0:0]
        :FORWARD DROP [0:0]
        :OUTPUT DROP [0:0]
        COMMIT
        <BLANKLINE>
        >>> f.close()
        
        """
        
        counters = dict({
            'filter': ['INPUT','FORWARD','OUTPUT'],
            'nat': ['PREROUTING','POSTROUTING','OUTPUT']
        })
        
        f = open(filename,'w')
        
        for tb in ['nat','filter']:
            table = self.all_chains[tb]
            
            # Write down what the table does
            f.write('\n\n\n\n###     \n###     {0}\n###     \n\n'.format(
                    self.table_description[tb].replace('\n','\n###     ') ))
            
            f.write('*{0}\n'.format(tb))
            
            # Write the chain declarations for all buitin chains
            for ch in counters[tb]:
                f.write(':{0} {1} [0:0]\n'.format(ch,table[ch]['policy']))
            
            # Write the chain declarations for all user-defined chains
            for ch,chain in table.items():
                if ch in counters[tb]: continue
                f.write('-N {0}\n'.format(ch))
                if chain['policy'] not in ['-','RETURN']:
                    f.write('-P {0} {1}\n'.format(ch,chain['policy']))
            
            # Write all the rules for the user-defined chains
            for ch,chain in table.items():
                if len(chain['rules']) > 0:
                    # Write the description first.
                    f.write('\n\n##  {0}\n\n'.format(
                            chain['description'].replace('\n','\n##  ') ))
                
                for r in chain['rules']:
                    if not r:
                        f.write('\n')
                    elif r[0] == '#':
                        f.write( '{0}\n'.format(r) )
                    else:
                        f.write('-A {0} {1}\n'.format(ch,r))
            
            # Commit everything.
            f.write('\n\nCOMMIT\n')
        
        f.close()
    
    


if __name__ == '__main__':
    import os,doctest
    doctest.testmod( optionflags = doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE )
    
    os.unlink('/tmp/doctest_IP_addresses_from_files')
    os.unlink('/tmp/doctest_create_filter')
    os.unlink('/tmp/doctest_output_chains')
