#!/usr/bin/python2.7
# batcot barebone

"""
                nixers/IOTek in-house solution for IRC automation

    Brought to you by dami-ooooh <dami0@iotek.org> & deadcat <dcat@iotek.org>

"""

import sys
import time
import ssl
import irc.client
import urllib2
import json
import datetime
import pytz
from math import floor
from BeautifulSoup import BeautifulSoup
from configs import settings, wordlist

config = {}

def get_title (url) :
	bufsiz = 2048
	prefix = ''
	if "://www.youtube." in url or "://youtu.be" in url: url = url.replace("http://", "https://")
	try:
		resp = urllib2.urlopen(url)
		html = resp.read()
		soup = BeautifulSoup(html, convertEntities=BeautifulSoup.HTML_ENTITIES)
	except Exception as e:
		print ("[ERROR] (get_title): %s" % e)
		return None
	if soup.title :
		if soup.title.string :
			if '://www.youtube.' in url or '://youtu.be' in url:
				prefix = "\x02\x031,15YOU\x030,4TUBE\x03  "
			if ".wikipedia.org/" in url: prefix = "\x02\x031,15WIKIPIDEA\x03  "
			return '%s%s' % (prefix, soup.title.string.strip())
		else:
			print("[ERROR] (title): no soup.title.string")
			return None
	else :
		print("[ERROR] (title): no soup.title")
		return None

def user_seen (user) :
	try: secs =  time.time() - seen_list[user]
	except KeyError: return "I haven't seen them around, nixer."
        units = [(2592000, "month(s)"), (604800, "week(s)"), (86400, "day(s)"), 
                (3600, "hour(s)"), (60, "minute(s)"), (1, "sec(s)")]
        prop_time = ""
        for unit in units:
            if secs > units[0][0]*2: return "They be gone, dude."
            if secs < 10:            return "Look up, dummy!"
            if secs > unit[0]:
                tmp = floor(secs/unit[0])
                secs -= tmp*unit[0]
                prop_time = " ".join([prop_time, str(int(tmp)), unit[1]])
                print (prop_time)

        return prop_time

def lastfm_resp (user) :
	try: buf = urllib2.urlopen('http://ws.audioscrobbler.com/2.0/?method=user.getrecenttracks&api_key=%s&limit=1&format=json&user=%s' % ('4c075129b62c24467502b31e40e2cb34', user)).read()
	except: return None
	obj = json.loads(buf)
                            
	if "recenttracks" not in obj : return None
	try:
		artist = obj['recenttracks']['track'][0]['artist']['#text']
		album  = obj['recenttracks']['track'][0]['album']['#text']
		track  = obj['recenttracks']['track'][0]['name']
		try : return "%s - %s (%s)" % (artist, track, album)
		except : return None
	except Exception as e:
		try:
			artist = obj['recenttracks']['track']['artist']['#text']
			album  = obj['recenttracks']['track']['album']['#text']
			track  = obj['recenttracks']['track']['name']
		except Exception as e:
			print ('[ERROR] (TypeError): %s' % e)
			return None

		try : return "%s - %s (%s)" % (artist, track, album)
		except:
			print ("[ERROR] can't return artist,track,album")
			return None

def tz_print (tz) :
	try : rtz = pytz.timezone(tz)
	except pytz.exceptions.UnknownTimeZoneError: return "I don't know that timezone"
	rtime = datetime.datetime.now(rtz)
	return rtime.strftime("%Z: %A %d, %H:%M:%S")


def proc_cmd (c, e) :

	if "NeoTerra" in e.source.nick :
		c.privmsg(e.target, "<NeoTerra> I don't trust a bot with chanop privileges")
		return

        msg = ""
        cmd = e.arguments[0][1:]
        if len(cmd) > 1:
            cmd = cmd.split(' ')[0]
        t = (e.arguments[0].encode("ascii", "ignore")).split(' ')
        nick = e.source.nick.encode("ascii", "ignore")
        cmdlist = ("best", "worst")
        setlist = ("tz", "np")

	if cmd == 'np' :
                if len(t) > 1:
                    t = t[1]
                elif nick in config: 
                        if "np" in config[e.source.nick]:
                                t = config[e.source.nick]["np"]
                else: t = nick
		print('[LASTFM] (%s) %s' % (e.target, t))
                resp = lastfm_resp(t)
                if resp: msg = resp
                else: msg = "Unable to locate information."

	elif cmd == 'seen' :
		if len(t) < 2: return
		t = t[1].encode("ascii", "ignore")
                msg = user_seen(t)

        elif cmd == 'help':
                msg = 'https://github.com/nixers-projects/batcot'

        elif cmd == 'ping':
                msg = 'pong'

	elif cmd == 'tz' :
                if len(t) > 1 and t[1] in config:
                    print t[1]
                    if "tz" in config[t[1]]:
                            t[1] = config[t[1]]["tz"]
                elif nick in config:
                        if "tz" in config[nick]:
                                t.append(config[nick]["tz"])
		if len(t) < 2 : return
                msg = tz_print(t[1])

        elif cmd in cmdlist :
                t = t[0][1:]
                if t in config[nick]: msg = config[nick][t]

        elif cmd in wordlist :
                msg = wordlist[cmd]

        elif cmd == 'list' :
                msg = ' '.join(wordlist.keys())
                msg = msg + " phrasing"

	elif cmd == 'set' :
                if len(t) < 3: return
                t = t[1:]
                print(t[0])

                if nick not in config: config[nick] = {}

                response = " ".join(t[1:])
                if t[0] in setlist:            config[nick][t[0]] = t[1]
                elif t[0] in cmdlist:          config[nick][t[0]] = response

                f = open("users.conf", "w")
                for nck in config:
                        prnt = nck
                        for key in config[nck]:
                                prnt = "|_|".join([prnt, key + ":" + config[nck][key]])
                        prnt = prnt + "\n"
                        f.write("%s" % (prnt))
                f.close()
            
                msg = nick + " has been added for processing. Welcome to the system."
                c.privmsg(e.target, "%s" % msg)
                return

#        else: msg = e.source.nick + ": Unrecognised command."

        print(cmd)
        if msg: 
                msg = "".join([nick, ": ", msg])
        	c.privmsg(e.target, "%s" % msg)

def reload_s() :
    from configs import wordlist

def on_connect (c, e) :
	if settings['ns_pass'] :
		c.privmsg("NickServ", "IDENTIFY %s" % settings['ns_pass'])
		print("nickserv pass")
		time.sleep(3)
	for chan in settings['chans'] :
		print("[JOIN] %s" % chan)
		c.join(chan)

def on_disconnect (c, e) :
        c.reconnect()

#def on_privmsg (c, e) :
#	# c(onnection), e(vent)
#        if 
#	None


def on_pubmsg (c, e) :
	seen_list[e.source.nick] = time.time()
	if e.arguments[0].startswith(settings['prefix']) :
		proc_cmd(c, e)
        if e.arguments[0] == 'phrasing' :
                c.privmsg(e.target, "BOOM!")
        if "yrmt" in e.source.nick and "brb" in e.arguments[0] and len(e.arguments[0]) < 4:
            c.privmsg(e.target, "eats")
        if "yrmt" in e.source.nick and "bbl" in e.arguments[0] and len(e.arguments[0]) < 4:
            c.privmsg(e.target, "sleeps")
	elif "https://" or "http://" in e.arguments[0] :
		for i in e.arguments[0].split(' ') :
			if i.startswith("http://") or i.startswith("https://"):
				if i.endswith('jpg') or i.endswith('png') or i.endswith('gif') :
					print('[TITLE] is image')
					break
				print('[TITLE] %s' % i)
				title = get_title(i)
				if title :
					try: c.privmsg(e.target, title)
					except Exception as e:
						print("[ERROR] (privmsg): %s" % e)
						return
				break

def read_conf() :
        
        f = open("users.conf", "r")
        for line in f:
                line = line.split("|_|")
                config[line[0]] = {}
                for lmnt in line[1:]:
                        lmnt = lmnt.split(":")
                        config[line[0]][lmnt[0]] = lmnt[1].strip("\n")
        print(config)
        f.close()

if (__name__ == '__main__') :
	# ssl?
	ssl_factory = irc.connection.Factory(wrapper=ssl.wrap_socket) if settings['ssl'] else None
	client = irc.client.IRC()
	server = client.server()
	server.buffer_class.errors = 'replace'
	global seen_list
	seen_list = {}

        try: 
                read_conf() 
        except IOError:
                print("we be broke")

	try:
		if ssl_factory:
			c = server.connect(
					settings['host'],
					settings['port'],
					settings['nick'],
					username=settings['user'],
					ircname=settings['real'],
					connect_factory=ssl_factory,
					)
		else:
			c = server.connect(
					settings['host'],
					settings['port'],
					settings['nick']
					)
	except irc.client.ServerConnectionError:
		print(sys.exc_info()[1])
		raise SystemExit(1)

	c.add_global_handler("welcome", on_connect)
#	c.add_global_handler("privmsg", on_privmsg)
	c.add_global_handler("pubmsg",  on_pubmsg)
        c.add_global_handler("disconnect", on_disconnect)
	# other handlers

	client.process_forever()


