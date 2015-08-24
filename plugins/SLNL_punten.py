import MySQLdb
import re
from datetime import datetime 

from util import hook

'''plugin om punten te tellen van de verschillende andere bots op Scoutlink'''

#bots = ['Jeebeevee','EA','Pimmetje']
#string = '^([A-Za-z0-9_-]){2,31}\w\s(heeft)\s([0-9]){0,1}\d\s(punten gehaald.)$'

# opbouw: naarbot [regex met tekst winnaar,locatie nick, locatie punten, als geen aantalpunten wat dan aan punten?]
bots = {
    'EA':['^([A-Za-z0-9_-]){2,31}\w\s(Jouw score is)\s([0-9]){0,1}\d)$',0,4],
    'Pimmetje':['^([A-Za-z0-9_-]){2,31}\w\s(krijgt)\s([0-9]){0,1}\d\s(punt.)$',0,2],
    'Burgemeester':['',0,None,10],
    'Proton':['^\w\s(pours)\w\s([A-Za-z0-9_-]){2,31}\w\s(a)*$',1],
    'Jeebeevee':['^([A-Za-z0-9_-]){2,31}\w\s(heeft)\s([0-9]){0,1}\d\s(punten gehaald.)$',0,2]
}


'''
to do:
- /ctcp nick number => geeft deelnemersnummer, deze opslaan in DB
---- [12:13:32] [NL_Nick NUMBERREPLY] ######
 - /ctcp nickname mail voor mail-adres ook in DB

'''

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


def OutputSQL(sql, bot):
    #mysql
    # Open database connection
    cur, msl = ConnectSQL(bot)
    #query uitvoeren
    try:
        cur.execute(sql)
        result = cur.fetchone()
    except MySQLdb.Error, e:
        result = ''
    return result

#ctcp terug met deelnemersnummer
@hook.regex(r'^\x01NUMBERREPLY*')
def getDLnummer(paraml, raw='', nick='', bot=None, pm=None):
    #pm(nick +' === '+ paraml,'Jeebeevee')
    sql = "UPDATE users SET DLnummer='%d' WHERE username='%s'" % (int(paraml),nick)
    InputSQL(sql, bot)
    #>>> u'PRIVMSG Gysta :\x01number\x01'
    #19:49:59 Gysta Gysta [~ScoutLink@ScoutLink-3b4a2395.direct-adsl.nl] requested unknown CTCP NUMBERREPLY from Gysta: 123456
    #>>> u'PRIVMSG Jeebeevee ::Gysta!~ScoutLink@ScoutLink-3b4a2395.direct-adsl.nl PRIVMSG Douwe :\x01NUMBERREPLY 123456\x01'
    

@hook.event('JOIN')
def getHostname(paraml, raw='', bot=None, conn=None, notice=None):
    #user komt online in game kanaal

    #raw message opbouw
    # :Jeebeevee!~Jeebeevee@ircop.scoutlink.net JOIN :#test
    complete = raw[1:].split(':',1) #Parse the message into useful data 
    info = complete[0].split(' ') #all user info
    nickname = info[0].split('!') #Nickname
    hostname = info[0].split('@') #hostname

    sql = "SELECT * FROM users WHERE username = '%s' AND hostname = '%s'" % (nickname[0],hostname[1])
    nick_ids = OutputSQL(sql, bot)
    print nick_ids[0]
    
    if nick_ids[0] != '' or nick_ids[0] != None :
        return

    conn.cmd('PRIVMSG',[nickname[0],'\x01number\x01'])

    sql = "INSERT INTO users (username, DLnummer, hostname, raw) VALUES ('%s' , '%d' , '%s' , '%s' )" % (nickname[0], 0,hostname[1],raw)
    InputSQL(sql, bot)


@hook.event('NICK')
def nickChange(paraml, raw='', bot=None, conn=None):
    #nick is veranderd, deze opslaan in db

    # :Jeebeevee_NL: :Jeebeevee_NL!~Jeebeevee@ircop.scoutlink.net NICK Jeebeevee
    complete = raw[1:].split(':') #Parse the message into useful data 
    info = complete[0].split(' ') #all user info
    old_nick = info[0].split('!') #Old nickname on array key 0
    new_nick = info[2] #new nickname
    hostname = info[0].split('@') #hostname

    #conn.send('NOTICE Jeebeevee ' + new_nick + ' ' + old_nick[0])

    #sql_new = "SELECT * FROM users WHERE username = '%s' AND hostname = '%s'" % (new_nick, hostname[1])
    sql_old = "SELECT * FROM users WHERE username = '%s' AND hostname = '%s'" % (old_nick[0], hostname[1])
    #new_nick_exist = OutputSQL(sql_new, bot)
    old_nick_exist = OutputSQL(sql_old, bot)
    #conn.send('NOTICE Jeebeevee '+ old_nick_exist[1] + ' +++ ' + new_nick_exist[1])
    if old_nick_exist[1] != '' or old_nick_exist[1] != None:
        # old nick bestaat, dus nick aanpassen
        sql = "UPDATE users SET username='%s' WHERE username='%s'" % (new_nick,old_nick[0])
        InputSQL(sql, bot)
        #elif new_nick_exist[1] == '' and old_nick_exist[1] == '':
    else:
        # old nick bestaat niet, dus toevoegen aan de DB
        sql = "INSERT INTO users (username, DLnummer, hostname, raw) VALUES ('%s' , '%s' , '%d' , '%s' )" % (nickname[0],1,hostname[1],raw)
        InputSQL(sql, bot)

        conn.cmd('PRIVMSG',[nickname[0],'\x01number\x01'])

    #elif new_nick_exist != '' and old_nick_exist == '':
    #    sql = 


@hook.event('PRIVMSG')
def ReadPoints(paraml, nick='', raw='', bot=None):
    # tekst van bots?
    if any(nick in s for s in bots):

        #raw message opbouw
        # :Jeebeevee!~Jeebeevee@ircop.scoutlink.net PRIVMSG #test :.ptest
        complete = raw[1:].split(':',1) #Parse the message into useful data              
        info = complete[0].split(' ') #all sender info
        msgpart = complete[1] # message
        #sender = info[0].split('!') #sender username
        hostname = info[0].split('@')

        #hoort de tekst bij de bot? en geeft deze tekst de punten?
        match = re.search(bots[nick][0],msgpart)
        if match:
            #haal de nick van de speler en het aantal punten uit de tekst
            words = msgpart.split(' ')
            give_nick = words[bots[nick][1]]
            points = int(words[bots[nick][2]])

            sql = "SELECT id FROM users WHERE username = '%s'" % give_nick
            nick_id = OutputSQL(sql, bot)[0]
            print nick_id
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

            sql = "INSERT INTO points (user_id, bot, points, nick) VALUES ( '%d' , '%s' , '%d' , '%s')" % (nick_id[0], nick, give_points, give_nick)
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
        
@hook.regex(r'^\x01MAILREPLY .*\x01$')
def my_ctcp_hook(match, notice=None):
    ctcp_contents = match.group(1)
    ctcp(ctcp_contents,'VERSION','Jeebeevee')

@hook.irc_raw("NOTICE")
def not_test(irc_raw, notice=None):
    notice('dus: %s' % irc_raw)
'''
