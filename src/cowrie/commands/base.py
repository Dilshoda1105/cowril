# Copyright (c) 2009 Upi Tamminen <desaster@gmail.com>
# See the COPYRIGHT file for more information

from __future__ import absolute_import, division

import codecs
import datetime
import getopt
import random
import re
import time

from twisted.internet import error, reactor
from twisted.python import failure, log

from cowrie.core import utils
from cowrie.shell.command import HoneyPotCommand
from cowrie.shell.honeypot import HoneyPotShell

commands = {}


class command_whoami(HoneyPotCommand):

    def call(self):
        self.write('{0}\n'.format(self.protocol.user.username))


commands['/usr/bin/whoami'] = command_whoami
commands['whoami'] = command_whoami
commands['/usr/bin/users'] = command_whoami
commands['users'] = command_whoami


class command_help(HoneyPotCommand):

    def call(self):
        self.write("""GNU bash, version 4.2.37(1)-release (x86_64-pc-linux-gnu)
These shell commands are defined internally.  Type `help' to see this list.
Type `help name' to find out more about the function `name'.
Use `info bash' to find out more about the shell in general.
Use `man -k' or `info' to find out more about commands not in this list.

A star (*) next to a name means that the command is disabled.

 job_spec [&]                                                                                   history [-c] [-d offset] [n] or history -anrw [filename] or history -ps arg [arg...]
 (( expression ))                                                                               if COMMANDS; then COMMANDS; [ elif COMMANDS; then COMMANDS; ]... [ else COMMANDS; ] fi
 . filename [arguments]                                                                         jobs [-lnprs] [jobspec ...] or jobs -x command [args]
 :                                                                                              kill [-s sigspec | -n signum | -sigspec] pid | jobspec ... or kill -l [sigspec]
 [ arg... ]                                                                                     let arg [arg ...]
 [[ expression ]]                                                                               local [option] name[=value] ...
 alias [-p] [name[=value] ... ]                                                                 logout [n]
 bg [job_spec ...]                                                                              mapfile [-n count] [-O origin] [-s count] [-t] [-u fd] [-C callback] [-c quantum] [array]
 bind [-lpvsPVS] [-m keymap] [-f filename] [-q name] [-u name] [-r keyseq] [-x keyseq:shell-c>  popd [-n] [+N | -N]
 break [n]                                                                                      printf [-v var] format [arguments]
 builtin [shell-builtin [arg ...]]                                                              pushd [-n] [+N | -N | dir]
 caller [expr]                                                                                  pwd [-LP]
 case WORD in [PATTERN [| PATTERN]...) COMMANDS ;;]... esac                                     read [-ers] [-a array] [-d delim] [-i text] [-n nchars] [-N nchars] [-p prompt] [-t timeout>
 cd [-L|[-P [-e]]] [dir]                                                                        readarray [-n count] [-O origin] [-s count] [-t] [-u fd] [-C callback] [-c quantum] [array]>
 command [-pVv] command [arg ...]                                                               readonly [-aAf] [name[=value] ...] or readonly -p
 compgen [-abcdefgjksuv] [-o option]  [-A action] [-G globpat] [-W wordlist]  [-F function] [>  return [n]
 complete [-abcdefgjksuv] [-pr] [-DE] [-o option] [-A action] [-G globpat] [-W wordlist]  [-F>  select NAME [in WORDS ... ;] do COMMANDS; done
 compopt [-o|+o option] [-DE] [name ...]                                                        set [-abefhkmnptuvxBCHP] [-o option-name] [--] [arg ...]
 continue [n]                                                                                   shift [n]
 coproc [NAME] command [redirections]                                                           shopt [-pqsu] [-o] [optname ...]
 declare [-aAfFgilrtux] [-p] [name[=value] ...]                                                 source filename [arguments]
 dirs [-clpv] [+N] [-N]                                                                         suspend [-f]
 disown [-h] [-ar] [jobspec ...]                                                                test [expr]
 echo [-neE] [arg ...]                                                                          time [-p] pipeline
 enable [-a] [-dnps] [-f filename] [name ...]                                                   times
 eval [arg ...]                                                                                 trap [-lp] [[arg] signal_spec ...]
 exec [-cl] [-a name] [command [arguments ...]] [redirection ...]                               true
 exit [n]                                                                                       type [-afptP] name [name ...]
 export [-fn] [name[=value] ...] or export -p                                                   typeset [-aAfFgilrtux] [-p] name[=value] ...
 false                                                                                          ulimit [-SHacdefilmnpqrstuvx] [limit]
 fc [-e ename] [-lnr] [first] [last] or fc -s [pat=rep] [command]                               umask [-p] [-S] [mode]
 fg [job_spec]                                                                                  unalias [-a] name [name ...]
 for NAME [in WORDS ... ] ; do COMMANDS; done                                                   unset [-f] [-v] [name ...]
 for (( exp1; exp2; exp3 )); do COMMANDS; done                                                  until COMMANDS; do COMMANDS; done
 function name { COMMANDS ; } or name () { COMMANDS ; }                                         variables - Names and meanings of some shell variables
 getopts optstring name [arg]                                                                   wait [id]
 hash [-lr] [-p pathname] [-dt] [name ...]                                                      while COMMANDS; do COMMANDS; done
 help [-dms] [pattern ...]                                                                      { COMMANDS ; }\n""")  # noqa: E501


commands['help'] = command_help


class command_w(HoneyPotCommand):

    def call(self):
        self.write(' %s up %s,  1 user,  load average: 0.00, 0.00, 0.00\n' %
                   (time.strftime('%H:%M:%S'), utils.uptime(self.protocol.uptime())))
        self.write('USER     TTY      FROM              LOGIN@   IDLE   JCPU   PCPU WHAT\n')
        self.write('%-8s pts/0    %s %s    0.00s  0.00s  0.00s w\n' %
                   (self.protocol.user.username,
                    self.protocol.clientIP[:17].ljust(17),
                    time.strftime('%H:%M', time.localtime(self.protocol.logintime))))


commands['/usr/bin/w'] = command_w
commands['w'] = command_w


class command_who(HoneyPotCommand):

    def call(self):
        self.write('%-8s pts/0        %s %s (%s)\n' %
                   (self.protocol.user.username,
                    time.strftime('%Y-%m-%d', time.localtime(self.protocol.logintime)),
                    time.strftime('%H:%M', time.localtime(self.protocol.logintime)),
                    self.protocol.clientIP))


commands['/usr/bin/who'] = command_who
commands['who'] = command_who


class command_echo(HoneyPotCommand):

    def call(self):

        newline = True
        escape_decode = False

        try:
            optlist, args = getopt.getopt(self.args, "eEn")
            for opt in optlist:
                if opt[0] == '-e':
                    escape_decode = True
                elif opt[0] == '-E':
                    escape_decode = False
                elif opt[0] == '-n':
                    newline = False
        except Exception:
            args = self.args

        try:
            # replace r'\\x' with r'\x'
            string = ' '.join(args).replace(r'\\x', r'\x')

            # replace single character escape \x0 with \x00
            string = re.sub(r'(?<=\\)x([0-9a-fA-F])(?=\\|\"|\'|\s|$)', r'x0\g<1>', string)

            # if the string ends with \c escape, strip it and set newline flag to False
            if string.endswith('\\c'):
                string = string[:-2]
                newline = False

            if newline is True:
                string += '\n'

            if escape_decode:
                string = codecs.escape_decode(string)[0]
                self.writeBytes(string)
            else:
                self.write(string)

        except ValueError:
            log.msg("echo command received Python incorrect hex escape")


commands['/bin/echo'] = command_echo
commands['echo'] = command_echo


class command_printf(HoneyPotCommand):

    def call(self):
        if not len(self.args):
            self.write('printf: usage: printf [-v var] format [arguments]\n')
        else:
            if '-v' not in self.args and len(self.args) < 2:
                # replace r'\\x' with r'\x'
                s = ''.join(self.args[0]).replace('\\\\x', '\\x')

                # replace single character escape \x0 with \x00
                s = re.sub(r'(?<=\\)x([0-9a-fA-F])(?=\\|\"|\'|\s|$)', r'x0\g<1>', s)

                # strip single and double quotes
                s = s.strip('\"\'')

                # if the string ends with \c escape, strip it
                if s.endswith('\\c'):
                    s = s[:-2]

                self.write(codecs.escape_decode(s)[0])


commands['/usr/bin/printf'] = command_printf
commands['printf'] = command_printf


class command_exit(HoneyPotCommand):

    def call(self):
        stat = failure.Failure(error.ProcessDone(status=""))
        self.protocol.terminal.transport.processEnded(stat)
        return

    def exit(self):
        pass


commands['exit'] = command_exit
commands['logout'] = command_exit


class command_clear(HoneyPotCommand):

    def call(self):
        self.protocol.terminal.reset()


commands['/usr/bin/clear'] = command_clear
commands['clear'] = command_clear
commands['/usr/bin/reset'] = command_clear
commands['reset'] = command_clear


class command_hostname(HoneyPotCommand):

    def call(self):
        if len(self.args):
            if self.protocol.user.username == "root":
                self.protocol.hostname = self.args[0]
            else:
                self.write("hostname: you must be root to change the host name\n")
        else:
            self.write('{0}\n'.format(self.protocol.hostname))


commands['/bin/hostname'] = command_hostname
commands['hostname'] = command_hostname


class command_ps(HoneyPotCommand):

    def call(self):
        user = self.protocol.user.username
        args = ''
        if len(self.args):
            args = self.args[0].strip()
        _user, _pid, _cpu, _mem, _vsz, _rss, _tty, _stat, _start, _time, _command = list(range(11))
        output_array = []

        output = (
            '%s'.ljust(15 - len("USER")) % "USER",
            '%s'.ljust(8 - len("PID")) % "PID",
            '%s'.ljust(13 - len("%CPU")) % "%CPU",
            '%s'.ljust(13 - len("%MEM")) % "%MEM",
            '%s'.ljust(12 - len("VSZ")) % "VSZ",
            '%s'.ljust(12 - len("RSS")) % "RSS",
            '%s'.ljust(10 - len("TTY")) % "TTY",
            '%s'.ljust(8 - len("STAT")) % "STAT",
            '%s'.ljust(8 - len("START")) % "START",
            '%s'.ljust(8 - len("TIME")) % "TIME",
            '%s'.ljust(30 - len("COMMAND")) % "COMMAND")
        output_array.append(output)
        if (self.protocol.user.server.process):
            for single_ps in self.protocol.user.server.process:
                output = ('%s'.ljust(15 - len(str(single_ps['USER']))) % str(single_ps['USER']),
                          '%s'.ljust(8 - len(str(single_ps['PID']))) % str(single_ps['PID']),
                          '%s'.ljust(13 - len(str(round(single_ps['CPU'], 2)))) % str(round(single_ps['CPU'], 2)),
                          '%s'.ljust(13 - len(str(round(single_ps['MEM'], 2)))) % str(round(single_ps['MEM'], 2)),
                          '%s'.ljust(12 - len(str(single_ps['VSZ']))) % str(single_ps['VSZ']),
                          '%s'.ljust(12 - len(str(single_ps['RSS']))) % str(single_ps['RSS']),
                          '%s'.ljust(10 - len(str(single_ps['TTY']))) % str(single_ps['TTY']),
                          '%s'.ljust(8 - len(str(single_ps['STAT']))) % str(single_ps['STAT']),
                          '%s'.ljust(8 - len(str(single_ps['START']))) % str(single_ps['START']),
                          '%s'.ljust(8 - len(str(single_ps['TIME']))) % str(single_ps['TIME']),
                          '%s'.ljust(30 - len(str(single_ps['COMMAND']))) % str(single_ps['COMMAND']))
                output_array.append(output)
            process = random.randint(4000, 8000)
            output = ('%s'.ljust(15 - len('root')) % 'root',
                      '%s'.ljust(8 - len(str(process))) % str(process),
                      '%s'.ljust(13 - len('0.0')) % '0.0',
                      '%s'.ljust(13 - len('0.1')) % '0.1',
                      '%s'.ljust(12 - len('5416')) % '5416',
                      '%s'.ljust(12 - len('1024')) % '1024',
                      '%s'.ljust(10 - len('?')) % '?',
                      '%s'.ljust(8 - len('Ss')) % 'Ss',
                      '%s'.ljust(8 - len('June22')) % 'June22',
                      '%s'.ljust(8 - len('0:00')) % '0:00',
                      '%s'.ljust(30 - len('/usr/sbin/sshd: %s@pts/0')) % '/usr/sbin/sshd: %s@pts/0' % user)
            output_array.append(output)
            process = process + 5
            output = ('%s'.ljust(15 - len(user)) % user,
                      '%s'.ljust(8 - len(str(process))) % str(process),
                      '%s'.ljust(13 - len('0.0')) % '0.0',
                      '%s'.ljust(13 - len('0.1')) % '0.1',
                      '%s'.ljust(12 - len('2925')) % '5416',
                      '%s'.ljust(12 - len('1541')) % '1024',
                      '%s'.ljust(10 - len('pts/0')) % 'pts/0',
                      '%s'.ljust(8 - len('Ss')) % 'Ss',
                      '%s'.ljust(8 - len('06:30')) % '06:30',
                      '%s'.ljust(8 - len('0:00')) % '0:00',
                      '%s'.ljust(30 - len('bash')) % '-bash')
            output_array.append(output)
            process = process + 2
            output = ('%s'.ljust(15 - len(user)) % user,
                      '%s'.ljust(8 - len(str(process))) % str(process),
                      '%s'.ljust(13 - len('0.0')) % '0.0',
                      '%s'.ljust(13 - len('0.1')) % '0.1',
                      '%s'.ljust(12 - len('2435')) % '2435',
                      '%s'.ljust(12 - len('929')) % '929',
                      '%s'.ljust(10 - len('pts/0')) % 'pts/0',
                      '%s'.ljust(8 - len('Ss')) % 'Ss',
                      '%s'.ljust(8 - len('06:30')) % '06:30',
                      '%s'.ljust(8 - len('0:00')) % '0:00',
                      '%s'.ljust(30 - len('ps')) % 'ps %s' % ' '.join(self.args))

            output_array.append(output)
        else:
            output_array = (
                (
                    'USER      ', ' PID', ' %CPU', ' %MEM', '    VSZ', '   RSS', ' TTY      ', 'STAT ', 'START',
                    '   TIME ',
                    'COMMAND',),
                (
                    'root      ', '   1', '  0.0', '  0.1', '   2100', '   688', ' ?        ', 'Ss   ', 'Nov06',
                    '   0:07 ',
                    'init [2]  ',),
                (
                    'root      ', '   2', '  0.0', '  0.0', '      0', '     0', ' ?        ', 'S<   ', 'Nov06',
                    '   0:00 ',
                    '[kthreadd]',),
                (
                    'root      ', '   3', '  0.0', '  0.0', '      0', '     0', ' ?        ', 'S<   ', 'Nov06',
                    '   0:00 ',
                    '[migration/0]',),
                (
                    'root      ', '   4', '  0.0', '  0.0', '      0', '     0', ' ?        ', 'S<   ', 'Nov06',
                    '   0:00 ',
                    '[ksoftirqd/0]',),
                (
                    'root      ', '   5', '  0.0', '  0.0', '      0', '     0', ' ?        ', 'S<   ', 'Nov06',
                    '   0:00 ',
                    '[watchdog/0]',),
                (
                    'root      ', '   6', '  0.0', '  0.0', '      0', '     0', ' ?        ', 'S<   ', 'Nov06',
                    '   0:17 ',
                    '[events/0]',),
                (
                    'root      ', '   7', '  0.0', '  0.0', '      0', '     0', ' ?        ', 'S<   ', 'Nov06',
                    '   0:00 ',
                    '[khelper]',),
                (
                    'root      ', '  39', '  0.0', '  0.0', '      0', '     0', ' ?        ', 'S<   ', 'Nov06',
                    '   0:00 ',
                    '[kblockd/0]',),
                (
                    'root      ', '  41', '  0.0', '  0.0', '      0', '     0', ' ?        ', 'S<   ', 'Nov06',
                    '   0:00 ',
                    '[kacpid]',),
                (
                    'root      ', '  42', '  0.0', '  0.0', '      0', '     0', ' ?        ', 'S<   ', 'Nov06',
                    '   0:00 ',
                    '[kacpi_notify]',),
                (
                    'root      ', ' 170', '  0.0', '  0.0', '      0', '     0', ' ?        ', 'S<   ', 'Nov06',
                    '   0:00 ',
                    '[kseriod]',),
                (
                    'root      ', ' 207', '  0.0', '  0.0', '      0', '     0', ' ?        ', 'S    ', 'Nov06',
                    '   0:01 ',
                    '[pdflush]',),
                (
                    'root      ', ' 208', '  0.0', '  0.0', '      0', '     0', ' ?        ', 'S    ', 'Nov06',
                    '   0:00 ',
                    '[pdflush]',),
                (
                    'root      ', ' 209', '  0.0', '  0.0', '      0', '     0', ' ?        ', 'S<   ', 'Nov06',
                    '   0:00 ',
                    '[kswapd0]',),
                (
                    'root      ', ' 210', '  0.0', '  0.0', '      0', '     0', ' ?        ', 'S<   ', 'Nov06',
                    '   0:00 ',
                    '[aio/0]',),
                (
                    'root      ', ' 748', '  0.0', '  0.0', '      0', '     0', ' ?        ', 'S<   ', 'Nov06',
                    '   0:00 ',
                    '[ata/0]',),
                (
                    'root      ', ' 749', '  0.0', '  0.0', '      0', '     0', ' ?        ', 'S<   ', 'Nov06',
                    '   0:00 ',
                    '[ata_aux]',),
                (
                    'root      ', ' 929', '  0.0', '  0.0', '      0', '     0', ' ?        ', 'S<   ', 'Nov06',
                    '   0:00 ',
                    '[scsi_eh_0]',),
                (
                    'root      ', '1014', '  0.0', '  0.0', '      0', '     0', ' ?        ', 'D<   ', 'Nov06',
                    '   0:03 ',
                    '[kjournald]',),
                (
                    'root      ', '1087', '  0.0', '  0.1', '   2288', '   772', ' ?        ', 'S<s  ', 'Nov06',
                    '   0:00 ',
                    'udevd --daemon',),
                (
                    'root      ', '1553', '  0.0', '  0.0', '      0', '     0', ' ?        ', 'S<   ', 'Nov06',
                    '   0:00 ',
                    '[kpsmoused]',),
                (
                    'root      ', '2054', '  0.0', '  0.2', '  28428', '  1508', ' ?        ', 'Sl   ', 'Nov06',
                    '   0:01 ',
                    '/usr/sbin/rsyslogd -c3',),
                (
                    'root      ', '2103', '  0.0', '  0.2', '   2628', '  1196', ' tty1     ', 'Ss   ', 'Nov06',
                    '   0:00 ',
                    '/bin/login --     ',),
                (
                    'root      ', '2105', '  0.0', '  0.0', '   1764', '   504', ' tty2     ', 'Ss+  ', 'Nov06',
                    '   0:00 ',
                    '/sbin/getty 38400 tty2',),
                (
                    'root      ', '2107', '  0.0', '  0.0', '   1764', '   504', ' tty3     ', 'Ss+  ', 'Nov06',
                    '   0:00 ',
                    '/sbin/getty 38400 tty3',),
                (
                    'root      ', '2109', '  0.0', '  0.0', '   1764', '   504', ' tty4     ', 'Ss+  ', 'Nov06',
                    '   0:00 ',
                    '/sbin/getty 38400 tty4',),
                (
                    'root      ', '2110', '  0.0', '  0.0', '   1764', '   504', ' tty5     ', 'Ss+  ', 'Nov06',
                    '   0:00 ',
                    '/sbin/getty 38400 tty5',),
                (
                    'root      ', '2112', '  0.0', '  0.0', '   1764', '   508', ' tty6     ', 'Ss+  ', 'Nov06',
                    '   0:00 ',
                    '/sbin/getty 38400 tty6',),
                (
                    'root      ', '2133', '  0.0', '  0.1', '   2180', '   620', ' ?        ', 'S<s  ', 'Nov06',
                    '   0:00 ',
                    'dhclient3 -pf /var/run/dhclient.eth0.pid -lf /var/lib/dhcp3/dhclien',),
                (
                    'root      ', '4969', '  0.0', '  0.1', '   5416', '  1024', ' ?        ', 'Ss   ', 'Nov08',
                    '   0:00 ',
                    '/usr/sbin/sshd: %s@pts/0' % user,),
                ('%s'.ljust(8) % user, '5673', '  0.0', '  0.2', '   2924', '  1540', ' pts/0    ', 'Ss   ', '04:30',
                 '   0:00 ', '-bash',),
                ('%s'.ljust(8) % user, '5679', '  0.0', '  0.1', '   2432', '   928', ' pts/0    ', 'R+   ', '04:32',
                 '   0:00 ', 'ps %s' % ' '.join(self.args),)
            )

        output = output_array
        for i in range(len(output)):
            if i != 0:
                if 'a' not in args and output[i][_user].strip() != user:
                    continue
                elif 'a' not in args and 'x' not in args \
                        and output[i][_tty].strip() != 'pts/0':
                    continue
            line = [_pid, _tty, _time, _command]
            if 'a' in args or 'x' in args:
                line = [_pid, _tty, _stat, _time, _command]
            if 'u' in args:
                line = [_user, _pid, _cpu, _mem, _vsz, _rss, _tty, _stat, _start, _time, _command]
            s = ''.join([output[i][x] for x in line])
            if 'w' not in args:
                s = s[:(int(self.environ['COLUMNS']) if 'COLUMNS' in self.environ else 80)]
            self.write('{0}\n'.format(s))


commands['/bin/ps'] = command_ps
commands['ps'] = command_ps


class command_id(HoneyPotCommand):

    def call(self):
        u = self.protocol.user
        self.write('uid=%d(%s) gid=%d(%s) groups=%d(%s)\n' % (u.uid, u.username, u.gid, u.username, u.gid, u.username))


commands['/usr/bin/id'] = command_id
commands['id'] = command_id


class command_passwd(HoneyPotCommand):

    def start(self):
        self.write('Enter new UNIX password: ')
        self.protocol.password_input = True
        self.callbacks = [self.ask_again, self.finish]
        self.passwd = None

    def ask_again(self, line):
        self.passwd = line
        self.write('Retype new UNIX password: ')

    def finish(self, line):
        self.protocol.password_input = False

        if line != self.passwd or self.passwd == '*':
            self.write('Sorry, passwords do not match\n')
            self.exit()
            return

        self.write('passwd: password updated successfully\n')
        self.exit()

    def lineReceived(self, line):
        log.msg(eventid='cowrie.command.success',
                realm='passwd',
                input=line,
                format='INPUT (%(realm)s): %(input)s')
        self.password = line.strip()
        self.callbacks.pop(0)(line)


commands['/usr/bin/passwd'] = command_passwd
commands['passwd'] = command_passwd


class command_shutdown(HoneyPotCommand):

    def start(self):
        if len(self.args) and self.args[0].strip().count('--help'):
            output = (
                "Usage:     shutdown [-akrhHPfnc] [-t secs] time [warning message]",
                "-a:      use /etc/shutdown.allow ",
                "-k:      don't really shutdown, only warn. ",
                "-r:      reboot after shutdown. ",
                "-h:      halt after shutdown. ",
                "-P:      halt action is to turn off power. ",
                "-H:      halt action is to just halt. ",
                "-f:      do a 'fast' reboot (skip fsck). ",
                "-F:      Force fsck on reboot. ",
                "-n:      do not go through \"init\" but go down real fast. ",
                "-c:      cancel a running shutdown. ",
                "-t secs: delay between warning and kill signal. ",
                "** the \"time\" argument is mandatory! (try \"now\") **",
            )
            for line in output:
                self.write('{0}\n'.format(line))
            self.exit()
        elif len(self.args) > 1 and self.args[0].strip().count('-h') \
                and self.args[1].strip().count('now'):
            self.write('\n')
            self.write('Broadcast message from root@{} (pts/0) ({}):\n'.format(self.protocol.hostname, time.ctime()))
            self.write('\n')
            self.write('The system is going down for maintenance NOW!\n')
            reactor.callLater(3, self.finish)
        elif len(self.args) > 1 and self.args[0].strip().count('-r') \
                and self.args[1].strip().count('now'):
            self.write('\n')
            self.write('Broadcast message from root@{} (pts/0) ({}):\n'.format(self.protocol.hostname, time.ctime()))
            self.write('\n')
            self.write('The system is going down for reboot NOW!\n')
            reactor.callLater(3, self.finish)
        else:
            self.write("Try `shutdown --help' for more information.\n")
            self.exit()
            return

    def finish(self):
        stat = failure.Failure(error.ProcessDone(status=""))
        self.protocol.terminal.transport.processEnded(stat)
        return


commands['/sbin/shutdown'] = command_shutdown
commands['shutdown'] = command_shutdown
commands['/sbin/poweroff'] = command_shutdown
commands['poweroff'] = command_shutdown
commands['/sbin/halt'] = command_shutdown
commands['halt'] = command_shutdown


class command_reboot(HoneyPotCommand):

    def start(self):
        self.write('\n')
        self.write('Broadcast message from root@{} (pts/0) ({}):\n\n'.format(self.protocol.hostname, time.ctime()))
        self.write('The system is going down for reboot NOW!\n')
        reactor.callLater(3, self.finish)

    def finish(self):
        stat = failure.Failure(error.ProcessDone(status=""))
        self.protocol.terminal.transport.processEnded(stat)
        return


commands['/sbin/reboot'] = command_reboot
commands['reboot'] = command_reboot


class command_history(HoneyPotCommand):

    def call(self):
        try:
            if len(self.args) and self.args[0] == '-c':
                self.protocol.historyLines = []
                self.protocol.historyPosition = 0
                return
            count = 1
            for line in self.protocol.historyLines:
                self.write(' %s  %s\n' % (str(count).rjust(4), line))
                count += 1
        except Exception:
            # Non-interactive shell, do nothing
            pass


commands['history'] = command_history


class command_date(HoneyPotCommand):

    def call(self):
        time = datetime.datetime.utcnow()
        self.write('{0}\n'.format(time.strftime("%a %b %d %H:%M:%S UTC %Y")))


commands['/bin/date'] = command_date
commands['date'] = command_date


class command_yes(HoneyPotCommand):

    def start(self):
        self.y()

    def y(self):
        if len(self.args):
            self.write("{0}\n".format(' '.join(self.args, '\n')))
        else:
            self.write('y\n')
        self.scheduled = reactor.callLater(0.01, self.y)

    def handle_CTRL_C(self):
        self.scheduled.cancel()
        self.exit()


commands['/usr/bin/yes'] = command_yes
commands['yes'] = command_yes


class command_sh(HoneyPotCommand):

    def call(self):
        if len(self.args) and self.args[0].strip() == '-c':

            line = ' '.join(self.args[1:])

            # it might be sh -c 'echo "sometext"', so don't use line.strip('\'\"')
            if (line[0] == '\'' and line[-1] == '\'') or (line[0] == '"' and line[-1] == '"'):
                line = line[1:-1]

            self.execute_commands(line)

        elif self.input_data:
            self.execute_commands(self.input_data.decode('utf8'))

        # TODO: handle spawning multiple shells, support other sh flags

    def execute_commands(self, cmds):
        # self.input_data holds commands passed via PIPE
        # create new HoneyPotShell for our a new 'sh' shell
        self.protocol.cmdstack.append(HoneyPotShell(self.protocol, interactive=False))

        # call lineReceived method that indicates that we have some commands to parse
        self.protocol.cmdstack[-1].lineReceived(cmds)

        # remove the shell
        self.protocol.cmdstack.pop()


commands['/bin/bash'] = command_sh
commands['bash'] = command_sh
commands['/bin/sh'] = command_sh
commands['sh'] = command_sh


class command_chmod(HoneyPotCommand):

    def call(self):
        if len(self.args) < 2:
            self.write('chmod: missing operand\n')
            self.write('Try chmod --help for more information.\n')
            return
        for arg in self.args[1:]:
            path = self.fs.resolve_path(arg, self.protocol.cwd)
            if not self.fs.exists(path):
                self.write('chmod: cannot access {}: No such file or directory\n'.format(arg))


commands['/bin/chmod'] = command_chmod
commands['chmod'] = command_chmod


class command_php(HoneyPotCommand):

    def start(self):
        if not len(self.args):
            pass
        elif self.args[0] == '-v':
            output = (
                'PHP 5.3.5 (cli)',
                'Copyright (c) 1997-2010 The PHP Group'
            )
            for line in output:
                self.write('{0}\n'.format(line))
            self.exit()
        elif self.args[0] == '-h':
            output = (
                'Usage: php [options] [-f] <file> [--] [args...]',
                '       php [options] -r <code> [--] [args...]',
                '       php [options] [-B <begin_code>] -R <code> [-E <end_code>] [--] [args...]',
                '       php [options] [-B <begin_code>] -F <file> [-E <end_code>] [--] [args...]',
                '       php [options] -- [args...]',
                '       php [options] -a',
                '',
                '  -a               Run interactively',
                '  -c <path>|<file> Look for php.ini file in this directory',
                '  -n               No php.ini file will be used',
                "  -d foo[=bar]     Define INI entry foo with value 'bar'",
                '  -e               Generate extended information for debugger/profiler',
                '  -f <file>        Parse and execute <file>.',
                '  -h               This help',
                '  -i               PHP information',
                '  -l               Syntax check only (lint)',
                '  -m               Show compiled in modules',
                '  -r <code>        Run PHP <code> without using script tags <?..?>',
                '  -B <begin_code>  Run PHP <begin_code> before processing input lines',
                '  -R <code>        Run PHP <code> for every input line',
                '  -F <file>        Parse and execute <file> for every input line',
                '  -E <end_code>    Run PHP <end_code> after processing all input lines',
                '  -H               Hide any passed arguments from external tools.',
                '  -s               Output HTML syntax highlighted source.',
                '  -v               Version number',
                '  -w               Output source with stripped comments and whitespace.',
                '  -z <file>        Load Zend extension <file>.',
                '',
                '  args...          Arguments passed to script. Use -- args when first argument',
                '                   starts with - or script is read from stdin',
                '',
                '  --ini            Show configuration file names',
                '',
                '  --rf <name>      Show information about function <name>.',
                '  --rc <name>      Show information about class <name>.',
                '  --re <name>      Show information about extension <name>.',
                '  --ri <name>      Show configuration for extension <name>.',
                ''
            )
            for line in output:
                self.write('{0}\n'.format(line))
            self.exit()
        else:
            self.exit()

    def lineReceived(self, line):
        log.msg(eventid='cowrie.command.success',
                realm='php',
                input=line,
                format='INPUT (%(realm)s): %(input)s')

    def handle_CTRL_D(self):
        self.exit()


commands['/usr/bin/php'] = command_php
commands['php'] = command_php


class command_chattr(HoneyPotCommand):

    def call(self):
        if len(self.args) < 1:
            self.write('Usage: chattr [-RVf] [-+=AacDdeijsSu] [-v version] files...\n')
            return
        elif len(self.args) < 2:
            self.write("Must use '-v', =, - or +'\n")
            return
        if not self.fs.exists(self.args[1]):
            self.write('chattr: No such file or directory while trying to stat ' + self.args[1] + '\n')
        return


commands['/usr/bin/chattr'] = command_chattr
commands['chattr'] = command_chattr


class command_set(HoneyPotCommand):
    # Basic functionaltly (show only), need enhancements
    # This will show ALL environ vars, not only the global ones
    # With enhancements it should work like env when -o posix is used
    def call(self):
        for i in sorted(list(self.environ.keys())):
            self.write('{0}={1}\n'.format(i, self.environ[i]))


commands['set'] = command_set


class command_nop(HoneyPotCommand):

    def call(self):
        pass


commands['umask'] = command_nop
commands['unset'] = command_nop
commands['export'] = command_nop
commands['alias'] = command_nop
commands['jobs'] = command_nop
commands['/bin/kill'] = command_nop
commands['/bin/pkill'] = command_nop
commands['/bin/killall'] = command_nop
commands['/bin/killall5'] = command_nop
commands['/bin/su'] = command_nop
commands['su'] = command_nop
commands['/bin/chown'] = command_nop
commands['chown'] = command_nop
commands['/bin/chgrp'] = command_nop
commands['chgrp'] = command_nop
commands['/usr/bin/chattr'] = command_nop
commands['chattr'] = command_nop
commands[':'] = command_nop
commands['do'] = command_nop
commands['done'] = command_nop
