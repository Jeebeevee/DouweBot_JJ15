import socket
import subprocess
import time

from util import hook, http

socket.setdefaulttimeout(10)  # global setting


def get_version():
    p = subprocess.Popen(['git', 'log', '--oneline'], stdout=subprocess.PIPE)
    stdout, _ = p.communicate()
    p.wait()

    revnumber = len(stdout.splitlines())

    shorthash = stdout.split(None, 1)[0]

    http.ua_skybot = 'Skybot/r%d %s (http://github.com/rmmh/skybot)' \
        % (revnumber, shorthash)

    return shorthash, revnumber


# autorejoin channels
@hook.event('KICK')
def rejoin(paraml, conn=None):
    if paraml[1] == conn.nick:
        if paraml[0].lower() in conn.conf.get("channels", []):
            conn.join(paraml[0])


# join channels when invited
@hook.event('INVITE')
def invite(paraml, conn=None):
    conn.join(paraml[-1])


@hook.event('004')
def onjoin(paraml, conn=None):
    # identify to services
    nickserv_password = conn.conf.get('nickserv_password', '')
    nickserv_name = conn.conf.get('nickserv_name', 'nickserv')
    nickserv_command = conn.conf.get('nickserv_command', 'IDENTIFY %s')
    if nickserv_password:
        conn.msg(nickserv_name, nickserv_command % nickserv_password)
        time.sleep(1)
    
    #hackje voor oper rechten/botline
    oper_nickname = conn.conf.get('oper_nickname')
    oper_password = conn.conf.get('oper_password')
    if oper_password:
        conn.cmd('OPER '+ oper_nickname +' '+ oper_password)
        time.sleep(2)
        conn.send('PART #opers')

    # set mode on self
    mode = conn.conf.get('mode')
    if mode:
        conn.cmd('MODE', [conn.nick, mode])

    # join channels
    for channel in conn.conf.get("channels", []):
        conn.join(channel)
        # hackje voor rechten via Lotje
        if channel != '#dutchbots':
            time.sleep(3)
            conn.msg('#dutchbots','SETRIGHTS '+ channel +' TYCEmEMCznK5Ebyu8SZ')
        #conn.cmd('MODE '+ channel +' +Y '+ conn.nick )
        time.sleep(1)  # don't flood JOINs

    # set user-agent
    ident, rev = get_version()


@hook.regex(r'^\x01VERSION\x01$')
def version(inp, notice=None):
    ident, rev = get_version()
    notice('\x01VERSION skybot %s r%d - http://github.com/rmmh/'
           'skybot/\x01' % (ident, rev))
