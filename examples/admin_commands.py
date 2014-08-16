#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    Slixmpp: The Slick XMPP Library
    Copyright (C) 2010  Nathanael C. Fritz
    This file is part of Slixmpp.

    See the file LICENSE for copying permission.
"""

import logging
import getpass
from optparse import OptionParser

import slixmpp


class AdminCommands(slixmpp.ClientXMPP):

    """
    A simple Slixmpp bot that uses admin commands to
    add a new user to a server.
    """

    def __init__(self, jid, password, command):
        slixmpp.ClientXMPP.__init__(self, jid, password)

        self.command = command

        self.add_event_handler("session_start", self.start)

    def start(self, event):
        """
        Process the session_start event.

        Typical actions for the session_start event are
        requesting the roster and broadcasting an initial
        presence stanza.

        Arguments:
            event -- An empty dictionary. The session_start
                     event does not provide any additional
                     data.
        """
        self.send_presence()
        self.get_roster()

        def command_success(iq, session):
            print('Command completed')
            if iq['command']['form']:
                for var, field in iq['command']['form']['fields'].items():
                    print('%s: %s' % (var, field['value']))
            if iq['command']['notes']:
                print('Command Notes:')
                for note in iq['command']['notes']:
                    print('%s: %s' % note)
            self.disconnect()

        def command_error(iq, session):
            print('Error completing command')
            print('%s: %s' % (iq['error']['condition'],
                              iq['error']['text']))
            self['xep_0050'].terminate_command(session)
            self.disconnect()

        def process_form(iq, session):
            form = iq['command']['form']
            answers = {}
            for var, field in form['fields'].items():
                if var != 'FORM_TYPE':
                    if field['type'] == 'boolean':
                        answers[var] = input('%s (y/n): ' % field['label'])
                        if answers[var].lower() in ('1', 'true', 'y', 'yes'):
                            answers[var] = '1'
                        else:
                            answers[var] = '0'
                    else:
                        answers[var] = input('%s: ' % field['label'])
                else:
                    answers['FORM_TYPE'] = field['value']
            form['type'] = 'submit'
            form['values'] = answers

            session['next'] = command_success
            session['payload'] = form

            self['xep_0050'].complete_command(session)

        session = {'next': process_form,
                   'error': command_error}

        command = self.command.replace('-', '_')
        handler = getattr(self['xep_0133'], command, None)

        if handler:
            handler(session={
                'next': process_form,
                'error': command_error
            })
        else:
            print('Invalid command name: %s' % self.command)
            self.disconnect()


if __name__ == '__main__':
    # Setup the command line arguments.
    optp = OptionParser()

    # Output verbosity options.
    optp.add_option('-q', '--quiet', help='set logging to ERROR',
                    action='store_const', dest='loglevel',
                    const=logging.ERROR, default=logging.INFO)
    optp.add_option('-d', '--debug', help='set logging to DEBUG',
                    action='store_const', dest='loglevel',
                    const=logging.DEBUG, default=logging.INFO)
    optp.add_option('-v', '--verbose', help='set logging to COMM',
                    action='store_const', dest='loglevel',
                    const=5, default=logging.INFO)

    # JID and password options.
    optp.add_option("-j", "--jid", dest="jid",
                    help="JID to use")
    optp.add_option("-p", "--password", dest="password",
                    help="password to use")
    optp.add_option("-c", "--command", dest="command",
                    help="admin command to use")

    opts, args = optp.parse_args()

    # Setup logging.
    logging.basicConfig(level=opts.loglevel,
                        format='%(levelname)-8s %(message)s')

    if opts.jid is None:
        opts.jid = input("Username: ")
    if opts.password is None:
        opts.password = getpass.getpass("Password: ")
    if opts.command is None:
        opts.command = input("Admin command: ")

    # Setup the CommandBot and register plugins. Note that while plugins may
    # have interdependencies, the order in which you register them does
    # not matter.
    xmpp = AdminCommands(opts.jid, opts.password, opts.command)
    xmpp.register_plugin('xep_0133') # Service Administration

    # If you are working with an OpenFire server, you may need
    # to adjust the SSL version used:
    # xmpp.ssl_version = ssl.PROTOCOL_SSLv3

    # If you want to verify the SSL certificates offered by a server:
    # xmpp.ca_certs = "path/to/ca/cert"

    # Connect to the XMPP server and start processing XMPP stanzas.
    xmpp.connect()
    xmpp.process()
