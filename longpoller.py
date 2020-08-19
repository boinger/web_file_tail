"""
Python 3 re-implementation of LongPoller.php

Author: https://github.com/boinger/ / jeff@jeffvier.com
Produced while working for Vendita (https://vendita.com)

"""

import datetime
import os
import subprocess
import sys
import time
import json
import urllib.parse
import logging as log

class Main:
    """Display stuff

    Variables:
        safety_max {int} -- seconds. safety fallback timeout.  should be longer than ajax timeout
        logfile {str} -- static (for now) path of logfile to tail
        wc {str} -- command path
        sudo {str} -- command path
        tail {str} -- command path
        cut {str} -- command path
        tr {str} -- command path
    """

    safety_max = 50 ## seconds. It should be shorter than the ajax timeout to be handled more gracefully.
    logpath_file = os.path.dirname(os.path.realpath(__file__)) + '/logpaths.txt'
    initial_tail = '25'
    log.basicConfig(stream=sys.stderr, level=log.ERROR) ## ERROR, INFO, or DEBUG

    pather = {}
    with open(logpath_file) as f:
        for line in f:
            (key, val) = line.split()
            if '#DAY#' in val:
                val = val.replace('#DAY#', datetime.datetime.now().strftime('%a'))
            pather[key] = val

    wc = '/usr/bin/wc'
    sudo = '/usr/bin/sudo'
    tail = '/usr/bin/tail'
    cut = '/usr/bin/cut'
    tr = '/usr/bin/tr'
    stat = '/usr/bin/stat'

    def __init__(self, environ, start_response):
        self.environ = environ
        self.start = start_response

    def file_path(self, fakename='thiswontwork'):
        """Translates codenames to log file paths

        Keyword Arguments:
            fakename {str} -- codename that probably came in via POST (default: {'thiswontwork'})

        Returns:
            {str} -- a path to a filename (or to /dev/null if you guessed wrong)
        """
        file_path = self.pather.get(fakename, '/dev/null')
        log.info('Tailing: %s', file_path)
        return file_path

    def tail_file(self):
        """do the actual file tailing

        Uses POST vars:
        tailfile (str): path to file to tail (this is admittedly EXTREMELY DANGEROUS RIGHT NOW)
                            XXX this needs to be converted to a dict case thing to limit the options
        num (int): line to start at

        Returns:
            [str] -- latest log lines
        """

        http_post_data = urllib.parse.parse_qs(self.environ['wsgi.input'].read().decode('utf8'))
        num = int(http_post_data.get('num', [0])[0])
        file_name = self.file_path(http_post_data.get('tailfile', [None])[0])

        if num:
            log.debug('Requested starting line is %s', str(num))
            nextline = num + 1
            time.sleep(2)
            curr_len = int(self._get_file_line_count(file_name))
            log.debug('File length is %s.', curr_len)
            if curr_len == num:
                log.debug('Requested start line is same as file length. Waiting for file change...')
                mtime_cmd = '%s %s -c %%Y %s' % (self.sudo, self.stat, file_name)
                file_mtime = self._shell_exec(mtime_cmd)
                current_file_mtime = file_mtime
                safety = 0
                while (current_file_mtime == file_mtime and safety < self.safety_max):
                    log.debug('File mtime is %s.', current_file_mtime.strip())
                    log.debug('Safety iteration %d.', safety)
                    time.sleep(1)
                    current_file_mtime = self._shell_exec(mtime_cmd)
                    safety += 1

                if safety >= self.safety_max:
                    ret_dict = {'filename' : file_name, 'count' : -1}
                    return json.dumps(ret_dict)

            return self._get_last_log_lines_from_pos(file_name, '+' + str(nextline))

        return self._get_last_log_lines_from_pos(file_name, self.initial_tail)


    def _get_file_line_count(self, file_name):
        line_count_cmd = '%s %s -l %s | %s -d \" \" -f 1 | %s -d \'\n\' 2>/dev/null' \
            % (self.sudo, self.wc, file_name, self.cut, self.tr)
        line_count = self._shell_exec(line_count_cmd)
        log.debug('Counted %s lines.', line_count)

        if int(line_count) == 0:
            time.sleep(1) ## rest a second if the file is empty

        return line_count

    def _get_last_log_lines_from_pos(self, file_name, from_where):

        cmd = "%s %s -n %s %s" % (self.sudo, self.tail, from_where, file_name)
        logfile_lines = self._shell_exec(cmd)
        file_len = self._get_file_line_count(file_name)
        log.debug('Received %s log lines starting at line %s.', str(file_len), str(from_where))

        if int(file_len) == 0:
            time.sleep(1) ## rest a second if the file is empty
            logfile_lines_arr = list('')
        else:
            logfile_lines_arr = list(map(str.strip, logfile_lines.splitlines()))

        log.info('Returning filename: %s; count: %s; loglines (len): %d', \
                file_name, file_len, len(logfile_lines_arr))
        ret_dict = {'filename' : file_name, 'count' : file_len, 'loglines' : logfile_lines_arr}
        return json.dumps(ret_dict)

    @staticmethod
    def _shell_exec(command):
        """Executes a specified command in a shell and returns stdout

        Args:
            command (string): The full path of the script to execute
                or the name of the command in the PATH

        Returns:
            string: stdout
        """

        log.debug('Executing: %s', repr(command))
        try:
            output = subprocess.check_output(command, \
                     shell=True, \
                     ).decode('utf-8')

        except OSError as oserr:
            log.error("OS error")
            log.error(oserr)
            return oserr
        except subprocess.CalledProcessError as ex:
            log.error("CalledProcessError caught")
            log.error(ex)
            return ex
        except BaseException as ex:
            log.error("Exception caught")
            log.error(ex)
            return ex
        if output:
            return output

        return ''

def application(environ, response):
    """
    Required for WSGI functionality
    """
    # pylint: disable-msg=unused-variable
    status = '200 OK'
    app = Main(environ, response)
    output = bytes(app.tail_file(), encoding='utf-8')

    response_headers = [('Content-type', 'text/plain'),
                        ('Content-Length', str(len(output)))]
    response(status, response_headers)

    return [output]
