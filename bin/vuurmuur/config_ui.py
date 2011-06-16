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

import os, sys, termios

class ConfigUI:
    """A simple text-based UI for the Config class"""
    
    C = None
    tion = ( None, None, None )
    
    def __init__(self,config ):
        self.C = config
        if len(config.Interfaces) > 0:
            self.tion = ( config.Interfaces[0], None, None )
    
    @staticmethod
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
    
    def arrow_key( self, hm ):
        """Handle the arrow key pess events.
        
        Example:
        
        >>> from network_config import Config,Iface
        >>> C = Config()
        >>> C.Interfaces = [Iface(),Iface()]
        >>> C.local_services = [1,2,3]
        >>> UI = ConfigUI(C)
        >>> print '.', UI.Display()
        .    \                                                                       
        ...
        I  /  --    ##    --   ()                                                 <
        N  \                                                                       
        T  /  --    ##    --   ()                                                  
        ...
        None
        >>> UI.arrow_key( 1 )
        >>> print '.', UI.Display()
        .    \                                                                       
        ...
        I  /  --    ##    --   ()                                                  
        N  \                                                                       
        T  /  --    ##    --   ()                                                 <
        ...
        None
        >>> UI.arrow_key( 1 )
        >>> print '.', UI.Display()
        .    \                                                                       
        ...
        I  /  --    ##    --   ()                                                  
        N  \                                                                       
        T  /  --    ##    --   ()                                                 <
        ...
        None
        """
        
        if self.tion[1] == None:
            i = self.C.Interfaces.index( self.tion[0] ) + hm
            i = i if i >= 0 else 0
            i = i if i < len(self.C.Interfaces) else len(self.C.Interfaces) - 1
            self.tion = ( self.C.Interfaces[i], None, None )
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
    
    def loop( self ):
        """Run the UI.
        
        Display a simple text-based UI, and perform actions according to user
        interaction."""
        
        self.Display()
        while True:
            c = ConfigUI.getkey()
            
            if c[1] == (27,91,65,0): # Up arrow
                self.arrow_key( -1 )
            elif c[1] == (27,91,66,0): # Down arrow
                self.arrow_key( 1 )
            
            elif self.tion[1] == None:
                
                # A network interface is selected, but nothing else.
                
                if c[1] == (27,0,0,0): # Escape
                    break
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
                    sn = self.tion[0].new_subnet(sys.stdin.readline().strip())
                    self.tion = ( self.tion[0], sn, None )
                elif c[0] == 'r':
                    print "Enter WAN address: ",
                    self.tion[0].wan_address = sys.stdin.readline().strip()
                elif c[0] == 's':
                    print "Enter port number: ",
                    port = int(sys.stdin.readline().strip())
                    if port in self.C.local_services:
                        self.C.local_services.remove(port)
                    else:
                        self.C.local_services.append(port)
                elif c[1] == (27, 91, 50, 52): # F12
                    self.C.Export()
                    print "Export complete."
                    print "If you blindly trust this script, run the following commands:"
                    print ""
                    print "sudo mv /tmp/firewall/dhcpd.conf /etc/dhcp3/dhcpd.conf"
                    print "sudo mv /tmp/firewall/interfaces /etc/network/interfaces"
                    print "sudo mv /tmp/firewall/if-config /etc/vuurmuur/if-config"
                    print "sudo rm -rf /etc/firewall.d/config/networks /etc/vuurmuur/networks"
                    print "sudo mv /tmp/firewall/{networks,ports} /etc/vuurmuur/"
                    print "rmdir /tmp/firewall"
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
                    try:
                        self.tion[1].address = str(int(
                                sys.stdin.readline().strip() ))
                    except ValueError:
                        print "Error: Network prefix must be an integer between 1 and 255."
                elif c[0] == '+':
                    print " Enter hostname: ",
                    hn = sys.stdin.readline().strip()
                    print "Enter MAC address: ",
                    mac = sys.stdin.readline().strip()
                    print "Enter IP extension: ",
                    ip = sys.stdin.readline().strip()
                    
                    host = self.tion[1].new_host( hn, mac, ip )
                    self.tion = ( self.tion[0], self.tion[1], host )
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
                
                # TODO: Implement the rest of the options
                
                if c[1] == (27,0,0,0): # Escape
                    self.tion[1].showhosts = False
                    self.tion = ( self.tion[0], self.tion[1], None )
                else:
                    continue
            self.Display( UI_options=True )
    
    def Display( self, UI_options = True ):
        """Display the UI.
        
        Example:
        
        >>> from network_config import Config,Iface
        >>> C = Config()
        >>> C.Interfaces = [Iface()]
        >>> C.local_services = [1,2,3]
        >>> UI = ConfigUI(C)
        >>> print '.', UI.Display()
        .    \                                                                       
           /   Open ports: [1, 2, 3]                                               
           \                                                                       
        I  /  --    ##    --   ()                                                 <
        N  \                                                                       
        ...
         [F12] Write config                                  [Esc] Exit
        None
        
        """
        
        cnt = [-1,0]
        def cb(s,o):
            curs = -1
            if o == self.tion[0] and o != None and cnt[0] < 0:
                curs = cnt[0] = 0
            elif o == self.tion[1] and o != None and cnt[0] < 1:
                curs = cnt[0] = 1
            elif o == self.tion[2] and o != None and cnt[0] < 2:
                curs = cnt[0] = 2
            
            print '{string:<71s} {cursor:>3s}'.format(
                    string = s[2:],
                    cursor = ('<','<<','<<<')[curs] if curs >= 0 else ''
            )
            cnt[1] += 1
        
        self.C.Display(cb)
        if UI_options:
            self.UI_optns( cnt[1] )
        
    def UI_optns( self, ct ):
        """Show the keyboard shortcuts
        
        Show the keyboard shortcuts relevant to the current selection."""
        
        print "\n"*( 30 - ct if ct < 30 else 1 )
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
    


if __name__ == '__main__':
    
    import doctest
    doctest.testmod( optionflags = doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE )
