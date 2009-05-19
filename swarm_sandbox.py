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
import random
from key_codes import *
from pyaosocket import AoResolver
import camera
from time import localtime

# Import audio - for text to speech
SPEECH_ENABLED = False
try:
    import audio
    SPEECH_ENABLED = True
except:
    print u"Failed to import audio"

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

# Set Globals for Maintaining SWARM device list
SCAN_INTERVAL = 120
START_SCAN_DELAY = random.randrange(10, 120)
FIRST_DEVICE_SCAN_DONE = False
THE_SWARM_DICT = {}

# This class manages the GUI of the app
class myGUI(object):
    def __init__(self):
        appuifw.app.title = u"Swarm Sandbox v0.1"
        appuifw.app.screen = "normal"

        # Create MAIN UI Text -------------
        #Create an instance of Text and set it as the application's body
        self.mainText = appuifw.Text()

        #Set the font by name, size and flags
        self.mainText.font = (u"Nokia Hindi S60", 25, None)

        #Write text to see the effect
        self.mainText.style = appuifw.STYLE_BOLD
        self.mainText.add(u"Swarm Sandbox v0.2\n")
        self.mainText.font = (u"Nokia Hindi S60", 16, None)
        self.mainText.style = 0

        # Show to user
        appuifw.app.body = self.mainText
        
    def drawText(self, string):
        self.mainText.add( unicode(string) )
        #1return self.mainText
        
    def reDrawGUI(self):
        # Show to user
        appuifw.app.body = self.mainText

# This class manages initializing / reading / writing the Pulse Rules to a file
class ManageRulesClass(object):
    def __init__(self, theGUI):
        # Import active local rules
        self.PULSE_VIBRATE = False
        self.PULSE_FLASH = False
        self.PULSE_SNAP = False
        self.PULSE_TONE = False

        self.textGUI = theGUI
        self.newline = "\n"
        self.RULES_DIR = "E:\\Python\SwarmFiles"
        self.THE_RULES_FILE = 'E:\\Python\SwarmFiles\pulserules.txt'
        
    # Prints out the current rule status -------
    def print_rules_status(self):
        #1print u"--------------"
        self.textGUI.drawText("---------\n")
        

        if (self.PULSE_VIBRATE == True):
           #1print "Vibrate Rule: ON"
           self.textGUI.drawText("Vibrate Rule: ON\n")
        else:
           #1print "Vibrate Rule: OFF"
           self.textGUI.drawText("Vibrate Rule: OFF\n")

        if (self.PULSE_FLASH == True):
           #1print "Flash Rule: ON"
           self.textGUI.drawText("Flash Rule: ON\n")
        else:
           #1print "Flash Rule: OFF"
           self.textGUI.drawText("Flash Rule: OFF\n")

        if (self.PULSE_SNAP == True):
           #1print "Snap Rule: ON"
           self.textGUI.drawText("Snap Rule: ON\n")
        else:
           #1print "Snap Rule: OFF"
           self.textGUI.drawText("Snap Rule: OFF\n")
           
        if (self.PULSE_TONE == True):
           #1print "Tone Rule: ON"
           self.textGUI.drawText("Speech Rule: ON\n")
        else:
           #1print "Tone Rule: OFF"
           self.textGUI.drawText("Speech Rule: OFF\n")
           
        #1print u"--------------"
        self.textGUI.drawText("---------\n")

        # Redraw GUI
        self.textGUI.reDrawGUI()

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
        L = [u"Vibrate Rule", u"Flash Rule", u"Snap Rule", u"Speech Rule"]
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
    # Setup server socket
    serverSocket = socket.socket(socket.AF_BT, socket.SOCK_STREAM)

    # Accept instance of RuleManagerClass and myGUI class
    def __init__(self, theRuleManager, theGUI):
        # print u"Server class initiated"
        # Import active local rules from theRuleManager
        self.ruleMan = theRuleManager
        self.VIBRATE_ON_PULSE = self.ruleMan.PULSE_VIBRATE
        self.FLASH_ON_PULSE = self.ruleMan.PULSE_FLASH
        self.SNAP_ON_PULSE = self.ruleMan.PULSE_SNAP
        self.TONE_ON_PULSE = self.ruleMan.PULSE_TONE

        self.LOCALBTNAME = misty.local_bt_name()
       
        self.active = True
        self.socketConnected = False
        # New timer for waiting on sending
        self.serverTimer = e32.Ao_timer()
        self.lock = e32.Ao_lock()
        self.serverconn = None
        self.mainTextGUI = theGUI

    # Getter & setter for self.active
    def getActive(self):
        return self.active

    def setActive(self, status):
        self.active = status

    activeSetting = property(getActive, setActive)
    
    # PHONE BASED ACTIONS -----------
    def vibrateMe(self):
        try:
            misty.vibrate(500, 100)
        except Exception, error:
            self.mainTextGUI.drawText("Error running vibrate: %s\n" % str(error))
            self.mainTextGUI.reDrawGUI()

    def flashMe(self):
        try:
            image = camera.take_photo(exposure='night', flash='forced', size=(640, 480))
            tm = localtime()
            fn='E:\\PYTHON\\SwarmFiles\\img%02d%02d%02d%02d.jpg' % (tm.tm_mday, tm.tm_hour, tm.tm_min, tm.tm_sec)
            image.save(filename=fn)
        except:
            self.mainTextGUI.drawText("Error triggering flash\n")
            self.mainTextGUI.reDrawGUI()
            
    def speechMe(self, toBeSaid):
        # If phone capable of speech then say message
        if(SPEECH_ENABLED == True):
            audio.say(toBeSaid)
        else:
            self.mainTextGUI.drawText("Speech disabled\n")
            self.mainTextGUI.reDrawGUI()

    # Trigger actions when Pulse recieved (follow active pulse rules)
    # If recievedMessage is "Pulse", run local actions
    # If recievedMessage starts with "M" then speak message
    # If recievedMessage begins with "R" then trigger recieved rules
    def triggerPulse(self, recievedMessage):
        global SPEECH_ENABLED
        # DEBUG ONLY
        self.mainTextGUI.drawText("Recieved: %s\n" %recievedMessage)
        self.mainTextGUI.reDrawGUI()

        # If recieve PULSE then..
        if(recievedMessage == "Pulse"):
            self.mainTextGUI.drawText("Receieved a PULSE\n")
            self.mainTextGUI.reDrawGUI()

            # If VIBRATE is active then..
            if( self.ruleMan.PULSE_VIBRATE == True ):
                self.vibrateMe()

            # If FLASH is active then...
            if( self.ruleMan.PULSE_FLASH == True ):
                self.flashMe()

            # If SNAP is active then..
            if( self.ruleMan.PULSE_SNAP == True ):
                #1print u"I am snapping"
                #1appuifw.note(u"SNAP", 'info')
                self.mainTextGUI.drawText("I am snapping\n")
                self.mainTextGUI.reDrawGUI()

            # If TONE is active then..
            if( self.ruleMan.PULSE_TONE == True ):
                self.speechMe(recievedMessage)

        elif(recievedMessage[0] == "M"):
            self.mainTextGUI.drawText("Receieved a MESSAGE\n")
            self.mainTextGUI.reDrawGUI()
            endStr = len(recievedMessage)
            stringForSaying = str(recievedMessage[1:endStr])
            self.speechMe(stringForSaying)
            self.mainTextGUI.drawText("Saying %s\n" % recievedMessage[1:endStr])
            self.mainTextGUI.reDrawGUI()

        # Try and take a photo of the user with front cam
        """try:
            sneakImage = camera.take_photo(mode = "RGB", size = (176, 144), exposure = "auto", position = 1)
            tm = localtime()
            fn='E:\\PYTHON\\SwarmFiles\\img%02d%02d%02d%02d.jpg' % (tm.tm_mday, tm.tm_hour, tm.tm_min, tm.tm_sec)
            sneakImage.save(filename=fn)
        except Exception, e:
            self.mainTextGUI.drawText("Could not snap user\n")
            self.mainTextGUI.reDrawGUI()"""

    # Fuction listens for .recv data on the socket
    def timeout_h(self):
        # wait for next client to connect
        self.serverconn, addr = self.serverSocket.accept()
        #1serverconn.setblocking(False)
        #1print "Connected by", addr
        self.mainTextGUI.drawText(u"Connected by %s \n" % addr)
        self.mainTextGUI.reDrawGUI()

        rxmsg = self.serverconn.recv(1024)
        if rxmsg == None or rxmsg == '':
            print 'no msg'
            #pass
        else:
            try:
                self.triggerPulse(rxmsg)
            except:
                self.mainTextGUI.drawText("Unable to run triggerPulse\n")
                self.mainTextGUI.reDrawGUI()

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
        #1channel = 8
        self.serverSocket.bind(("", channel))
        self.serverSocket.listen(1)
        socket.bt_advertise_service(u"btchat", self.serverSocket, True, socket.RFCOMM)
        socket.set_security(self.serverSocket, socket.AUTH | socket.AUTHOR)
        self.serverSocket.setblocking(False)

        #1print u"Opening listening socket on port: %s" % str(channel)
        #1print "Local address: %s" % self.LOCALBTNAME
        #1print u"waiting for clients"
        self.mainTextGUI.drawText(u"%s listening on port: %d \n" % (self.LOCALBTNAME, channel))
        self.mainTextGUI.drawText(u"waiting for clients \n")
        self.mainTextGUI.reDrawGUI()

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
    
    # Accept instance of myGUI
    def __init__(self, theGUI):
        #1print u"Client Class Initialized"
        # New timer for waiting on sending
        self.clientTimer = e32.Ao_timer()
        self.clientLock = e32.Ao_lock()
        self.LOCAL_BT_NAME = misty.local_bt_name()
        self.clientConnected = False
        self.currentlySearching = False
        self.resolver = AoResolver() # Bluetooth Reader
        self.count = 0
        self.cont = None
        self.TEMP_DICLIST = {}
        self.CONNECTED = False
        
        self.myMainTextGUI = theGUI

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
    
    # Format mac address with proper colons
    def format_macaddress(self, addr):
        n =  "%s:%s:%s:%s:%s:%s" % (addr[0:2], addr[2:4], addr[4:6], addr[6:8], addr[8:10], addr[10:])
        return n

    # Setup timeout connection function
    def timeout_connect_send(self, sock, hostAddr, hostName,  porty, timeout, sendMessage):
        closeit = lambda : sock.close()
        w = e32.Ao_timer()
        w.after(timeout, closeit)

        # If cannot connect to host, return False to skip
        try:
            sock.connect((hostAddr, porty))
            self.CONNECTED = True;
            #1print u"Connected to %s" %hostName
            self.myMainTextGUI.drawText("Connected to %s\n" %hostName)
            self.myMainTextGUI.reDrawGUI()
        except Exception, error:
            #1print u"Could not connect to %s, skipping" %hostName
            self.myMainTextGUI.drawText("Could not connect to %s, skipping\n" %hostName)
            self.myMainTextGUI.reDrawGUI()
            self.CONNECTED = False;
            return False
        
        #1sock.send("HELP ME")
        sock.send(sendMessage)
        #1print u"Sent Pulse"
        self.clientTimer.cancel()
        self.clientTimer.after(0.3)

        sock.close()
        self.CONNECTED = False
        #1print u"Socket Closed"

        w.cancel()

    # Send to Swarm function - Iterates SWARM dictionary sending pulse to all
    def sendToSwarm(self, theMessage):
        global THE_SWARM_DICT

        #1print u"Sending to Swarm List"
        self.myMainTextGUI.drawText("Sending to Swarm List\n")
        self.myMainTextGUI.reDrawGUI()
        
        # If THE_SWARM_DICT empty then run BT SEARCH function
        swarm_length = len(THE_SWARM_DICT)
        if (swarm_length == 0):
            self.myMainTextGUI.drawText("Swarm list empty, running discovery.\n")
            self.myMainTextGUI.reDrawGUI()
            self.btSearch()

        else:
            # Iterate through
            for (k, v) in THE_SWARM_DICT.iteritems():
                # Ensure no current connections
                if( self.CONNECTED == False ):
                    clientSocket = socket.socket(socket.AF_BT, socket.SOCK_STREAM)

                    # Run connect & send function - (socket, hostaddr, hostName, port, timeout, message)
                    self.timeout_connect_send(clientSocket, v, k, port, 5, theMessage)

                    self.clientTimer.cancel()
                    self.clientTimer.after(0.5)
                else:
  		    #1print u"Already connected to server";
  		    self.myMainTextGUI.drawText("Already connected to server\n")
                    self.myMainTextGUI.reDrawGUI()

        self.myMainTextGUI.drawText("Finished sending.\n")
        self.myMainTextGUI.drawText("Listening for incoming connections..\n")
        self.myMainTextGUI.reDrawGUI()

    # Callback run from Aosocket BT resolver
    def callBack(self, error, mac, name, dummy):
        if error == -25: # KErrEof (no more devices)
            #1print "no more"
            self.cont = None
        elif error:
            raise
        else:
            self.count += 1

            # Format address and add to temp dictionary
            formattedMac = self.format_macaddress(mac)
            self.TEMP_DICLIST[name] = formattedMac
            #1print u"Found: %s" %name
            self.myMainTextGUI.drawText("Found: %s \n" %name)
            self.myMainTextGUI.reDrawGUI()

            # Display added message if not already in swarm dictionary
            #1if (name, formattedMac) not in THE_SWARM_DICT:
            #1   print u"Added %s to swarm list" %name

            # Add to temp device dictionary
            #1self.SWARM_DICLIST[name] = formattedMac

            self.cont = self.resolver.next
        self.clientLock.signal()

    # Search local bluetooth devices using AoResolver
    def btSearch(self):
        global THE_SWARM_DICT
        global FIRST_DEVICE_SCAN_DONE

        try:
            self.resolver.open()
            #1print u"Searching for devices..."
            self.myMainTextGUI.drawText("Searching for devices...\n")
            self.myMainTextGUI.reDrawGUI()

            self.currentlySearching = True
            self.cont = lambda: self.resolver.discover(self.callBack, None)
            while self.cont:
                self.cont()
                self.clientLock.wait()
        finally:
            self.resolver.close()
            self.currentlySearching = False
            FIRST_DEVICE_SCAN_DONE = True

        # Update global swarm list with temp device list
        THE_SWARM_DICT = self.TEMP_DICLIST
        
        #1print u"Search complete"
        self.myMainTextGUI.drawText("Search complete\n")
        self.myMainTextGUI.reDrawGUI()

        # Check running swarm sandbox service on discovered devices
        #self.check_device_services()

# MAIN CLASS - BASIC APP FUNCTIONS HERE --------------
# -------------------------------------------------- #

class Main(object):

    def __init__(self):
        global app_lock

        appuifw.app.exit_key_handler = self.set_exit
        self.discov_timer = e32.Ao_timer()
        self.btServer = None
        self.btClient = None
        
         # Create instance of myGUI manager
        self.mainGUI = myGUI()

        # Create instance of the Pulse Rules Manager & run init check
        self.rulesManager = ManageRulesClass(self.mainGUI)
        self.rulesManager.init_rules_file_check()

        # Provide App Menu
        appuifw.app.menu = [(u"Send Pulse", self.client_send_swarm),
                            (u"Send Message", self.enter_send_message),
                            (u"Refresh Swarm List", self.discovery_callback),
                            (u"Pulse Rules", ((u"Modify Rules", self.rulesManager.modify_pulse_ruleset),
                                              (u"Send Rules", self.rulesManager.modify_pulse_ruleset)))]

        self.menuMain = appuifw.app.menu

        # Begin Listener server
        self.discov_timer.cancel()
        self.discov_timer.after(0.3)
        self.initServer()

        app_lock.wait()

    # Discovery Timer callback
    def discovery_callback(self):
        global FIRST_DEVICE_SCAN_DONE

        # If currentlySearching skip auto-discovery
        if( self.btClient is not None ):
            if( self.btClient.currentSearching == True ):
                #1print u"Already discovering, skipping"
                self.mainGUI.drawText("Already discovering, skipping\n")
                self.mainGUI.reDrawGUI()

            else:
                #1print u"Running discovery.."
                self.mainGUI.drawText("Running discovery..\n")
                self.mainGUI.reDrawGUI()
                try:
                    self.btClient.btSearch()
                except:
                    #1print u"Could not run discovery."
                    self.mainGUI.drawText("Could not run discovery\n")
                    self.mainGUI.reDrawGUI()
        else:
            #1print u"Running discovery.."
            self.mainGUI.drawText("Starting client & Running discovery..\n")
            self.mainGUI.reDrawGUI()
            try:
                self.initClient()
                self.btClient.btSearch()
            except:
                #1print u"Could not run discovery."
                self.mainGUI.drawText("Could not run discovery\n")
                self.mainGUI.reDrawGUI()

        # Restart timer
        #1self.start_discovery_timer(False)

        #1print u"Listening for incoming..."
        self.mainGUI.drawText("Listening for incoming...\n")
        self.mainGUI.reDrawGUI()

    # Periodically scan for devices and update Swarm List
    def start_discovery_timer(self, first):
        global SCAN_INTERVAL
        global START_SCAN_DELAY

        if( first == True ):
            self.discov_timer.cancel()
            self.discov_timer.after(START_SCAN_DELAY, self.discovery_callback)
            print u"Discovering devices in %s seconds" %START_SCAN_DELAY
        elif( first == False):
            # New timer for waiting on sending
            self.discov_timer.cancel()
            self.discov_timer.after(SCAN_INTERVAL, self.discovery_callback)
            print u"Discovering devices in %s seconds" %SCAN_INTERVAL

    # Start Server class and start listening
    # Parsing instance of rulesManager so Server can access Local active rules
    def initServer(self):
        readyToStartServer = True

        # Check server not already running or active - else enable active
        if( readyToStartServer == True ):
            if self.btServer is None:
                self.btServer = BTServerClass(self.rulesManager, self.mainGUI)

                # AFTER LISTENER STARTED (first time?)- run discovery timer in background
                #1self.start_discovery_timer(True)

                # Setup a incoming connection listener
                self.btServer.listenForConnection()

            elif (self.btServer.activeSetting == False):
                self.btServer.activeSetting = True
                print u"Listening server resumed"
            else:
                print u"Server already listening"
        else:
            print u"Server not ready to start"

    # Start Client class and run btSearch
    def initClient(self):
        global FIRST_DEVICE_SCAN_DONE

        # Start new instance of BTClientClass if doesnt exist
        if self.btClient is None:
            try:
                self.btClient = BTClientClass(self.mainGUI)
            except:
                print u"Could not launch client"

        if( FIRST_DEVICE_SCAN_DONE == False ):
            self.btClient.btSearch()
        else:
            pass

    # Enter send message - prompt for user message to send
    def enter_send_message(self):
        messageData = appuifw.query(u"Type word or message:", "text")
        preparedMessage = u"M" + messageData
        self.client_send_swarm(preparedMessage)
        #1self.mainGUI.drawText("Sent: %s\n" %preparedMessage)
        #1self.mainGUI.reDrawGUI()

    # Send to Swarm function
    def client_send_swarm(self, message = "Pulse"):
        # Check btClient exists (not to overwrite)
        if self.btClient is None:
            self.initClient()
            self.mainGUI.drawText("Initing Client\n")
            self.mainGUI.reDrawGUI()

        if( self.btClient.currentSearching == True ):
            self.mainGUI.drawText("Busy discovering, skipping..\n")
            self.mainGUI.reDrawGUI()
        else:
            try:
                self.btClient.sendToSwarm(message)
            except Exception, e:
                self.mainGUI.drawText("Cannot sendToSwarm (from client_send_swarm): %s\n" %e)
                self.mainGUI.reDrawGUI()

            #1self.btClient.sendToSwarm()

    # FOR MENU USE - INIT CLIENT & SEND SWARM -----------
    """def init_client_and_send(self):
        
        # STOP Discovery timer if running
        self.discov_timer.cancel()

        # Check btClient exists (not to overwrite)
        if self.btClient is None:
            print u"Initing client"
            self.initClient()

        if( self.btClient.currentSearching == True ):
            print u"Busy discovering, skipping.."
        else:
            self.client_send_swarm()
            
        # Start discover timer
        #1self.start_discovery_timer(False)"""

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