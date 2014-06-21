#!/usr/bin/python
import socket
import sys
import threading
import re
##load config
import config

##command line

def commandline():
	try:	
		while 1:
			command=input('>> ')
			if len(command)>0:
				if command.split()[0]=='tell':
					irc.send_message_to_channel(command[5:])
				if command=='exit':
					irc.send('QUIT :got exit command')
					sys.exit(0)
				if command=='help':
					print('Available commands:')
					print('tell <bleh> == send message to channel')
					print('exit        == stop the bot')
					print('help        == print\'s this message')
	except KeyboardInterrupt:
		sys.exit(0)
##bot main code
class irc_connection:
	def __init__(self, host, port, nick, ident, name, channel, debug, owners):
		self.address_set=0
		self.host=host
		self.port=port
		self.nick=nick
		self.ident=ident
		self.name=name
		self.channel=channel
		self.connection=socket.socket()
		self.connection.connect((self.host,self.port))
		self.debug=debug
		self.owners=owners
		self.send("NICK %s" % self.nick)
		self.send("USER %s %s bla :%s" % (self.ident, self.host, self.name))
		self.topic=''
		self.regex=re.compile("\sxd$",re.M)
	def send(self, data):
		if self.debug==1:
			print(">>",data)
		data=data+'\r\n'
		data=data.encode('utf-8','ignore')
		self.connection.send(data)
	def recive(self):
		buffer=self.connection.recv(2048).decode('utf-8','ignore')
		buffer=buffer.split('\r\n')
		return buffer
	def join(self):
		self.send("JOIN %s\r\n" % self.channel)
		self.get_topic()
		print('Joined channel: %s' % self.channel)
	def message(self, data, sender):
		logfile=open('log','a')
		sender_nick=sender.split('!')[0]
		if self.debug==1:
			print('Got message: %s' % data)
			print('From: %s' % sender)
			logfile.write("<%s> %s\n"%(sender_nick, data))
		else:
			logfile.write("<%s> %s\n"%(sender_nick, data))
		iksde=re.search(self.regex, data.lower())
		if (iksde) or (data.lower()=='xd'):
			self.kick(sender_nick, 'iksde')
		if (data[0]=='!'):
			if (data=='!hello'):
				self.send_message_to_channel('hej %s' % sender_nick)
			if (data=='!op'):
				if(sender_nick in self.owners):
					self.op(sender_nick)
			if (data=='!deop'):
				if(sender_nick in self.owners):
					self.deop(sender_nick)	
			if (data.find('!temat')==0):
				if(sender_nick in self.owners):
					data=data.replace('!temat ','')
					self.set_topic(data)
			if (data.find('!dopisz')==0):
				if(sender_nick in self.owners):
					data=data.replace('!dopisz ','')
					self.get_topic()
					self.append_topic(data)
			if (data=='!opall'):
				if(sender_nick in self.owners):
					for op in self.owners:
						self.op(op)
			if (data=='!deopall'):
				if(sender_nick in self.owners):
					for op in self.owners:
						self.deop(op)
					
		logfile.close()
	def send_message_to_channel(self, data):
		self.send('PRIVMSG %s :%s' % (self.channel, data))
	def set_mode(self, who, mode):
		self.send('MODE %s %s' %(who,mode))
	def op(self,who):
		self.set_mode(self.channel, '+o %s' % who)
	def deop(self,who):
		self.set_mode(self.channel, '-o %s' % who)
	def kick(self,who,message):
		if(who!=self.nick):
			self.send('KICK %s %s %s'% (self.channel, who, message))
	def set_realserver_address(self, address):
		self.host=address
	def get_topic(self):
		self.send('TOPIC %s' % self.channel)
		buffer=self.recive()
		for line in buffer:
			if len(line)>0:
				if(':%s 332 %s %s ' % (irc.host, irc.nick, irc.channel) in line):
					line=line.split(':',2)
					self.topic=line[2]
					print('Got Topic: %s' % self.topic)
			
	def set_topic(self, topic):
		self.send('TOPIC %s :%s' % (self.channel, topic))
	def append_topic(self, topic):
		self.send('TOPIC %s :%s' % (self.channel, self.topic+' | '+topic))
buffer=''
irc=irc_connection(config.HOST, config.PORT, config.NICK, config.IDENT, config.REALNAME, config.CHANNEL, config.DEBUG, config.OWNERS)
thread_comline = threading.Thread(target=commandline, args=[])
thread_comline.start()
while 1:
	try:
		buffer=irc.recive()
		for line in buffer:
			if len(line)>0:
				line=line.rstrip()
				if(irc.debug==1):			
					print("<<", end=' ')
					for element in line:
						print(element, end="")
					print("")
		
				if(irc.address_set==0):
					irc.set_realserver_address(line.split(':')[1].split()[0])
					irc.address_set=1
					print('Connected to server: %s' % irc.host)
				if(line[:4]=='PING'):
					line=line.split()
					print('PING? PONG!')
					irc.send("PONG %s" % line[1])
				if(':%s 376 %s' % (irc.host,irc.nick) in line):
					irc.join()
					irc.set_mode(irc.nick, '+B %s' % irc.nick)
				if('PRIVMSG %s' % irc.channel in line):
					line=line.split(' PRIVMSG %s :' % irc.channel)
					sender=line[0]
					sender=sender[1:]
					irc.message(line[1] , sender)
				if('JOIN :%s' % irc.channel in line):
					line=line.split('JOIN %s' % irc.channel)
					user=line[0]
					user=user[1:].split('!')
					host=user[1].split()[0]
					user=user[0]
					if user!=irc.nick:
						print('%s has joined %s' % (user, irc.channel))
						irc.send_message_to_channel('Hej %s \o' % user)
					if('%s!%s' %(user, host) in config.SECONDARY):
						irc.op(user)
	except KeyboardInterrupt:
		irc.send('QUIT :Keyboard Interrupt')
		sys.exit(0)
