# Swarm Sandbox - by Ben Reynhart
# Retrieves list of current neighboring bluetooth phones in swarm
# Performs custom actions depending on Swarm activity
# ---------------------------------------------------
# Copyright (c) 2009 Ben Reynhart
# http://swarmsandbox.reynhart.com/

# installed Python for S60 1.4.5
# installed PythonScriptShell_1_4_4_3rdEd_e71signed.SIS
# installed misty193_e71signed.SIS
# installed pyaosocket-2.02-s60_30_e71signed.sis

import appuifw
import e32
import select
import sys
import os
from key_codes import *
from pyaosocket import AoResolver

# Import appropriate version of socket depening on python
from e32 import pys60_version
if ((pys60_version.split())[0] >= '1.9.1'):
    import btsocket as socket
else:
    import socket

# Eventually move this somewhere suitable
# Try and import misty for vibration
VIBRATION_ENABLED = False
try:
    import misty
    VIBRATION_ENABLED = True
    print u"Imported misty"
except:
    print u"Failed to import misty"

# Not a timer, but close (Active Object) relative
app_lock = e32.Ao_lock()

# You can use just one timer for whole program
# Just ALWAYS remember to cancel it before use
my_timer = e32.Ao_timer()

SWARM_DICT = {"Benjee E71": "00:25:48:96:a5:03",
                    "Benje N95": "00:1E:3A:22:7E:D7",
                    "Andypandy": "00:1e:3a:23:53:0d"}

port = 5

# This class manages initializing / reading / writing the Pulse Rules to a file
class ManageRulesClass(object):
    def __init__(self):
        # Import active local rules
        self.PULSE_VIBRATE = False
        self.PULSE_FLASH = False
        self.PULSE_SNAP = False
        self.PULSE_TONE = False

        self.newline = "\n"
        self.RULES_DIR = "E:\\Python\SwarmFiles"
        self.THE_RULES_FILE = 'E:\\Python\SwarmFiles\pulserules.txt'
        
    # Prints out the current rule status -------
    def print_rules_status(self):
        if (self.PULSE_VIBRATE == True):
           print "Vibrate Rule: ON"
        else:
           print "Vibrate Rule: OFF"
           
        if (self.PULSE_FLASH == True):
           print "Flash Rule: ON"
        else:
           print "Flash Rule: OFF"
           
        if (self.PULSE_SNAP == True):
           print "Snap Rule: ON"
        else:
           print "Snap Rule: OFF"
           
        if (self.PULSE_TONE == True):
           print "Tone Rule: ON"
        else:
           print "Tone Rule: OFF"

     # Initialize the new pulse rules ----------
    def init_rules_file(self):
        # If file directory doesnt exist then create it & file
        if not os.path.isdir(self.RULES_DIR):
            os.makedirs(self.RULES_DIR)
            RULES_FILE = os.path.join(self.RULES_DIR,"pulserules.txt")
            print u"Created rules file in %s" % (self.RULES_DIR)

        # Ok now set the rules variables to be stored in file
        value1 = True
        value2 = False
        config = {}
        config['PULSE_VIBRATE']= value1
        config['PULSE_FLASH']= value2
        config['PULSE_SNAP']= value2
        config['PULSE_TONE']= value2
        f = open(RULES_FILE,'wt')
        f.write(repr(config))
        print u"Written to rules file"
        f.close()

        # Set active local rules
        self.PULSE_VIBRATE = value1
        self.PULSE_FLASH = value2
        self.PULSE_SNAP = value2
        self.PULSE_TONE = value2
        
        # Print out the rules
        self.print_rules_status()

    # Retrieve the settings from dictionary stored on file
    def read_rules_file(self):
        try:
            f = open(self.THE_RULES_FILE,'rt')
            try:
                content = f.read()
                config = eval(content)
                f.close()
                setting1 = config.get('PULSE_VIBRATE','')
                setting2 = config.get('PULSE_FLASH','')
                setting3 = config.get('PULSE_SNAP','')
                setting4 = config.get('PULSE_TONE','')

                # Set active local rules from file
                self.PULSE_VIBRATE = setting1
                self.PULSE_FLASH = setting2
                self.PULSE_SNAP = setting3
                self.PULSE_TONE = setting4

                # Print out the rules
                self.print_rules_status()
            except:
                print 'Cannot read file'
        except:
            print 'Cannot open file'

    # Modify Pulse Rulset opens checkbox list -> updates local rules & pulserules.txt file
    def modify_pulse_ruleset(self):

        # Function that writes values to pulserules.txt
        def write_settings_to_file():

            # Check rules file exists, proceed if it does, else run init
            if not os.path.exists(self.THE_RULES_FILE):
                print u"No rules file exists, running init"
                self.init_rules_file()
            else:
                # Try and open file
                try:
                    f = open(self.THE_RULES_FILE,'wt')
                    try:
                        # Re-build the config dictionary and write it to file
                        config={}
                        config['PULSE_VIBRATE']= self.PULSE_VIBRATE
                        config['PULSE_FLASH']= self.PULSE_FLASH
                        config['PULSE_SNAP']= self.PULSE_SNAP
                        config['PULSE_TONE']= self.PULSE_TONE
                        f.write(repr(config))
                        f.close()
                    except:
                        print u"Cannot write to file"
                except:
                    print u"Cannot open file"

        # Present selection list to user
        VIBRATE_CHOSEN, FLASH_CHOSEN, SNAP_CHOSEN, TONE_CHOSEN = 0, 1, 2, 3
        L = [u"Vibrate", u"Flash", u"Snap", u"Tone"]
        aRulesTuple = appuifw.multi_selection_list(L, style='checkbox', search_field=0)
        aRulesList = list(aRulesTuple)

        # Filter out selected list items & set the active rules
        if( VIBRATE_CHOSEN in aRulesList ):
            self.PULSE_VIBRATE = True
        else:
            self.PULSE_VIBRATE = False

        if( FLASH_CHOSEN in aRulesList ):
            self.PULSE_FLASH = True
        else:
            self.PULSE_FLASH = False

        if( SNAP_CHOSEN in aRulesList ):
            self.PULSE_SNAP = True
        else:
            self.PULSE_SNAP = False

        if( TONE_CHOSEN in aRulesList ):
            self.PULSE_TONE = True
        else:
            self.PULSE_TONE = False

        # Ok now run the write settings function
        write_settings_to_file()
        
        # Print out the rules
        self.print_rules_status()

    # Import rules if file exists, else run init_pulse_rules()
    def init_rules_file_check(self):
        if os.path.exists(self.THE_RULES_FILE):
            print u"Rules file exists, reading"
            self.read_rules_file()
        else:
            print u"No Rules file found, creating one"
            self.init_rules_file()

# Listener server - awaits connections from clients - Triggers pulse actions
class BTServerClass(object):
    print u"New Server Class started"
    # Setup server socket
    serverSocket = socket.socket(socket.AF_BT, socket.SOCK_STREAM)

    # Accept instance of RuleManagerClass
    def __init__(self, theRuleManager):
        # Import active local rules from theRuleManager
        self.ruleMan = theRuleManager
        self.VIBRATE_ON_PULSE = self.ruleMan.PULSE_VIBRATE
        self.FLASH_ON_PULSE = self.ruleMan.PULSE_FLASH
        self.SNAP_ON_PULSE = self.ruleMan.PULSE_SNAP
        self.TONE_ON_PULSE = self.ruleMan.PULSE_TONE

        self.LOCALBTNAME = misty.local_bt_name()
        print "Local address: %s" % self.LOCALBTNAME
        self.active = True
        self.socketConnected = False
        # New timer for waiting on sending
        self.serverTimer = e32.Ao_timer()
        self.lock = e32.Ao_lock()
        self.serverconn = None
        
    # Getter & setter for self.active
    def getActive(self):
        return self.active

    def setActive(self, status):
        self.active = status

    activeSetting = property(getActive, setActive)

    # Trigger actions when Pulse recieved (follow active pulse rules)
    def triggerPulse(self):
        print u"Pulse triggered"
        print u"Vibrate = %i" % self.VIBRATE_ON_PULSE
        print u"Flash = %i" % self.FLASH_ON_PULSE
        print u"Snap = %i" % self.SNAP_ON_PULSE
        print u"Tone = %i" % self.TONE_ON_PULSE

        if( self.VIBRATE_ON_PULSE == True ):
            print u"I am vibrating"
            try:
                misty.vibrate(500, 100)
                #1miso.vibrate(500, 100)
            except Exception, error:
                print u"Error running vibrate: %s" % str(error)

        if( self.FLASH_ON_PULSE == True ):
            print u"I am flashing"
            appuifw.note(u"FLASH", 'info')

        if( self.SNAP_ON_PULSE == True ):
            print u"I am snapping"
            appuifw.note(u"SNAP", 'info')

        if( self.TONE_ON_PULSE == True ):
            print u"I am making a tone"
            appuifw.note(u"TONE", 'info')

    # Fuction listens for .recv data on the socket
    def timeout_h(self):
            # wait for next client to connect
            self.serverconn, addr = self.serverSocket.accept()
            #1serverconn.setblocking(False)
            print "Connected by", addr

            rxmsg = self.serverconn.recv(1024)
            if rxmsg == None or rxmsg == '':
                print 'no msg'
                #pass
            else:
                #1appuifw.note(unicode(rxmsg), 'info')
                try:
                    self.triggerPulse()
                except:
                    print u"Unable to run triggerPulse"

            self.lock.signal()

    # Runs timeout_h in non-blocking every 0.5 secs
    def run(self):
            while 1:
                self.serverTimer.after(0.5, self.timeout_h)
                self.lock.wait()
                if not self.active: break

    # Start listening - Open listening socket - returns serverconn
    def listenForConnection(self):
        channel = socket.bt_rfcomm_get_available_server_channel(self.serverSocket)
        self.serverSocket.bind(("", channel))
        self.serverSocket.listen(1)
        socket.bt_advertise_service(u"btchat", self.serverSocket, True, socket.RFCOMM)
        print u"Opening listening socket on port: %s" % str(channel)
        socket.set_security(self.serverSocket, socket.AUTH | socket.AUTHOR)
        self.serverSocket.setblocking(False)
        print u"waiting for clients"

        #return serverconn
        self.run()

    # If not listening then close socket
    def disconnect(self):
	self.active = False
        print "Stopped Listener Socket"
        self.serverTimer.cancel()
        self.lock.signal()

# Client class for sending out data
class BTClientClass(object):
    # Class Innit
    def __init__(self):
        print u"Client Class Initialized"
        # New timer for waiting on sending
        self.clientTimer = e32.Ao_timer()
        self.clientLock = e32.Ao_lock()
        self.LOCAL_BT_NAME = misty.local_bt_name()
        self.clientConnected = False
        self.currentlySearching = False
        self.resolver = AoResolver() # Bluetooth Reader
        self.clientSocket = socket.socket(socket.AF_BT, socket.SOCK_STREAM)
        self.count = 0
        self.cont = None
        self.TEMP_DICLIST = {}
        self.SWARM_DICLIST = {}
        self.CONNECTED = False
        
    # Getters & setters
    def getCurrrentSearching(self):
        return self.currentlySearching
        
    currentSearching = property(getCurrrentSearching)
    
    # TODO: Check Bt Address is running Swarm Client ----
    def check_device_services(self):
        # If discovered device run Swarm service add to SWARM Dictionary
        for (k, v) in self.TEMP_DICLIST.iteritems():
            print u"Checking services on %s" %k
            tempAddr, tempServ = socket.bt_discover(v)
            print repr(tempServ)

            # TODO: Check service name agains SwarmService - if running add to dict.
            # Currently forces popup followed by crash
            #1self.SWARM_DICLIST[name] = mac

    # Callback run from Aosocket BT resolver
    def callBack(self, error, mac, name, dummy):
        if error == -25: # KErrEof (no more devices)
            print "no more"
            self.cont = None
        elif error:
            raise
        else:
            self.count += 1

            # Add to temp dictionary (currently main dict.)
            self.SWARM_DICLIST[name] = mac
            print repr([mac, name, self.count])

            self.cont = self.resolver.next
        self.clientLock.signal()

    # Send to Swarm function - Iterates SWARM dictionary sending pulse to all
    def sendToSwarm(self):

        print u"Sending to Swarm List"
        for (k, v) in self.SWARM_DICLIST.iteritems():
            # Check own bt address not in dictionary - delete if is
            """if( k == self.LOCAL_BT_NAME ):
                del self.SWARM_DICLIST[self.LOCAL_BT_NAME]
                print u"Deleted self from SwarmDict

            if( self.CONNECTED == False ):
                print u"Connecting to %s" % (k)
                try:
                    self.clientSocket.connect((v, port))
                    self.CONNECTED = True;
                    print u"Connected"
                except:
                    print u"Failed to connect"

                self.clientSocket.send("hello")
                print u"Sent hello"
                self.clientTimer.after(0.5)

                #1clientSocket.shutdown(2)
                self.clientSocket.close()
                self.clientSocket = None
                self.CONNECTED = False
                print u"Socket Closed"
                self.clientTimer.after(0.5)
            else:
		print u"Already connected to server";"""

    # Search local bluetooth devices using AoResolver
    def btSearch(self):
        try:
            self.resolver.open()
            print u"Bluetooth Search Start"
            self.currentlySearching = True
            self.cont = lambda: self.resolver.discover(self.callBack, None)
            while self.cont:
                self.cont()
                self.clientLock.wait()
        finally:
            self.resolver.close()
            self.currentlySearching = False

        print u"Search done"

        self.clientTimer.cancel()
        self.clientTimer.after(0.5)
        
        
        try:
            self.sendToSwarm()
            #1print repr(self.SWARM_DICLIST)
        except Exception, e:
            print u"Could not exec sendToSwarm: %s" %s

        # Check running swarm sandbox service on discovered devices
        #self.check_device_services()

    def popAction(self):
        userAction1 = appuifw.popup_menu([u"Send Pulse"])
        if userAction1 == 0:
             self.sendToSwarm()
             self.clientTimer.after(1)
             self.popAction()
        #1elif userAction1 == 1:
             #1mySocket.close()
    #popAction()


# MAIN CLASS - BASIC APP FUNCTIONS HERE --------------
class Main(object):

    def __init__(self):
        global app_lock
        appuifw.app.exit_key_handler = self.set_exit
        appuifw.app.title = u"Swarm Sandbox v0.1"
        self.btServer = None
        self.btClient = None

        # Create instance of the Pulse Rules Manager & run init check
        rulesManager = ManageRulesClass()
        rulesManager.init_rules_file_check()
        
        # Start Server class and start listening
        # Parsing instance of rulesManager so Server can access Local active rules
        def initServer():
            readyToStartServer = True

            # Ensure client class is not running ----
            try:
                # If btClient exists
                if self.btClient is not None:
                   # If currentlySearching true then prevent more actions
                   if( self.btClient.currentSearching == True ):
                       appuifw.note(u"Searching for devices, please wait..", 'info')

                       readyToStartServer = False
                   else:
                       self.btClient = None

                # If not do nothing
                readyToStartServer = True
            except:
                print u"Error disabling client"

            # Check server not already running or active - else enable active
            if( readyToStartServer == True ):
                if self.btServer is None:
                    self.btServer = BTServerClass(rulesManager)
                    self.btServer.listenForConnection()
                elif (self.btServer.activeSetting == False):
                    self.btServer.activeSetting = True
                    print u"Listening server resumed"
                else:
                    print u"Server already listening"
            else:
                print u"Server not ready to start"

        # Start Client class and run btSearch
        def initClient():

            # If btServer is actively listening then stop it
            try:
                # If btServer exists
                if self.btServer is not None:
                    # If its set to actively listen
                    if( self.btServer.activeSetting == True ):
                        self.btServer.activeSetting = False
                        print u"listening server paused"
                        print u"waiting for clients"

            except:
                print u"Error disabling listening socket"

            # Start new instance of BTClientClass if doesnt exist
            if self.btClient is None:
                self.btClient = BTClientClass()
                self.btClient.btSearch()
            else:
                print u"Client Class already running"

        # Provide App Menu
        appuifw.app.menu = [(u"Send Pulse", initClient),
                            (u"Listen Mode", initServer),
                            (u"Pulse Rules", ((u"Modify Rules", rulesManager.modify_pulse_ruleset),
                                              (u"Send Rules", rulesManager.modify_pulse_ruleset)))]

        self.menuMain = appuifw.app.menu
        app_lock.wait()

    # Exit function -----------------
    def set_exit(self):
        global running
        running = 0

        # If Server class running, run disconnect func
        try:
            if self.btServer is None:
                #1print u"Server not listening"
                pass
            else:
                self.btServer.disconnect()
        except:
            print u"Error disconnectig server"
    
        app_lock.signal()
        appuifw.app.set_exit()


# START MAIN CLASS ----------------------------------
if __name__ == '__main__':

    Main()