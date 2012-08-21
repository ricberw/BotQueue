#!/usr/bin/env python

# This file is part of the Printrun suite.
# 
# Printrun is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# Printrun is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with Printrun.  If not, see <http://www.gnu.org/licenses/>.

from serial import Serial, SerialException
from threading import Thread
from select import error as SelectError
import time, getopt, sys

class printcore():
    def __init__(self,port=None,baud=None):
        """Initializes a printcore instance. Pass the port and baud rate to connect immediately
        """
        self.baud=None
        self.port=None
        self.printer=None #Serial instance connected to the printer, None when disconnected
        self.clear=0 #clear to send, enabled after responses
        self.online=False #The printer has responded to the initial command and is active
        self.printing=False #is a print currently running, true if printing, false if paused
        self.mainqueue=[] 
        self.jobfile=None
        self.filesize = 0
        self.sentbytes = 0
        self.priqueue=[]
        self.queueindex=0
        self.lineno=0
        self.resendfrom=-1
        self.paused=False
        self.sentlines={}
        self.log=[]
        self.sent=[]
        self.tempcb=None#impl (wholeline)
        self.recvcb=None#impl (wholeline)
        self.sendcb=None#impl (wholeline)
        self.errorcb=None#impl (wholeline)
        self.startcb=None#impl ()
        self.endcb=None#impl ()
        self.onlinecb=None#impl ()
        self.loud=False#emit sent and received lines to terminal
        self.greetings=['start','Grbl ']
        if port is not None and baud is not None:
            #print port, baud
            self.connect(port, baud)
            #print "connected\n"
        
        
    def disconnect(self):
        """Disconnects from printer and pauses the print
        """
        if(self.printer):
            self.printer.close()
        self.printer=None
        self.online=False
        self.printing=False
        
    def connect(self,port=None,baud=None):
        """Set port and baudrate if given, then connect to printer
        """
        if(self.printer):
            self.disconnect()
        if port is not None:
            self.port=port
        if baud is not None:
            self.baud=baud
        if self.port is not None and self.baud is not None:
            self.printer=Serial(self.port,self.baud,timeout=5)
            Thread(target=self._listen).start()
            
    def reset(self):
        """Reset the printer
        """
        if(self.printer):
            self.printer.setDTR(1)
            self.printer.setDTR(0)
            
            
    def _listen(self):
        """This function acts on messages from the firmware
        """
        self.clear=True
        time.sleep(1.0)
        self.send_now("M105")
        while(True):
            if(not self.printer or not self.printer.isOpen):
                break
            try:
                line=self.printer.readline()
            except SelectError, e:
                if 'Bad file descriptor' in e.args[1]:
                    print "Can't read from printer (disconnected?)."
                    print e
                    break
                else:
                    raise
            except SerialException, e:
                print "Can't read from printer (disconnected?)."
                print e
                break
            except OSError, e:
                print "Can't read from printer (disconnected?)."
                print e
                break

            if(len(line)>1):
                self.log+=[line]
                if self.recvcb is not None:
                    try:
                        self.recvcb(line)
                    except:
                        pass
                if self.loud:
                    print "RECV: ",line.rstrip()
            if(line.startswith('DEBUG_')):
                continue
            if(line.startswith(tuple(self.greetings)) or line.startswith('ok')):
                self.clear=True
            if(line.startswith(tuple(self.greetings)) or line.startswith('ok') or "T:" in line):
                if (not self.online or line.startswith(tuple(self.greetings))) and self.onlinecb is not None:
                    try:
                        self.onlinecb()
                    except:
                        pass
                self.online=True
                if(line.startswith('ok')):
                    #self.resendfrom=-1
                    #put temp handling here
                    if "T:" in line and self.tempcb is not None:
                        try:
                            self.tempcb(line)
                        except:
                            pass
                    #callback for temp, status, whatever
            elif(line.startswith('Error')):
                if self.errorcb is not None:
                    try:
                        self.errorcb(line)
                    except:
                        pass
                #callback for errors
                pass
            if line.lower().startswith("resend") or line.startswith("rs"):
                try:
                    toresend=int(line.replace("N:"," ").replace("N"," ").replace(":"," ").split()[-1])
                except:
                    if line.startswith("rs"):
                        toresend=int(line.split()[1])
                self.resendfrom=toresend
                self.clear=True
        self.clear=True
        #callback for disconnect
        
    def _checksum(self,command):
        return reduce(lambda x,y:x^y, map(ord,command))
        
    def startprint(self,jobfile):
        """Start a print, data is an open file object for printing.
        returns True on success, False if already printing.
        The print queue will be replaced with the contents of the data array, the next line will be set to 0 and the firmware notified.
        Printing will then start in a parallel thread.
        """
        if(self.printing or not self.online or not self.printer):
            print "bailing... because of %s %s %s" % (self.printing, self.online, self.printer)
            return False
        self.printing=True
        self.mainqueue=[]
        self.jobfile = jobfile
      
        #get our file size
        self.jobfile.seek(0, 2)
        self.filesize = self.jobfile.tell()
        self.jobfile.seek(0)
        print "file size: %s" % self.filesize

        self.lineno=0
        self.queueindex=0
        self.resendfrom=-1
        self._send("M110",-1, True)
        self.clear=False
        Thread(target=self._print).start()
        return True
        
    def pause(self):
        """Pauses the print, saving the current position.
        """
        self.paused=True
        self.printing=False
        time.sleep(1)
        
    def resume(self):
        """Resumes a paused print.
        """
        self.paused=False
        self.printing=True
        Thread(target=self._print).start()
    
    def send(self,command):
        """Adds a command to the checksummed main command queue if printing, or sends the command immediately if not printing
        """       
        if(self.printing):
            self.mainqueue+=[command]
        else:
            while not self.clear:
                time.sleep(0.001)
            self._send(command,self.lineno,True)
            self.lineno+=1
        
    
    def send_now(self,command):
        """Sends a command to the printer ahead of the command queue, without a checksum
        """
        if(self.printing):
            self.priqueue+=[command]
        else:
            while not self.clear:
                time.sleep(0.001)
            self._send(command)
        #callback for command sent
        
    def _print(self):
        #callback for printing started
        if self.startcb is not None:
            try:
                self.startcb()
            except:
                pass
        while(self.printing and self.printer and self.online):
            #print "in printcore thread"
            #time.sleep(1)
            self._sendnext()
        self.log=[]
        self.sent=[]
        if self.endcb is not None:
            try:
                self.endcb()
            except:
                pass
        #callback for printing done
        
    def _sendnext(self):
        #are we connected?
        if(not self.printer):
            return
        
        #wait until we're ready for data
        while not self.clear:
            time.sleep(0.001)
        self.clear=False
        
        #we have to be online and ready to go.
        if not (self.printing and self.printer and self.online):
            self.clear=True
            return
        
        #handle resending of gcode lines as needed.
        if(self.resendfrom<self.lineno and self.resendfrom>-1):
            self._send(self.sentlines[self.resendfrom],self.resendfrom,False)
            self.resendfrom+=1
            return
        self.sentlines={}
        self.resendfrom=-1

        #any priority lines that need to be sent out immediately?
        for i in self.priqueue[:]:
            self._send(i)
            del(self.priqueue[0])
            return

        #try to keep our queue happy.
        while self.queueindex < (len(self.mainqueue)+50):
            tline = self.jobfile.readline()
            if tline:
                #print "adding line"
                self.mainqueue+=[tline.rstrip()]
            else:
                #print "end of file!"
                break
        
        #okay, pull stuff out of the queue.
        if self.queueindex<len(self.mainqueue):
            tline=self.mainqueue[self.queueindex]
            self.sentbytes = self.sentbytes + len(tline) #keep track of how far we are, in bytes
            tline=tline.split(";")[0]
            if(len(tline)>0):
                self._send(tline,self.lineno,True)
                self.lineno+=1
            else:
                self.clear=True
            self.queueindex+=1
        #okay, we're all out of lines now.
        else:
            print "we're out of lines"
            #okay, we must be done!
            self.printing=False
            self.clear=True
            if(not self.paused):
                self.queueindex=0
                self.lineno=0
                self._send("M110",-1, True)
        
    def get_percentage(self):
      if self.filesize:
        return float(self.sentbytes) / float(self.filesize)*100
      else:
        return 0

    def _send(self, command, lineno=0, calcchecksum=False):
        if(calcchecksum):
            prefix="N"+str(lineno)+" "+command
            command=prefix+"*"+str(self._checksum(prefix))
            if("M110" not in command):
                self.sentlines[lineno]=command
        if(self.printer):
            self.sent+=[command]
            if self.loud:
                print "SENT: ",command
            if self.sendcb is not None:
                try:
                    self.sendcb(command)
                except:
                    pass
            try:
                self.printer.write(str(command+"\n"))
            except SerialException, e:
                print "Can't write to printer (disconnected?)."

if __name__ == '__main__':
    baud = 115200
    loud = False
    statusreport=False
    try:
	opts, args=getopt.getopt(sys.argv[1:], "h,b:,v,s",["help","baud","verbose","statusreport"])
    except getopt.GetoptError,err:
		print str(err)
		print help
		sys.exit(2)
    for o,a in opts:
	if o in ('-h', '--help'):
		# FIXME: Fix help
		print "Opts are: --help , -b --baud = baudrate, -v --verbose, -s --statusreport"
		sys.exit(1)
	if o in ('-b', '--baud'):
		baud = int(a)
	if o in ('-v','--verbose'):
		loud=True
        elif o in ('-s','--statusreport'):
		statusreport=True


    if len(args)>1:
        port=args[-2]
        filename=args[-1]
        print "Printing: "+filename + " on "+port + " with baudrate "+str(baud) 
    else:
        print "Usage: python [-h|-b|-v|-s] printcore.py /dev/tty[USB|ACM]x filename.gcode"
        sys.exit(2)
    p=printcore(port,baud)
    p.loud = loud
    time.sleep(2)
    jobfile = open(filename)
    p.startprint(jobfile)

    try:
        if statusreport:
            p.loud=False
            sys.stdout.write("Progress: 00.0%")
            sys.stdout.flush()
        while(p.printing):
            time.sleep(1)
            if statusreport:
                sys.stdout.write("\b\b\b\b%02.1f%%" % (100*float(p.queueindex)/len(p.mainqueue),) )
                sys.stdout.flush()
        p.disconnect()
        sys.exit(0)
    except:
        p.disconnect()
