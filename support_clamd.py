#!/usr/bin/python
import time, sys, os, platform, logging, support
import ctypes, math, sqlite3, clamd 

log = logging.getLogger(__name__)

def openClam(path="/var/run/clamav/clamd.ctl"):  # Need to update this file path for clam daemon
   try:
      cd = clamd.ClamdUnixSocket(path) # create clam daemon object
      check = cd.ping() 
      if check == 'PONG': # Checks if daemon is running
         ver = cd.version() # gets clam version number
         support.msg("Clam Connection %s acquired" % ver) 
      else:
         cd = None # If daemon is not running
   except:
      cd = None # If there is not any clam connection available 
   return cd

def scanfile(infile, cd):
   if cd:
      scanfile = os.path.realpath(infile) # gets full path of file
      result = cd.scan(scanfile) # Scans file and stores into result
      return result[scanfile]

if __name__ == "__main__":
   cd = openClam()
   if cd:
      support.msg("Clam daemon - green")
      for infile in sys.argv[1:]:
         result = scanfile(infile,cd)
         support.msg(result)