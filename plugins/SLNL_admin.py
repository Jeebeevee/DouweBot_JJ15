from util import hook

''' plugin om wat admin dingen te regelen. '''


@hook.command
def join(inp, nick='', conn=None):
    nick = nick.lower()
    if nick != 'jeebeevee':
        return
    
    conn.join(inp)
    

@hook.command
def part(inp, nick='', conn=None):
    nick = nick.lower()
    if nick != 'jeebeevee':
        return
    #return(inp)
    conn.send('PART' + ' ' + inp)

@hook.command
def ping(inp, say=None, conn=None):
    say('pong')
