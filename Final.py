#!/usr/bin/python
import logging, os, support

#Program function
DESCRIPTION="My Forensic Program"
VERSION='1.2'


if __name__ == '__main__':
    #Calls multiple functions in the support module to generate logs and store in log_filename. 
    support.ParseCmdLine(DESCRIPTION)
    # Creates the log directory if it doesn't exist
    logdir=os.path.abspath('.')+'/'+support.gl_args.case
    if not os.path.exists(logdir):
        os.makedirs(logdir)

    # Gets prefix for logfile
    prefix=support.getPrefix()

    # Generates string based off of PREFIX argument and time generates in the support getTime function
    log_filename=''.join([prefix,support.getDate(),'.txt'])

    # Create basic syntax configuration for logging 
    logging.basicConfig(filename=logdir+'/'+log_filename, level=logging.DEBUG, format='%(asctime)s %(message)s')
    
    # Calls start log using global variables and checkExternalTime from support
    support.startLog(DESCRIPTION,VERSION)
    support.checkExternalTime()
    support.additionalLogs()
    # Gets into the scanning module of the program
    support.mainMod()

    # Called from maingprog to store done string in the log when main finishes to excute
    support.msg('done')