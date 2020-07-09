#!/usr/bin/env python

__author__ = "Ruben Espino with help from Chris Warren"

import errno
import os
import argparse
from datetime import datetime as dt
import logging.handlers
import logging
import time
import signal


logger = logging.getLogger(__name__)
files = {}
exit_flag = False

def watch_dir(args):
    """
    Look at the directory you're watching
    Get list of files
    Add files to files dictionary if they aren't in it
    Log a message if you're adding something to dictionary that's not already there, log as new file
    Look through files dictionary and compare that to the list of files in the dictionary
    If file is not in your dictionary anymore you have to log that you removed the file from dictionary
    """
    logger.info('Watching directory: {}, File Extension: {}, Polling Interval: {}, Magic Text: {}'.format(
        args.path, args.ext, args.interval, args.magic
    ))
    file_list = os.listdir(args.path)
    for file in file_list:
        if file.endswith(args.ext) and file not in files:
            files[file] = 0
            logger.info(f"{file} added to watchlist.")
    for file in list(files):
        if file not in file_list:
            logger.info(f"{file} removed from watchlist.")
            del files[file]
    for file in files:
        files[file] = find_magic(
            os.path.join(args.path, file),
            files[files],
            args.magic
        )

def find_magic(filename, starting_line, magic_word):
    """
    Iterate through dictionary and open up each file at the last line that you read from to see if there's
    anymore "magic" text
    Update the last position you read from in the dictionary
    Key will be the filenames and the values will be the starting line you used and the last position
    you read from
    """
    line_number = 0
    with open(filename) as file:
        for line_number, line in enumerate(file):
            if line_number >= starting_line:
                if magic_word in line:
                    logger.info(
                        f"this file: {filename} found: {magic_word} on line: {line_number + 1}"
                    )
    return line_number + 1

def signal_handler(sig_num, frame):
    """
    This is a SIGTERM and SIGNIT handler. Other signals can be mapped here as well
    Sets a global flag, and main() will exit it's loop if the signal is trapped
    :param sig_num: The integer signal number that was trapped from the OS
    :param frame: Not used
    :return None
    """
    # Logs associated signal name (New way)
    signames = dict((k, v) for v, k in reversed(sorted(signal.__dict__.items()))
                    if v.startswith('SIG') and not v.startswith('SIG_'))
    logger.warning('Received ' + signames[sig_num])
    global exit_flag
    exit_flag = True
    
def create_parser():
    """Adds parser arguments"""
    parser = argparse.ArgumentParser()
    parser.add_argument('-e', '--ext', type=str, default='.txt',
                        help='Text file extension to watch')
    parser.add_argument('-i', '--interval', type=float, default=1.0,
                        help='Number of seconds between polling')
    parser.add_argument('path', help='Directory path to watch')
    parser.add_argument('magic', help='String to watch for')
    return parser

def main():
    """Runs the main func"""
    logging.basicConfig(
        format='%(asctime)s.%(msecs)03d %(name)-12s %(levelname)-8s %(message)s',
        datefmt='%M-%D-%Y & %H:%M:%S'
    )
    logger.setLevel(logging.DEBUG)
    app_start_time = dt.now()
    logger.info(
        '\n'
        '-------------------------------------------------\n'
        '   Running {0}\n'
        '   Started on {1}\n'
        '-------------------------------------------------\n'
        .format(__file__, app_start_time.isoformat())
    )
    parser = create_parser()
    args = parser.parse_args()
    
    # Connect these two signals from the OS
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    # signal_handler will get called if OS sends either of these
    
    while not exit_flag:
        try:
            # Call to watch_dir func
            watch_dir(args)
        except OSError as error:
            # Unhandled exception
            # Log an Error level message here
            if error.errno == errno.ENOENT:
                logger.error(f"{args.path} directory not found")
                time.sleep(2)
            else:
                logger.error(error)
        except Exception as error:
            logger.error(f"UNHANDLED EXCEPTION: {error}")
            
            # Sleeps while loop so cpu usage isn't at 100%
        time.sleep(int(float(args.interval)))
    
    # Final exit point
    # Logs a message that program is shutting down
    # Overall uptime since program start
    uptime = dt.now() - app_start_time
    logger.info(
        '\n'
        '-------------------------------------------------\n'
        '   Stopped {}\n'
        '   Uptime was {}\n'
        '-------------------------------------------------\n'
        .format(__file__, str(uptime))
    )
    logging.shutdown()
    
    
if __name__ == '__main__':
    main()
