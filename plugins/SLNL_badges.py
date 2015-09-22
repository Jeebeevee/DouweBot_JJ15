import MySQLdb
import time

from util import hook

'''plugin om de uitgegeven badges op te slaan voor de website van Scoutlink'''

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
    #print result
    return result

'''
user BADGE.LEUKSTECHAT
user BADGE.NIEUWEVRIEND
user BADGE.BESTEGROEP
user RECIEVED.BADGE.*
'''
'''
18:54:09 Gysta Gysta [~ScoutLink@ScoutLink-3b4a2395.direct-adsl.nl] requested unknown CTCP BADGE.LEUKSTECHAT from Gysta: geejee
>>> u'NOTICE Gysta ::Gysta!~ScoutLink@ScoutLink-3b4a2395.direct-adsl.nl PRIVMSG Douwe :\x01BADGE.LEUKSTECHAT geejee\x01'
18:54:09 geejee geejee [geejee@ScoutLink-74b38b2e.adsl-surfen.hetnet.nl] requested unknown CTCP RECIEVED.BADGE.LEUKSTECHAT from geejee: Gysta
>>> u'NOTICE geejee ::geejee!geejee@ScoutLink-74b38b2e.adsl-surfen.hetnet.nl PRIVMSG Douwe :\x01RECIEVED.BADGE.LEUKSTECHAT Gysta\x01'

18:29:12 geejee geejee [geejee@ScoutLink-74b38b2e.adsl-surfen.hetnet.nl] requested unknown CTCP RECIEVED.BADGE.LEUKSTECHAT from geejee: Gysta
:geejee!geejee@ScoutLink-74b38b2e.adsl-surfen.hetnet.nl PRIVMSG Douwe :RECIEVED.BADGE.LEUKSTECHAT Gysta
:Gysta!~ScoutLink@ScoutLink-3b4a2395.direct-adsl.nl PRIVMSG Douwe :BADGE.LEUKSTECHAT geejee
LEUKSTECHAT :: geejee
18:29:12 Gysta Gysta [~ScoutLink@ScoutLink-3b4a2395.direct-adsl.nl] requested unknown CTCP BADGE.LEUKSTECHAT from Gysta: geejee
'''

# Kijkt of er een CTCP request is die begint met BADGE.* dan actie uitvoeren.
# Deze kijkt of er een badge is uitgedeeld.
@hook.singlethread
@hook.regex(r'^\x01BADGE.*')
def badges(paraml, raw='', nick='', bot=None, conn=None):

    complete = raw[1:].split(':',1) #Parse the message into useful data 
    info = complete[0].split(' ') #all user info
    nickname = info[0].split('!') #Nickname
    hostname = info[0].split('@') #hostname
    
    badge = complete[1].split(' ')[0]
    badge = badge.split('.')[1]
    get_nick = complete[1].split(' ')[1]
    #print badge +' :: '+ get_nick

    sql_give = "SELECT id FROM users WHERE username = '%s' AND hostname = '%s'" % (nickname[0], hostname[1] )
    give_nick_id = OutputSQL(sql_give, bot)
    #print give_nick_id
    if give_nick_id is '' or give_nick_id is None:
        sql = "INSERT INTO users (username, DLnummer, hostname, raw) VALUES ('%s' , '%d' , '%s' , '%s' )" % (nickname[0], 2, hostname[1], raw )
        InputSQL(sql, bot)
        conn.cmd('PRIVMSG',[nickname[0],'\x01number\x01'])
        conn.cmd('PRIVMSG',[nickname[0],'\x01mail\x01'])
        sql_give = "SELECT id FROM users WHERE username = '%s' AND hostname = '%s'" % (nickname[0], hostname[1] )
        give_nick_id = OutputSQL(sql_give, bot)

    unixtime = int(time.time())
    sql_import = "INSERT INTO badges (badge, give_user_id, give_user, get_user, addtime, approved, give_user_raw) VALUES ('%s', '%d', '%s', '%s', '%d', '%d', '%s' )" % (badge, give_nick_id[0], nickname[0], get_nick, unixtime, 0, raw)
    print sql_import
    InputSQL(sql_import, bot)


# Kijkt of er een CTCP request is die begint met RECIEVED.BADGE.* dan actie uitvoeren.
# Deze checkt of de eerste heeft gestuurd en is ontvangen. en niet van dezelfde groep zijn
@hook.singlethread
@hook.regex(r'^\x01RECIEVED.BADGE.*')
def recievedBadges(paraml, raw='', nick='' , bot=None, conn=None):
    
    complete = raw[1:].split(':',1) #Parse the message into useful data 
    info = complete[0].split(' ') #all user info
    nickname = info[0].split('!') #Nickname
    hostname = info[0].split('@') #hostname
    
    badge = complete[1].split(' ')[0]
    badge = badge.split('.')[2]
    send_nick = complete[1].split(' ')[1]
    #print badge +' :: '+ get_nick

    time.sleep(10) #ff wachten op de zender

    timenow = int(time.time()) #nu
    oldtime = timenow-(11*60)  #nu - 11 minuten

    #zoek gegevnes van zendende user.
    #sql_send = "SELECT id, username, hostname FROM users WHERE username = '%s'" % (send_nick )
    #send_nick = OutputSQL(sql_send, bot)
    #zoek de bijbehorende badge record
    sql_badge = "SELECT id, give_user_id FROM badges WHERE give_user = '%s' AND get_user = '%s' AND addtime <= '%d' AND addtime >= '%d'" % (send_nick, nick, timenow, oldtime)
    print sql_badge	
    badge_id = OutputSQL(sql_badge, bot)
    
    #zoek gegevens van ontvangende user
    #get_nick_id = ""
    sql_get = "SELECT id FROM users WHERE username = '%s' AND hostname = '%s'" % (nickname[0], hostname[1] )
    get_nick_id = OutputSQL(sql_get, bot)
    if get_nick_id is '' or get_nick_id is None:
        sql = "INSERT INTO users (username, DLnummer, hostname, raw) VALUES ('%s' , '%d' , '%s' , '%s' )" % (nickname[0], 3, hostname[1], raw )
        InputSQL(sql, bot)
        conn.cmd('PRIVMSG',[nickname[0],'\x01number\x01'])
        conn.cmd('PRIVMSG',[nickname[0],'\x01mail\x01'])
        sql_get = "SELECT id FROM users WHERE username = '%s' AND hostname = '%s'" % (nickname[0], hostname[1] )
        get_nick_id = OutputSQL(sql_get, bot)

    print badge_id
    sql_badge_update = "UPDATE badges SET get_user_id = '%d', approved = '%d', get_user_raw = '%s' WHERE id = '%d'" % (get_nick_id[0], 1, raw, badge_id[0])
    print sql_badge_update
    InputSQL(sql_badge_update, bot)

    #print raw
    #notice('%s' % (raw))



