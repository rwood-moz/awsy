# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import sys
import time

from optparse import OptionParser


class AWSY(object):

    def __init__(self, marionette):
        pass


class awsyOptionParser(OptionParser):
    def __init__(self, **kwargs):
        OptionParser.__init__(self, **kwargs)       
        self.add_option('--iterations',
                        action='store',
                        dest='iterations',
                        default=10,
                        metavar='int',
                        type='int',
                        help='Number of iterations to run the orangutan test script')
        self.add_option('--sleep-between',
                        action='store',
                        dest='sleep_between',
                        default=30,
                        metavar='int',
                        type='int',
                        help='Sleep for x seconds between each iteration')
        self.add_option('--nap-every',
                        action='store',
                        dest='nap_after',
                        default=10,
                        metavar='int',
                        type='int',
                        help='Take an extended nap after every x iterations')
        self.add_option('--nap-time',
                        action='store',
                        dest='nap_time',
                        default=180,
                        metavar='int',
                        type='int',
                        help='Nap time in seconds')
        self.add_option('--get-mem-every',
                        action='store',
                        dest='checkpoint_every',
                        default=10,
                        metavar='int',
                        type='int',
                        help='Get about_memory dumps after every x iterations')
        self.add_option('--dmd',
                        action='store_true',
                        dest='dmd',
                        default=False,
                        help='Include DMD when get memory dumps')


def cli():
    print "\nAWSY B2G Emulator Test Runner\n"
    parser = awsyOptionParser(usage='%prog test_name [options]')
    options, args = parser.parse_args()

    # Ensure have test name on command line
    if len(args) == 0:
        parser.print_help()
        print "\nError: You must specify the test name as a command line argument.\n"
        parser.exit()

    # Ensure test file exists
    test_name = args[0]
    if not os.path.exists(test_name):
        print("Error: The specified test '%s' does not exist.\n" %test_name)
        exit()

    print "Test to run: %s" %test_name
    print "Iterations: %d" %options.iterations
    print "Sleep for %d seconds between iterations." %options.sleep_between
    print "After every %d iterations take a nap for %d seconds." %(options.nap_after, options.nap_time)
    print "Grab the about_memory dumps after every %d iterations." %options.checkpoint_every
    if options.dmd:
        print "DMD will be included in the memory dumps.\n"
    else:
        print "DMD will not be included in the memory dumps.\n"

    print "Starting test in 60 seconds..."
    time.sleep(60)

    # Begin

if __name__ == '__main__':
    cli()
