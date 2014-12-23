#!/usr/bin/env python
"""
    Very basic Python IRC Bot
    Has flaws. Beware!
    Copyright (c) Liam Stanley 2014
    License: https://liamstanley.io/basic-irc-bot.git
"""
import socket
import os
import sys
import time
import thread
import re
 
config = {
    'nick':      'TestBot',
    'user':      'TestBot',
    'network':   'irc.esper.net',
    'port':      6667,
    'channels':  ['#derp', '#herp'],
    'prefix':    '.'
}
 
# Notes, do join stuff on 001
 
class IRCClient(object):
    def __init__(self, config):
        self.user = config['user']
        self.nick = config['nick']
        self.realname = 'Python IRC Bot'
        self.prefix = config['prefix']
        self.server = config['network']
        self.port = int(config['port'])
        self.channels = list(config['channels'])
        self.connected = False
        self.irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.exec_buffer = []
        self.output_padding = 12
 
    def connect(self):
        """ Function that makes the connection to IRC and sets up the catching of data """
        # Point the socket to the IRC server and connect
        self.irc.connect((self.server, self.port))
        # Setup basic details that the IRC server needs to keep the connection
        self.send('NICK %s' % self.nick)
        self.send('USER %s %s bot :%s' % (self.user, self.nick, self.realname))
        self.output('STATUS', 'Bot starting up...')
        thread.start_new_thread(self.catch_data, ())
        while True:
            if self.exec_buffer:
                #try:
                self.exec_buffer[0]['function'](*self.exec_buffer[0]['args'])
                #except:
                #    self.exec_buffer.pop()
                #    continue
                self.exec_buffer.pop()
 
    def catch_data(self):
        """ Gets data from IRC and buffers it """
        while True:
            buf = self.irc.recv(4096)
            lines = buf.split('\n')
            for data in lines:
                data = str(data).strip()
 
                if len(data) < 2:
                    continue
 
                # server ping/pong? "PING :FFFFFFFF1155571C"
                if data.startswith('PING'):
                    self.send('PONG :' + data.split(':')[1])
                    if self.connected == False:
                        self.connected = True
 
                if len(data.split()) < 2:
                    continue
 
                try:
                    if len(data.split()) >= 4:
                        line = data.split()
                        sender = line[0][1::].split('!',1)[0] # :FM1337!Allen@staff.bouncer.ml
                        location = line[2] # Can be channel or user
                        text = ' '.join(line[3::])[1::] # Remove the first : then re-join the text
                        func = getattr(self, 'trigger_%s' % data.split()[1])
                        self.exec_buffer.append({'function': func, 'args': [data, sender, location, text]})
                    else:
                        func = getattr(self, 'trigger_%s' % data.split()[1])
                        self.exec_buffer.append({'function': func, 'args': [data]})
                except AttributeError:
                    continue
                except:
                    continue
 
    def trigger_NOTICE(self, data, sender, location, text):
        self.output('NOTICE', text)
 
    def trigger_PRIVMSG(self, data, sender, location, text):
        self.output(location, text, sender)
 
        try:
            tmp = list(re.findall(r'(?i)^\%s([a-zA-Z]+)(?: +(.*))?$' % self.prefix, text)[0])
        except IndexError:
            return
 
        if len(tmp[1]) < 1:
            args = []
        else:
            args = tmp[1].split()
 
        command = tmp[0].lower()
        try:
            self.commands(location, sender, command, args, text)
        except:
            self.output('ERROR', 'Error parsing users input (%s)' % data)
 
    def trigger_001(self, data, sender, location, text):
        self.output('NOTICE', text)
        self.perform()
 
    def output(self, name, message, user=None):
        """ Print pretty formatted data to console """
        padding = self.output_padding - len(name) - 2
        if str(padding).startswith('-'):
            padding = 1
        if user:
            message = '(%s) %s' % (user, message)
        print '%s [%s] | %s' % (padding * ' ', name, message)
 
    def send(self, data):
        """ Send raw data back to the IRC socket """
        self.irc.send(data + '\r\n')
 
    def msg(self, location, message):
        """ Send a message to a specific location """
        self.send("PRIVMSG %s :%s" % (location, message))
        self.output(location, message, self.nick)
 
    def perform(self):
        """
            Does basic stuff after connected to the server.
            Joining channels, auth here if needed, etc
        """
        for channel in self.channels:
            self.send('JOIN %s' % channel)
            self.output('INFO', 'Attempting to join channel %s' % channel)
 
    def commands(self, channel, user, command, arg, text):
        """
            Command stuff is done here
            Keep in mind, the prefix is stripped from the "command" variable already
 
            Variable info:
                channel = where it's from. Could /also/ be a username
                user = The person that triggered the command!
                arg = a list() of arguments, IF ANY
                text = the whole entire line, if needed
        """
 
        if command == 'herp': # Basic
            return self.msg(channel, 'Herpderptrains!')
 
        if command == 'derp': # Using args
            if args:
                return self.msg(channel, 'Herp' + arg[0] + 'trains')
            else:
                return self.msg(channel, 'Herp' + user + 'trains!')
 
if __name__ == '__main__':
    bot = IRCClient(config)
    try:
        bot.connect()
    except KeyboardInterrupt:
        print '\nClosing bot...'
        bot.irc.close()
        sys.exit(0)
