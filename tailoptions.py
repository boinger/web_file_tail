#!/usr/bin/env python3
"""
Produces an Javascript map (named tail_arr by default)

Author: https://github.com/boinger/ / jeff@jeffvier.com
Produced while working for Vendita (https://vendita.com/)

"""

import datetime
import os
import sys
import logging as log


class Main:
    """Return back a Javascript-consumable map

    Variables:
        js_map_name {str} -- what map/array name is the js lib expecting to see?
                If used as intended, the returned code will be directly executed
                in the browser.
        logpath_file {str} -- static (for now) path of logfile to tail
    """

    js_map_name = 'tail_arr'  # what is the js lib expecting to see?
    logpath_file = os.path.dirname(os.path.realpath(__file__)) + '/logpaths.txt'

    log.basicConfig(stream=sys.stderr, level=log.ERROR)  # ERROR, INFO, or DEBUG

    def __init__(self, environ, start_response):
        self.environ = environ
        self.start = start_response

    @staticmethod
    def js_mapify(mapname, pydict):
        """convert a dict to a js map

        Arguments:
            mapname {str} -- map name
            dict {dict} -- dict to mapify

        Returns:
            string: a Javascript map
        """
        return mapname + ' = ' + str(pydict)

    def list_options(self):
        """Lists the options for consumption by Javascript

        """
        path_dict = {}
        try:
            with open(self.logpath_file) as file:
                for line in file:
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
                    path_dict[key] = val
        except (FileNotFoundError, PermissionError) as err:
            log.error('logpaths.txt error: %s', err)

        return self.js_mapify(self.js_map_name, path_dict)


def application(environ, response):
    """
    Required for WSGI functionality
    """
    # pylint: disable-msg=unused-variable
    status = '200 OK'
    app = Main(environ, response)
    output = bytes(app.list_options(), encoding='utf-8')

    response_headers = [('Content-type', 'text/plain'),
                        ('Content-Length', str(len(output)))]
    response(status, response_headers)

    return [output]
