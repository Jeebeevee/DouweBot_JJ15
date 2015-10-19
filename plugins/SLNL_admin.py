import re

from util import hook

''' plugin om wat admin dingen te regelen. '''


@hook.command
def join(inp, input=None, conn=None):
    if input.host != 'ircop.scoutlink.net':
        return
    
    conn.join(inp)
    

@hook.command
def part(inp, input=None, conn=None):
    if input.host != 'ircop.scoutlink.net':
        return
    #return(inp)
    conn.send('PART' + ' ' + inp)

@hook.command
def ping(inp, input=None, say=None, conn=None):
    print type(input.inp)
    say('pong')

@hook.event('PRIVMSG')
def privates(paraml, input=None, conn=None, bot=None):
    if input.inp[0] == conn.nick: # and not re.match(r'^\x01*', input.msg):
            conn.msg('#dutchbots', '[PRIVAT] %s: %s' % (input.nick, input.msg))



#@hook.event('311')
#def whois(raw, input=None, nick=''):
#    print input

@hook.command
def test(inp, nick='', conn=None):
    #conn.send('VERSION'+ ' ' + nick)
    conn.send('WHOIS Baloe')

#@hook.regex(r'^\x01TEST*')
#def ctcptest(raw, input=None):
#    print type(input.inp)  

#@hook.event('NOTICE')
#def notice(raw, nick='', conn=None):
#    print nick
#    print raw[0]
#    print raw[1]
