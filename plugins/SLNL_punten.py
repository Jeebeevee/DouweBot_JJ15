import MySQLdb
import re
from datetime import datetime 

from util import hook

'''plugin om punten te tellen van de verschillende andere bots op Scoutlink'''

# opbouw: naarbot [regex met tekst winnaar,locatie nick, locatie punten, als geen aantalpunten wat dan aan punten?]
bots = {
    'EA':['^([A-Za-z0-9_-]){2,31}\w\s(Jouw score is)\s([0-9]){0,1}\d)$',0,4],
    'Pimmetje':['^([A-Za-z0-9_-]){2,31}\w\s(krijgt)\s([0-9]){0,1}\d\s(punt.)$',0,2],
    'Burgemeester':['',0,None,10],
    'Proton':['^\w\s(pours)\w\s([A-Za-z0-9_-]){2,31}\w\s(a)*$',1],
    'Jeebeevee':['^([A-Za-z0-9_-]){2,31}\w\s(heeft)\s([0-9]){0,1}\d\s(punten gehaald.)$',0,2]
}

#<EA> geejee Jouw score is 1
def ConnectSQL(bot):
    #mysql
    #haal gegevens op uit config file
    db = bot.config.get('mysql', {})
    
    dbhost = db.get('dbhost', None)
    dbuser = db.get('dbuser', None)
    dbname = db.get('dbname', None)
    dbpass = db.get('dbpass', None)
    
    # Open database connection
    msl = MySQLdb.connect(dbhost,dbuser,dbpass,dbname)
    #db cursor
    cur = msl.cursor()
    return cur, msl


def InputSQL(sql, bot):
    #mysql
    # Open database connection
    cur, msl = ConnectSQL(bot)
    #query uitvoeren
    cur.execute(sql)
    msl.commit()
    if msl:
        msl.close()


def OutputSQL(sql, bot):
    #mysql
    # Open database connection
    cur, msl = ConnectSQL(bot)
    #query uitvoeren
    result = ''
    try:
        cur.execute(sql)
        result = cur.fetchone()
    except MySQLdb.Error, e:
        result = ''
    finally:
        if msl:
            msl.close()
    return result


#ctcp terug met deelnemersnummer
@hook.regex(r'^\x01NUMBERREPLY*')
def getDLnummer(inp, raw='', nick='', bot=None, pm=None):
    complete = raw[1:].split(':',1) #Parse the message into useful data 
    dlnummer = complete[1].split(' ')[1]
    sql = "UPDATE users SET DLnummer='%s' WHERE username='%s'" % (dlnummer, nick)
    InputSQL(sql, bot)

#ctcp terug met deelnemersmailadres
@hook.regex(r'^\x01MAILREPLY*')
def getDLmail(inp, raw='', nick='', bot=None, pm=None):
    complete = raw[1:].split(':',1) #Parse the message into useful data 
    dlmail = complete[1].split(' ')[1]
    sql = "UPDATE users SET email='%s' WHERE username='%s'" % (dlmail, nick)
    InputSQL(sql, bot)


@hook.singlethread
@hook.event('JOIN')
def getHostname(paraml, raw='', bot=None, conn=None, notice=None):
    #user komt online in game kanaal

    #raw message opbouw
    # :Jeebeevee!~Jeebeevee@ircop.scoutlink.net JOIN :#test
    complete = raw[1:].split(':',1) #Parse the message into useful data 
    info = complete[0].split(' ') #all user info
    nickname = info[0].split('!') #Nickname
    hostname = info[0].split('@') #hostname

    sql = "SELECT * FROM users WHERE username = '%s' AND hostname = '%s'" % (nickname[0],hostname[1] )
    nick_ids = OutputSQL(sql, bot)
    
    if nick_ids is not '' and nick_ids is not None:
        print nick_ids
        print "Joiner al bekend (exit)"
        return

    conn.cmd('PRIVMSG',[nickname[0],'\x01number\x01'])
    conn.cmd('PRIVMSG',[nickname[0],'\x01mail\x01'])

    sql = "INSERT INTO users (username, DLnummer, hostname, raw) VALUES ('%s' , '%d' , '%s' , '%s' )" % (nickname[0], 0,hostname[1],raw)
    InputSQL(sql, bot)

@hook.singlethread
@hook.event('NICK')
def nickChange(paraml, raw='', bot=None, conn=None):
    #nick is veranderd, deze opslaan in db

    # :Jeebeevee_NL: :Jeebeevee_NL!~Jeebeevee@ircop.scoutlink.net NICK Jeebeevee
    complete = raw[1:].split(':') #Parse the message into useful data 
    info = complete[0].split(' ') #all user info
    old_nick = info[0].split('!') #Old nickname on array key 0
    new_nick = info[2] #new nickname
    hostname = info[0].split('@') #hostname

    sql_old = "SELECT id FROM users WHERE username = '%s' AND hostname = '%s'" % (old_nick[0], hostname[1] )
    nick_ids = OutputSQL(sql_old, bot)

    if nick_ids is not '' and nick_ids is not None:
        print "Oude Nick bekend - update"
        # old nick bestaat, dus nick aanpassen
        sql = "UPDATE users SET username='%s' WHERE username='%s'" % (new_nick, old_nick[0] )
        InputSQL(sql, bot)

    else:
        print "Oude Nick nog niet bekend - add"
        # old nick bestaat niet, dus toevoegen aan de DB
        sql = "INSERT INTO users (username, DLnummer, hostname, raw) VALUES ('%s' , '%d' , '%s' , '%s' )" % (new_nick, 1, hostname[1], raw )
        InputSQL(sql, bot)

        conn.cmd('PRIVMSG',[new_nick,'\x01number\x01'])
        conn.cmd('PRIVMSG',[new_nick,'\x01mail\x01'])

@hook.singlethread
@hook.event('PRIVMSG')
def ReadPoints(paraml, nick='', raw='', bot=None):
    # tekst van bots?
    if any(nick in s for s in bots):

        #raw message opbouw
        # :Jeebeevee!~Jeebeevee@ircop.scoutlink.net PRIVMSG #test :.ptest
        complete = raw[1:].split(':',1) #Parse the message into useful data              
        info = complete[0].split(' ') #all sender info
        msgpart = complete[1] # message
        hostname = info[0].split('@')

        #hoort de tekst bij de bot? en geeft deze tekst de punten?
        match = re.search(re.escape(bots[nick][0]), msgpart, re.M|re.I)
        if match:
            #haal de nick van de speler en het aantal punten uit de tekst
            words = msgpart.split(' ')
            give_nick = words[bots[nick][1]]
            points = int(words[bots[nick][2]])

            sql = "SELECT id FROM users WHERE username = '%s'" % give_nick
            nick_id = OutputSQL(sql, bot)[0]

            # hackje voor EA. om alleen de punten te registreren die de laatste 10 vragen (minuten) zijn gehaald
            if nick == 'EA':
                sql = "SELECT points, timestamp FROM points WHERE user_id = '%d' AND bot = 'EA' ORDER BY date DESC LIMIT 1" % nick_id
                old_input = OutputSQL(sql, bot)
                if old_input:
                    old_time = old_input['date']
                    old_points = old_input['points']
                    FMT = '%Y-%m-%d %H:%M:%S'
                    new_time = datetime.now()
                    tdelta = new_time - old_time
                    tdelta = divmod(tdelta.total_seconds(),60)

                    if old_points != '' and tdelta[0] <= 10.0:
                        points = points-old_points
            #zijn er punten gegeven door de bot (sommige zeggen alleen dat je wint) dan 1 punt toekennen
            #dit moet nog variable worden, bot afhankelijk
            if isinstance( points, int):
                give_points = points
            else:
                give_points = 1

            sql = "INSERT INTO points (user_id, bot, points, nick) VALUES ( '%d' , '%s' , '%d' , '%s')" % (nick_id, nick, give_points, give_nick)
            InputSQL(sql, bot)
'''
# ontvangen punten via NOTICE
@hook.event("NOTICE")
def GetPoints(paraml, raw='', nick=''):
    #Komt de NOTICE van een van de bekende bots?
    if any(nick in s for s in bots):
        complete = irc_raw[1:].split(':',1) #Parse the message into useful data              
        info = complete[0].split(' ') #all sender info
        msgpart = complete[1] # message
        notice('TEXT: %s' % msgpart)

        #ctcp('','MAIL',msgpart)
        
'''
