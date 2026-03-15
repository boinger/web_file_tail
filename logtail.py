#!/usr/bin/env python3

"""
Command-line interaction script for web_file_tail (mainly to simplify sudo needs)

Author: https://github.com/boinger/ / jeff@jeffvier.com
Produced while working for Vendita (https://vendita.com)

"""

import os
import subprocess
import sys
import logging as log
import argparse

log.basicConfig(stream=sys.stderr, level=log.ERROR)  # ERROR, INFO, or DEBUG

WC = '/usr/bin/wc'
TAIL = '/usr/bin/tail'
STAT = '/usr/bin/stat'

VERSION = '0.0.1'


def init_argparse() -> argparse.ArgumentParser:
    """Parse args"""
    parser = argparse.ArgumentParser(
        usage="%(prog)s [OPTION] [FILE]",
        description="Basic log file interactions.",
    )
    parser.add_argument("-n", "--num",
                        type=str, default='10',
                        help="starting line")
    parser.add_argument("--func",
                        type=str, default='tail',
                        choices=['linecount', 'mtime', 'isreadable', 'tail'],
                        required=True,
                        help="function requested")
    parser.add_argument("file", nargs="?")
    parser.add_argument("-v", "--version", action="version", version=f"{parser.prog} v" + VERSION)
    return parser


def isreadable(file):
    """check if file is readable
    """
    log.debug('Beginning isreadable()')
    if os.path.exists(file) and not os.path.isdir(file):
        with open(file, "r") as fp:
            return fp.readable()
    return False


def mtime(file):
    """get file mtime
    """
    # pylint: disable-msg=unused-variable
    log.debug('Beginning mtime()')
    if isreadable(file):
        output = shell_exec([STAT, '-c', '%Y', file])
        log.debug('shell_exec() returned: %s', output)
        return output
    log.error('File not readable')
    return False


def linecount(file):
    """get file line count
    """
    log.debug('Beginning linecount()')
    if isreadable(file):
        output = shell_exec([WC, '-l', file])
        line_count = output.split()[0] if output else '0'
        log.debug('Counted %s lines.', line_count)
        return line_count
    log.error('File not readable')
    return False


def tail(file, from_where):
    """tail file from indicated line number

    Returns:
        [list] -- log lines
    """
    # pylint: disable-msg=unused-variable

    log.debug('Beginning tail()')
    if isreadable(file):
        log.debug('File is readable')
        logfile_lines = shell_exec([TAIL, '-n', from_where, file])

        return logfile_lines
    log.error('File not readable')
    return False


def shell_exec(command):
    """Executes a specified command and returns stdout

    Args:
        command (list): Command and arguments as a list

    Returns:
        string: stdout
    """

    log.debug('Executing: %s', repr(command))
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
    # log.debug('Output: %s', output) ## this creates a mess
    if output:
        return output

    return ''


def main() -> None:
    """do the thing
    Returns:
        output from called func()
    """
    parser = init_argparse()
    args = parser.parse_args()
    file = args.file
    func = globals()[args.func]
    num = args.num
    try:
        if args.func == 'tail':
            print(func(file, num))
            sys.exit()
        print(func(file))
        sys.exit()
    except (FileNotFoundError, IsADirectoryError) as err:
        print(f"{parser.prog}: {file}: {err.strerror}", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
    sys.exit(99)
