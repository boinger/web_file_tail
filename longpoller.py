#!/usr/bin/env python3
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
        logtail_py {str} -- path to logtail handler (so that we only have to give sudo
                perms for this one command)
        logpath_file {str} -- text file full of k:v pairs like "codeword: /full/log/path/to/filename.log"
        initial_tail {int} -- default tail length
        safety_max {int} -- seconds. safety fallback timeout.  should be longer than ajax timeout
        sudo {str} -- command path
    """

    safety_max = 50  # seconds. It should be shorter than the ajax timeout.
    logpath_file = os.path.dirname(os.path.realpath(__file__)) + '/logpaths.txt'
    initial_tail = '25'
    sudo = '/usr/bin/sudo'
    logtail_py = '/usr/local/sbin/logtail.py'  # this should of course point to the path where you put this script.

    log.basicConfig(stream=sys.stderr, level=log.ERROR)  # ERROR, INFO, or DEBUG

    def __init__(self, environ, start_response):
        self.environ = environ
        self.start = start_response
        self.pather = self._load_logpaths()

    def _load_logpaths(self):
        """Parse logpaths.txt, substituting #DAY# with current weekday.

        Returns:
            dict: codename -> file path mapping
        """
        paths = {}
        try:
            with open(self.logpath_file) as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    parts = line.split()
                    if len(parts) != 2:
                        log.warning('Skipping malformed logpaths line: %s', line)
                        continue
                    key, val = parts
                    if '#DAY#' in val:
                        val = val.replace('#DAY#', datetime.datetime.now().strftime('%a'))
                    paths[key] = val
        except FileNotFoundError:
            log.error('logpaths.txt not found: %s', self.logpath_file)
        except PermissionError:
            log.error('logpaths.txt not readable: %s', self.logpath_file)
        return paths

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
                mtime_cmd = [self.logtail_py, '--func', 'mtime', file_name]
                file_mtime = self._sudo_exec(mtime_cmd)
                current_file_mtime = file_mtime
                safety = 0
                while current_file_mtime == file_mtime and safety < self.safety_max:
                    log.debug('File mtime is %s.', current_file_mtime.strip())
                    log.debug('Safety iteration %d.', safety)
                    time.sleep(1)
                    current_file_mtime = self._sudo_exec(mtime_cmd)
                    safety += 1

                if safety >= self.safety_max:
                    ret_dict = {'filename': file_name, 'count': -1}
                    return json.dumps(ret_dict)

            return self._get_last_log_lines_from_pos(file_name, '+' + str(nextline))

        return self._get_last_log_lines_from_pos(file_name, self.initial_tail)

    def _get_file_line_count(self, file_name):
        cmd = [self.logtail_py, '--func', 'linecount', file_name]
        line_count = self._sudo_exec(cmd)
        log.debug('Counted %s lines.', line_count)
        return line_count

    def _get_last_log_lines_from_pos(self, file_name, from_where):
        cmd = [self.logtail_py, '--func', 'tail', '--num', str(from_where), file_name]
        logfile_lines = self._sudo_exec(cmd)
        logfile_lines_arr = list(map(str.strip, logfile_lines.splitlines()))
        file_len = self._get_file_line_count(file_name)

        if int(len(logfile_lines_arr)) == 0:
            time.sleep(1)  # rest a second if the file is empty

        log.info('Returning filename: %s; count: %s; loglines (len): %d',
                 file_name, file_len, len(logfile_lines_arr))
        ret_dict = {'filename': file_name, 'count': file_len, 'loglines': logfile_lines_arr}
        return json.dumps(ret_dict)

    def _sudo_exec(self, command):
        """Executes a specified command via sudo and returns stdout

        Args:
            command (list): Command and arguments as a list

        Returns:
            string: stdout
        """

        log.debug('SUDO Executing: %s', repr(command))
        command = [self.sudo] + command
        try:
            output = subprocess.check_output(command).decode('utf-8').strip()

        except OSError as oserr:
            log.error("OS error")
            log.error(oserr)
            return str(oserr)
        except subprocess.CalledProcessError as ex:
            log.error("CalledProcessError caught")
            log.error(ex)
            return str(ex)
        except BaseException as ex:
            log.error("Exception caught")
            log.error(ex)
            return str(ex)
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
