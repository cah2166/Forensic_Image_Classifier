import sqlite3, os, sys, support, support_clamd, support_tf

def opendb(dbfilename):
    global con
    global cursor
    if os.path.isfile(dbfilename) and os.access(dbfilename, os.R_OK): # checks if the dbfile already exists
        con = sqlite3.connect(dbfilename, check_same_thread=False)  # Connects to the already connected sqlite db 
        cursor = con.cursor() # assigns cursor to pass for opening database 
    else:  # If database file does not exist
        con = sqlite3.connect(dbfilename)  # Establishes sqlite connection for new database
        cursor = con.cursor() # assigns cursor to pass for opening database
        createNewTables(cursor) # calls create tables 
    return cursor

def createNewTables(cursor): # Creates database tables 
    query = '''DROP TABLE IF EXISTS CaseTab;
        CREATE TABLE CaseTab(
        CaseKey INTEGER PRIMARY KEY AUTOINCREMENT,
        Casename TEXT,
        CaseDate TEXT
        );
        
        DROP TABLE IF EXISTS RunTab;
        CREATE Table RunTab (
        RunKey INTEGER PRIMARY KEY AUTOINCREMENT,
        CaseKey INTEGER,
        RunDate TEXT,
        Timestamp TEXT
        );

        DROP TABLE IF EXISTS FileStat;
        CREATE Table FileStat(
        FileKey INTEGER PRIMARY KEY AUTOINCREMENT,
        RunKey INTEGER,
        Filename TEXT,
        Hash_Type TEXT,
        Hash TEXT,
        MODE TEXT,
        UID TEXT,
        GID TEXT,
        Modify_Time TEXT,
        Access_Time TEXT,
        Change_Time TEXT,
        FileMagic TEXT
        );

        DROP TABLE IF EXISTS FileAVScan;
        CREATE Table FileAVScan (
        FileKey INTEGER PRIMARY KEY,
        RunKey INTEGER,
        Result TEXT
        );

        DROP TABLE IF EXISTS ImageClassScan;
        CREATE Table ImageClassScan (
        ImageClassKey INTEGER PRIMARY KEY AUTOINCREMENT,
        FileKey INTEGER,
        RunKey INTEGER,
        Class TEXT,
        Score TEXT
        );
        '''
    cursor.executescript(query)
    return

def startCase(case, cursor):
    #Create Case if require
    casekey = getCurrentCaseKey(case,cursor)
    #Create new row
    ndate=support.getDate()
    Timestamp=support.getTime()
    query = ('''INSERT INTO RunTab (caseKey,RunDate,Timestamp) Values("%s", "%s", "%s");''' % (casekey,ndate,Timestamp))
    cursor.executescript(query)
    con.commit()
    current=getCurrentRunKey(casekey, cursor)
    support.msg("Database Key is: %s" % (current))
    return current

def getCurrentCaseKey(case, cursor):
    query = ('''SELECT CaseKey FROM CaseTab WHERE CaseName LIKE "%s"''' % (case))
    cursor.execute(query)
    row = cursor.fetchone()
    if row == None:
        ndate=support.getDate()
        query = ('''INSERT INTO CaseTab (Casename,CaseDate) Values("%s","%s");''' % (case,ndate))
        cursor.executescript(query)
        con.commit()
        query = ('''SELECT CaseKey FROM CaseTab WHERE CaseName LIKE "%s"''' % (case))
        cursor.execute(query)
        row = cursor.fetchone()
    return row[0]

def getCurrentRunKey(casekey, cursor):
    query = ('''SELECT RunKey FROM RunTab WHERE caseKey LIKE "%s" ORDER BY RunKey DESC''' % (casekey))
    cursor.execute(query)
    row = cursor.fetchone()
    print(row)
    current = row[0]
    return current

def getLastRun(casename, cursor):
    query = ('''SELECT CaseKey FROM CaseTab WHERE CaseName LIKE "%s"''' % (casename))
    cursor.execute(query)
    row = cursor.fetchone()    
    if row == None:
        support.msg("There were not run entries for the case.")
        return
    casekey = row[0]
    RunKey = getCurrentRunKey(casekey,cursor)
    query= ('''SELECT * FROM FileStat WHERE RunKey = "%s" LIMIT 1;''' % (RunKey))
    cursor.execute(query)
    row = cursor.fetchone()
    try:
        (RowId,RunKey,Filename,Hash_Type,Hash,MODE,UID,GID,Modify_Time,Access_Time,Change_Time,FileMagic) = row
        support.msg('Output from the last file query')
        support.msg(str(RunKey)+' '+Filename+' '+Hash_Type+' '+Hash+' '+MODE+' '+UID+' '+GID+' '+Modify_Time+' '+Access_Time+' '+Change_Time+' '+FileMagic)
    except:
        support.msg("Errors in grabbing the last run. Please check if there are entries in the database.")
    
def scanfile_sql(infile, cursor, runkey, filekey):
    cd=support_clamd.openClam()
    if cd:
        result = support_clamd.scanfile(infile, cd)
        print(result)
        if result[1]:
            try:
                query = ('''INSERT INTO FileAVScan (FileKey, RunKey, Result) VALUES (%d, %d, "%s")''' % (filekey, runkey, result[1]))
                cursor.executescript(query)
            except:
                support.msg("Could not send AV results to database. (%s - %s)" % (infile,result))
        else:
            support.msg("The AV did not detect a virus for %s." % (infile))

def tensorfile_sql(cursor, runkey, filekey, infile):
    top_k, label_lines, predictions=support_tf.classifyImage(infile)
    for node_id in top_k:
        human_string = label_lines[node_id]
        score = predictions[0][node_id]
        query = ('''INSERT INTO ImageClassScan (FileKey,RunKey,Class,Score) VALUES ("%s","%s","%s","%s");''' % (filekey,runkey,human_string,score))
        cursor.executescript(query)

def addFilestat(cursor, runkey, FILENAME, htype, hash,stat_mode, stat_UID, stat_GID,m_time, a_time, c_time, magic_buff):
    query = ('''INSERT INTO FileStat (RunKey,Filename,Hash_Type,Hash,MODE,UID,GID,Modify_Time,Access_Time,Change_Time,FileMagic) VALUES ("%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s");''' % (runkey,FILENAME,htype, hash,stat_mode, stat_UID, stat_GID,m_time, a_time, c_time, magic_buff))
    cursor.executescript(query)
    query = ('''SELECT FileKey FROM FileStat WHERE RunKey = "%s" and Filename = "%s"''' % (runkey,FILENAME))
    cursor.execute(query)
    file=cursor.fetchone()
    filekey=file[0]
    return filekey

def closedb():
    global con
    con.commit()
    con.close()

if __name__ == '__main__':
    CASENAMETEST = 'TestCase'
    cursor = opendb('sqltest1.db')
    runkey=startCase(CASENAMETEST, cursor)
    casekey=getCurrentCaseKey(CASENAMETEST,cursor)
    for infile in sys.argv[1:]:
        filekey=addFilestat(cursor,runkey,infile,"TestHash","acbdefghi_123456789","777","testUID","testGID","MTime","ATime","CTime",'Abra-Ka-Dabra')
        scanfile_sql(infile, cursor, runkey, filekey)
    getLastRun(CASENAMETEST, cursor)
    closedb()