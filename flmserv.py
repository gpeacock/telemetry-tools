#!/usr/bin/python
# Telemetry Monitor service 
# Serves multiple flash player telemetry sessions, saves each session
# as a raw telemetry (flm) file for viewing in FlashMonitor or post processing

# Copyright 2013 Adobe Systems Incorporated.
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0.html 

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import threading
import sys,os
import socket
import datetime
#import amf3reader
from optparse import OptionParser
#from pprint import pformat

folder = "flm" # set this to where you want to store your logs
ext = ".flm"    # extension to add to log files
telemetryPort = 7934  # port used by this service
sessionCount = 0;
queueSize = 10
log = []

def timestamp():
    n = datetime.datetime.now()
    return n.strftime("%Y-%m-%d %H:%M")

# Our thread class:
class ClientThread ( threading.Thread ):

   # Override Thread's __init__ method to accept the parameters needed:
    def __init__ ( self, channel, details, sessionId ):
        channel.setblocking(1)
        self.channel = channel
        self.details = details
        self.sessionId = sessionId  #eventually use a unique device ID
        threading.Thread.__init__ ( self )
        self.daemon = True

    def makeFileName(self):
        # files should be stored by client ID when we have one	
        path = folder+"/"  #+str(self.sessionId)+"/"
        if not os.path.exists(path):
            os.makedirs(path)	
        #find the swf name from the content if we have one
        fname = path+"log"
        # generate unique file name		
        i = 0
        while (os.path.isfile(fname+str(i)+ext)):
            i += 1
        return (fname+str(i)+ext)   		
 
    def run ( self ):
        print('Connected:', self.details[0], self.details[1], timestamp())
        connected = True;
        f = None
        try:
        #if True:
            while  connected:
                data = self.channel.recv ( 1024 )
                #print data
                if data:
                    if len(data) > 0:
                        if f==None:
                            fname = self.makeFileName()
                            f = open(fname, 'wb')
                        #print("writing ",len(data))
                        f.write(data)
                else:
                    connected = False
        except:
            print("error on connection");

        if (f):
            f.close()
            print ("Created "+fname)
        self.channel.close()
        print('Closed:', self.details[0], self.details[1], timestamp())



def parseArguments():
    parser = OptionParser()
    #parser.add_option("-f", "--file", dest="filename",
    #    help="write report to FILE", metavar="FILE")
    parser.add_option("-q", "--quiet",
        action="store_false", dest="verbose", default=True,
        help="don't print status messages to stdout")

    (options, args) = parser.parse_args()

parseArguments()

# Set up the server:
try:
    server = socket.socket ( socket.AF_INET, socket.SOCK_STREAM )
    server.bind ( ( '', telemetryPort ) )
    server.listen ( 5 )
    server.settimeout( 2.0 )
except:
    print("unable to initialize server")
    print("Close any other Telemetry services")
    exit(1);

# Have the server serve "forever":
print("Telemetry Monitor Service Running, ^c to quit")
while True:
    try:
        channel, details = server.accept()
    except socket.timeout:
        continue
    except:
        print("Server Session canceled %d sessions" % sessionCount)
        sys.exit(1)
    ClientThread ( channel, details, sessionCount ).start()
    sessionCount += 1
