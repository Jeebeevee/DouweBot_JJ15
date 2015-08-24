import MySQLdb

from util import hook

'''plugin om de uitgegeven badges op te slaan voor de website van Scoutlink'''
'''
def ConnectSQL(event):
    #mysql
    #haal gegevens op uit config file
    db = event.bot.config.get('mysql', {})
    
    dbhost = db.get('dbhost', None)
    dbuser = db.get('dbuser', None)
    dbname = db.get('dbname', None)
    dbpass = db.get('dbpass', None)
    
    # Open database connection
    msl = pymysql.connect(dbhost,dbuser,dbpass,dbname,cursorclass=pymysql.cursors.DictCursor)
    #db cursor
    cur = msl.cursor()
    return cur, msl


def InputSQL(sql, event):
    #mysql
    # Open database connection
    cur, msl = ConnectSQL(event)
    #query uitvoeren
    cur.execute(sql)
    msl.commit()


def OutputSQL(sql, event):
    #mysql
    # Open database connection
    cur, msl = ConnectSQL(event)
    #query uitvoeren
    cur.execute(sql)
    result = cur.fetchone()
    return result
'''
# Kijkt of er een CTCP request is die begint met BADGE.* dan actie uitvoeren.
# Deze kijkt of er een badge is uitgedeeld.
@hook.regex(r'^\x01BADGE.*')
def badges(paraml, raw='', nick='' , notice=None):
    #print inp
    #ctcp("Testje", "BADGE", nick)
    notice('%s' % (raw))

# Kijkt of er een CTCP request is die begint met RECIEVED.BADGE.* dan actie uitvoeren.
# Deze checkt of de eerste heeft gestuurd en is ontvangen. en niet van dezelfde groep zijn
@hook.regex(r'^\x01RECIEVED.BADGE.*')
def recievedBadges(paraml, raw='', nick='' , notice=None, ctcp=None):
    #print inp
    notice('%s' % (raw))

'''
user BADGE.LEUKSTECHAT
user BADGE.NIEUWEVRIEND
user BADGE.BESTEGROEP
user RECIEVED.BADGE.*
'''

