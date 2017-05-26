#!/usr/bin/python
import argparse, ntplib, time, sys, platform, logging, glob, os, re, support_sql, fattr
from PIL import Image

# Get the logging argument form the main program running to use for storing in msg
log = logging.getLogger(__name__)

# MTP server address usesd to validate clock times
NTP_SERVER='utcnist.colorado.edu' #Colorado

def ParseCmdLine(DESCRIPTION="Missing Name"):
    #This function verifies where the user specifies the path to relatively run the application. 
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    # Because the p flag argument is required our code was unable to run the progress any further
    parser.add_argument('-C','--case',required=True,help='Directory location to store files.') 
    parser.add_argument('-P','--prefix',action='store',help='Log File Prefix.') 
    parser.add_argument('-U','--utc', action='store_true',help='Log with UTC time instead of local time.') 
    parser.add_argument('-S224','--sha224', action='store_true',help='Runs the sha224 algorithm on file(s).') 
    parser.add_argument('-S256','--sha256', action='store_true',help='Runs the sha256 algorithm on file(s).') 
    parser.add_argument('-S384','--sha384', action='store_true',help='Runs the sha384 algorithm on file(s).') 
    parser.add_argument('-S512','--sha512', action='store_true',help='Runs the sha512 algorithm on file(s).') 
    parser.add_argument('-MD5','--md5sum', action='store_true',help='Runs the MD5 algorithm on file(s).') 
    parser.add_argument('-s','--scan',action='store',nargs='+',help='Saves case information into a database.')
    parser.add_argument('-c','--classify', action='store_true',help='Gets the last filestat run data stored in database.') 
    parser.add_argument('-gr','--getRun', action='store_true',help='Gets the last filestat run data stored in database.') 
    parser.add_argument('-v','--verbose', action='store_true',help='Explains what is being done') 
    global gl_args
    gl_args = parser.parse_args()
    return

def ValidateFileRead(theFile):
    # Validate theFile is a valid readable file
    if not os.path.exists(theFile):
        raise argparse.ArgumentTypeError('File does not exist')
    # Validate the path is readable
    if os.access(theFile, os.R_OK):
        return theFile
    else:
        raise argparse.ArgumentTypeError('File is not readable')

def getDate():
    # This function either grabs the gm or utc time depending if the -u or -utc flag was was enabled
    now = time.time()
    return time.strftime("%m-%d-%Y")

def getPrefix():
    # This function returns the log prefix if specified
    if gl_args.prefix is not None:
        prefix=gl_args.prefix+'-'
    else:
        prefix='log-'
    return prefix

def getTime():
    # This function either grabs the gm or utc time depending if the -u or -utc flag was was enabled
    now = time.time()
    try:
        if gl_args.utc:
            return time.strftime("%H.%M.%S%z", time.gmtime(int(now)))
        else:
            return time.strftime("%H.%M.%S%z", time.localtime(int(now)))
    except:
        return time.strftime("%H.%M.%S%z", time.localtime(int(now)))

def checkExternalTime():
    ''' 
    Grabs the time from an NTP server from the address in the global variable using the ntplib. Then it compares the value with the current time by calculating the differnece. While checking it stores logging information using the msg command into the log file created from startLog.
    '''
    ntp = ntplib.NTPClient()
    msg('Time Verification')
    msg('NTP Server: ' + NTP_SERVER)
    # Colorado server is taking to long March remove return later
    try:
        ntpResponse = ntp.request(NTP_SERVER)
        if(ntpResponse):
            now = time.time()
            diff = now - ntpResponse.tx_time
            delay = ntpResponse.delay
            msg('Time difference is secs '+str(diff)+' and Network delay is '+str(delay)+' secs')  
    except:
        msg('Time Verification Failed For '+ NTP_SERVER +'!')

def msg(msg):
    log.info(msg)
    # grabs msg argument and stores it in a log from the main program running
    try:
        if gl_args.verbose:
            print(msg)
    except:
        print(msg)
    return

def startLog(DESCRIPTION="Missing", VERSION="Missing"):
    # Writes out the first messages for the log file to start
    msg('---')
    msg('Starting '+DESCRIPTION+' V'+VERSION)
    msg('')
    log_uname = ' '.join(platform.uname())
    msg('System information: ' + log_uname)
    msg('')
    msg('Program started at: '+getTime())

def additionalLogs():
    # Outputs the arguments when the program was called
    msg('Arguments: '+ ' '.join(sys.argv))
    # Outputs python build information python version numver and date
    msg('Python build running: '+' '.join(platform.python_build())) 

def check_image_with_pil(path): # Uses pil to check if the file is an image
    try:
        Image.open(path)
    except IOError:
        return False
    return True

def mainMod():
    case=gl_args.case
    cursor=support_sql.opendb("JJayCaseDB.db")
    runkey=support_sql.startCase(case,cursor)
    for scanItem in gl_args.scan:
        full_filename=os.path.abspath(scanItem)
        if os.path.isfile(full_filename):            
            filekey=fattr.getFileAttr(case,full_filename,cursor)
            support_sql.scanfile_sql(full_filename, cursor, runkey, filekey)
        if gl_args.classify and check_image_with_pil(full_filename):
            support_sql.tensorfile_sql(cursor, runkey, filekey, full_filename)
    if gl_args.getRun:
        support_sql.getLastRun(cursor)     
    support_sql.closedb()

if __name__ == '__main__':
    ParseCmdLine()
    startLog()
    additionalLogs()
    getTime()
    checkExternalTime()
    msg("Testing Code!!")
    checkExternalTime()
    for infile in sys.argv[1:]:
        full_filename=os.path.abspath(infile)
        if check_image_with_pil(full_filename):
            print("%s: is an image file\n"%(full_filename))
    mainMod()