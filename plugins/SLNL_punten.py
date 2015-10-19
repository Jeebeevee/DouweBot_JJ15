import MySQLdb
import re
import time
from datetime import datetime 


from util import hook

'''plugin om punten te tellen van de verschillende andere bots op Scoutlink'''

# opbouw: naarbot [regex met tekst winnaar,locatie nick, locatie punten, als geen aantalpunten wat dan aan punten?]
# henkhuppelschoten krijgt 1 punt voor het antwoord :  neerstortpiloot.

bots = {
    #'222EA':[r'^([A-Za-z0-9_-]){2,31}\w\s(Jouw score is)\s([0-9]){0,1}\d)$',0,4],
    'Pimmetje':[r'^([A-Za-z0-9_-]){2,31}\w\s(krijgt)\s([0-9]){0,1}\d\s(punt voor het antwoord :)*',0,2],
    #'Burgemeester':[r'AAAAAAAAAAAAAA',0,None,10],
    #'Proton':[r'AAAAAAAAAAAAA^\w\s(pours)\w\s([A-Za-z0-9_-]){2,31}\w\s(a)*$',1],
    'Jeebeevee':[r'^([A-Za-z0-9_-]){2,31}\w\s(heeft)\s([0-9]){0,1}\d\s(punten gehaald.)$',0,2]
}
botnames = ['EA','Burgemeester','Jeebeevee','Pimmetje']

###################################################
##			Database connecties					###
###################################################

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

###################################################
##			User gegevens ontvangen				###
###################################################

#ctcp terug met deelnemersnummer
@hook.singlethread
@hook.regex(r'^\x01NUMBERREPLY*')
def getDLnummer(inp, raw='', nick='', bot=None, pm=None):
    complete = raw[1:].split(':',1) #Parse the message into useful data 
    if complete[1] == '':
        dlnummer = '9995'	
    else:
        dlnummer = complete[1].split(' ')
        if dlnummer[1] != '' or dlnummer[1] == None or isinstance(dlnummer[1], int):
            dlnummer = dlnummer[1]
        else:
            dlnummer = '9995'
    sql = "UPDATE users SET DLnummer='%s' WHERE username='%s'" % (dlnummer, nick)
    InputSQL(sql, bot)

#ctcp terug met deelnemersmailadres
@hook.singlethread
@hook.regex(r'^\x01MAILREPLY*')
def getDLmail(inp, raw='', nick='', bot=None, pm=None):
    complete = raw[1:].split(':',1) #Parse the message into useful data 
    dlmail = complete[1].split(' ')[1]
    sql = "UPDATE users SET email='%s' WHERE username='%s'" % (dlmail, nick)
    InputSQL(sql, bot)

def usercheck(nick, conn=None, bot=None):
    conn.send('WHOIS '+ nick)

@hook.singlethread
@hook.event('311')
def userChecker(inp, input=None, conn=None, bot=None):
    nickname = inp[1]
    hostname = inp[3]

    sql = "SELECT id FROM users WHERE username = '%s' AND hostname = '%s'" % (nickname, hostname)
    nick_id = OutputSQL(sql, bot)
    
    if nick_id is not '' and nick_id is not None:
        print nick_id
        print "Joiner al bekend (exit)"
    else:
        conn.cmd('PRIVMSG',[nickname,'\x01number\x01'])
        conn.cmd('PRIVMSG',[nickname,'\x01mail\x01'])

        sql = "INSERT INTO users (username, DLnummer, hostname, raw) VALUES ('%s' , '%d' , '%s' , '%s' )" % (nickname, 9991,hostname, input.params)
        InputSQL(sql, bot)

##################################
##	Punten verwerken			##
##################################
		
@hook.singlethread
@hook.event('PRIVMSG')
def regex_points(paraml, input=None, nick='', raw='', bot=None):
    # tekst van bots?
    if any(nick in s for s in botnames):
        #raw message opbouw
        # :Jeebeevee!~Jeebeevee@ircop.scoutlink.net PRIVMSG #test :.ptest
        complete = raw[1:].split(':',1) #Parse the message into useful data              
        info = complete[0].split(' ') #all sender info
        msgpart = complete[1] # message
        hostname = info[0].split('@')
		
        #hackje voor pimmetje
        msgpart = msgpart.lstrip()
        #bericht = msgpart.split(' ',1)

        #hoort de tekst bij de bot? en geeft deze tekst de punten?
        p = re.compile(r'^([A-Za-z0-9_-]){2,31}\w\s(krijgt 1 punt voor het antwoord)\w*')
        match = p.match(msgpart)
        print match
        if match:
        #if bericht[1] == 'krijgt 1 punt voor het antwoord*':
            print 2
       	    #haal de nick van de speler en het aantal punten uit de tekst
            words = msgpart.split(' ')
            give_nick = words[bots[nick][1]]
            #points = words[bots[nick][2]]
            points = 1
            usercheck(give_nick, conn, bot);
            time.sleep(2)
            GetPoints(nick, give_nick, int(points), bot)
  

# ontvangen punten via CTCP
@hook.singlethread
@hook.event(r'^\x01POINTS*')
def ctcp_points(paraml, raw='', nick='', bot=None):
    #Komt de CTCP van een van de bekende bots?
    if  any(nick in s for s in botnames):
        #raw message opbouw
        # :Jeebeevee!~Jeebeevee@ircop.scoutlink.net PRIVMSG #test :.ptest
        complete = raw[1:].split(':',1) #Parse the message into useful data              
        info = complete[0].split(' ') #all sender info
        msgpart = complete[1] # message
        hostname = info[0].split('@')

        words = msgpart.split(' ')
        give_nick = words[1]
        points = words[2]

        usercheck(give_nick, conn, bot);
        time.sleep(2)
        GetPoints(nick, give_nick, int(points), bot)



# ontvangen punten via NOTICE
@hook.singlethread
@hook.event('NOTICE')
def notice_points(raw, nick='', conn=None, bot=None):
    #Komt de NOTICE van een van de bekende bots?
    print raw
    if any(nick in s for s in botnames):

        give_nick = raw[1].split(' ')[0]
        points = raw[1].split(' ')[1]

        usercheck(give_nick, conn, bot);
        time.sleep(2)
        GetPoints(nick, give_nick, int(points), bot)

# verwerk de pinten die gegeven zijn.
def GetPoints(nick, give_nick, points, bot=None):

    sql = "SELECT id FROM users WHERE username = '%s'" % give_nick
    nick_id = OutputSQL(sql, bot)[0]
    #if nick_id == '' or nick_id == None:
    #nick_id = usercheck(give_nick, conn, bot);

    unixtime = int(time.time())

    # hackje voor EA. om alleen de punten te registreren die de laatste 10 vragen (minuten) zijn gehaald
    if nick == 'EA':
        max_time = unixtime - (10*60)
        sql = "SELECT points FROM 'points' WHERE user_id = '%d' AND bot = 'EA' AND time <= '%d' AND time >= '%d' ORDER BY time DESC LIMIT 1" % (nick_id, unixtime, max_time)
        time.sleep(2)
        old_input = OutputSQL(sql, bot)
        if old_input:
            if old_input[0] != '': 
                sql = "UPDATE 'points' SET points = '%d' time = '%d'  WHERE user_id = '%d' AND bot = 'EA' AND time <= '%d' AND time >= '%d'" % (points, unixtime, nick_id, unixtime, max_time)
                InputSQL(sql, bot)
                print 'Points from: ' + nick + ' to: ' + give_nick
                return

    sql = "INSERT INTO points (user_id, bot, points, time, nick) VALUES ( '%d' , '%s' , '%d' , '%d' , '%s')" % (nick_id, nick, points, unixtime, give_nick)
    InputSQL(sql, bot)
    print 'Points from: ' + nick + ' to: ' + give_nick



