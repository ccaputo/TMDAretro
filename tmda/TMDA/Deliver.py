# -*- python -*-
#
# Copyright (C) 2001,2002 Jason R. Mastaler <jason@mastaler.com>
#
# This file is part of TMDA.
#
# TMDA is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.  A copy of this license should
# be included in the file COPYING.
#
# TMDA is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License
# along with TMDA; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA

"""TMDA local mail delivery."""


import fcntl
import os
import re
import signal
import socket
import stat
import time

import Defaults
import Errors
import Util


def alarm_handler(signum, frame):
    """Handle an alarm."""
    print 'Signal handler called with signal', signum
    raise IOError, "Couldn't open device!"


def lock_file(fp):
    """Do fcntl file locking."""
    fcntl.flock(fp.fileno(), fcntl.LOCK_EX)


def unlock_file(fp):
    """Do fcntl file unlocking."""
    fcntl.flock(fp.fileno(), fcntl.LOCK_UN)


class Deliver:
    def __init__(self, headers, body, delivery_option):
        """
        headers is an rfc822.Message instance.

        body is the message content from that instance.

        deliver_option is a delivery action option string returned
        from the TMDA.FilterParser instance.
        """
        self.headers = headers
        self.body = body
        self.message = str(headers) + '\n' + body
        self.option = delivery_option
        self.env_sender = os.environ.get('SENDER')
        
    def get_instructions(self):
        """Process the delivery_option string, returning a tuple
        containing the type of delivery to be performed, and the
        normalized delivery destination.  e.g,

        ('forward', 'me@new.job.com')
        """
        self.delivery_type = self.delivery_dest = None
        firstchar = self.option[0]
        lastchar = self.option[-1]
        # A program line begins with a vertical bar.
        if firstchar == '|':
            self.delivery_type = 'program'
            self.delivery_dest = self.option[1:].strip()
        # A forward line begins with an ampersand.  If the address
        # begins with a letter or number, you may leave out the
        # ampersand.
        elif firstchar == '&' or firstchar.isalnum():
            self.delivery_type = 'forward'
            self.delivery_dest = self.option
            if firstchar == '&':
                self.delivery_dest = self.delivery_dest[1:].strip()
        # An mbox line begins with a slash or tilde, and does not end
        # with a slash.
        elif (firstchar == '/' or firstchar == '~') and (lastchar != '/'):
            self.delivery_type = 'mbox'
            self.delivery_dest = self.option
            if firstchar == '~':
                self.delivery_dest = os.path.expanduser(self.delivery_dest)
        # A maildir line begins with a slash or tilde and ends with a
        # slash.
        elif (firstchar == '/' or firstchar == '~') and (lastchar == '/'):
            self.delivery_type = 'maildir'
            self.delivery_dest = self.option
            if firstchar == '~':
                self.delivery_dest = os.path.expanduser(self.delivery_dest)
        # Unknown delivery instruction.
        else:
            raise Errors.DeliveryError, \
                  'Delivery instruction "%s" is not recognized!' % self.option
        return (self.delivery_type, self.delivery_dest)

    def deliver(self):
        """Deliver the message appropriately."""
        (type, dest) = self.get_instructions()
        if type == 'program':
            self.__deliver_program(self.message, dest)
        elif type == 'forward':
            self.__deliver_forward(self.headers, self.body, dest)
        elif type == 'mbox':
            # Ensure destination path exists.
            if not os.path.exists(dest):
                raise Errors.DeliveryError, \
                      'Destination "%s" does not exist!' % dest
            # Refuse to deliver to an mbox if it's a symlink, to
            # prevent symlink attacks.
            elif os.path.islink(dest):
                raise Errors.DeliveryError, \
                      'Destination "%s" is a symlink!' % dest
            else:
                self.__deliver_mbox(self.message, dest)
        elif type == 'maildir':
            # Ensure destination path exists.
            if not os.path.exists(dest):
                raise Errors.DeliveryError, \
                      'Destination "%s" does not exist!' % dest
            else:
                self.__deliver_maildir(self.message, dest)

    def __deliver_program(self, message, program):
        """Deliver message to /bin/sh -c program."""
        Util.pipecmd(program, message)

    def __deliver_forward(self, headers, body, address):
        """Forward message to address, preserving the existing Return-Path."""
        Util.sendmail(headers, body, address, self.env_sender)
        
    def __deliver_mbox(self, message, mbox):
        """Reliably deliver a mail message into an mboxrd-format mbox file.

        See <URL:http://www.qmail.org/man/man5/mbox.html>
        
        Based on code from getmail
        <URL:http://www.qcc.sk.ca/~charlesc/software/getmail-2.0/>
        Copyright (C) 2001 Charles Cazabon, and licensed under the GNU
        General Public License version 2.
        """
        # Construct a UUCP-style From_ line, e.g:
        # From johndoe@nightshade.la.mastaler.com Thu Feb 28 20:16:35 2002
        #
        ufline = 'From %s %s\n' % (self.env_sender,
                                   time.asctime(time.gmtime(time.time())))
        try:
	    # When orig_length is None, we haven't opened the file yet.
            orig_length = None
            # Open the mbox file.
            fp = open(mbox, 'rb+')
            lock_file(fp)
            status_old = os.fstat(fp.fileno())
            # Check if it _is_ an mbox file; mbox files must start
            # with "From " in their first line, or are 0-length files.
            fp.seek(0, 0)                # seek to start
            first_line = fp.readline()
            if first_line != '' and first_line[:5] != 'From ':
                # Not an mbox file; abort here.
                unlock_file(fp)
                fp.close()
                raise Errors.DeliveryError, \
                      'Destination "%s" is not an mbox file!' % mbox
            fp.seek(0, 2)                # seek to end
            orig_length = fp.tell()      # save original length
            fp.write(ufline)

            # Replace lines beginning with "From ", ">From ", ">>From ", ...
            # with ">From ", ">>From ", ">>>From ", ...
            escapefrom = re.compile(r'^(?P<gts>\>*)From ', re.MULTILINE)
            msg = escapefrom.sub('>\g<gts>From ', message)
            # Add a trailing newline if last line incomplete.
            if msg[-1] != '\n':
                msg = msg + '\n'

            # Write the message.
            fp.write(msg)
            # Add a trailing blank line.
            fp.write('\n')
            fp.flush()
            os.fsync(fp.fileno())
            # Unlock and close the file.
            status_new = os.fstat(fp.fileno())
            unlock_file(fp)
            fp.close()
            # Reset atime.
            os.utime(mbox, (status_old[stat.ST_ATIME], status_new[stat.ST_MTIME]))
        except IOError, txt:
            try:
                if not fp.closed and not orig_length is None:
		    # If the file was opened and we know how long it was,
		    # try to truncate it back to that length.
                    fp.truncate(orig_length)
                unlock_file(fp)
                fp.close()
            except:
                pass
            raise Errors.DeliveryError, \
                  'Failure writing message to mbox file "%s" (%s)' % (mbox, txt)

    def __deliver_maildir(self, message, maildir):
        """Reliably deliver a mail message into a Maildir.

        See <URL:http://www.qmail.org/man/man5/maildir.html>

        Based on code from getmail
        <URL:http://www.qcc.sk.ca/~charlesc/software/getmail-2.0/>
        Copyright (C) 2001 Charles Cazabon, and licensed under the GNU
        General Public License version 2.
        """
        # e.g, 1014754642.51195.aguirre.la.mastaler.com
        filename = '%s.%s.%s' % (int(time.time()), Defaults.PID,
                                 socket.gethostname())
        # Set a 24-hour alarm for this delivery.
        signal.signal(signal.SIGALRM, alarm_handler)
        signal.alarm(24 * 60 * 60)

        dir_tmp = os.path.join(maildir, 'tmp')
        dir_new = os.path.join(maildir, 'new')
        if not (os.path.isdir(dir_tmp) and os.path.isdir(dir_new)):
            raise Errors.DeliveryError, 'not a Maildir! (%s)' % maildir

        fname_tmp = os.path.join(dir_tmp, filename)
        fname_new = os.path.join(dir_new, filename)

        # File must not already exist.
        if os.path.exists(fname_tmp):
            raise Errors.DeliveryError, fname_tmp + 'already exists!'
        if os.path.exists(fname_new):
            raise Errors.DeliveryError, fname_new + 'already exists!'

        # Get user & group of maildir.
        s_maildir = os.stat(maildir)
        maildir_owner = s_maildir[stat.ST_UID]
        maildir_group = s_maildir[stat.ST_GID]

        # Open file to write.
        try:
            fp = open(fname_tmp, 'wb')
            try:
                os.chown(fname_tmp, maildir_owner, maildir_group)
            except OSError:
                # Not running as root, can't chown file.
                pass
            os.chmod(fname_tmp, 0600)
            fp.write(message)
            fp.flush()
            os.fsync(fp.fileno())
            fp.close()
        except IOError:
            raise Errors.DeliveryError, 'Failure writing file ' + fname_tmp

        # Move message file from Maildir/tmp to Maildir/new
        try:
            os.link(fname_tmp, fname_new)
            os.unlink(fname_tmp)
        except OSError:
            try:
                os.unlink(fname_tmp)
            except:
                pass
            raise Errors.DeliveryError, 'failure renaming "%s" to "%s"' \
                   % (fname_tmp, fname_new)

        # Cancel the alarm.
        signal.alarm(0)
        signal.signal(signal.SIGALRM, signal.SIG_DFL)