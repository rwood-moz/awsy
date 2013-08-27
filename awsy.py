# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import sys
import time
import subprocess

from optparse import OptionParser


class AWSY(object):

    def __init__(self):
        # Ensure $B2G_HOME is set
        try:
            self.b2g_home = os.environ["B2G_HOME"]
            print "\n$B2G_HOME points to emulator location at: %s" %self.b2g_home
        except:
            print "$B2G_HOME env var must be set to point to the B2G emulator location."
            sys.exit(1)
        # Ensure run-emulator script exist
        if not os.path.exists("%s/run-emulator.sh" %self.b2g_home):
            print("The emulator doesn't exist in the specified $B2G_HOME location.")
            exit(1)
        # Ensure get_about_memory tool script exists
        if not os.path.exists("%s/tools/get_about_memory.py" %self.b2g_home):
            print("The get_about_memory.py script doesn't exist in $B2G_HOME/tools.")
            exit(1)

    def backup_existing_reports(self):
        # If any about-memory reports exist, back them up
        file_path = "%s/tools" %self.b2g_home
        print "\nSearching for existing memory reports in %s" % file_path
        entire_file_list = os.listdir(file_path)
        for found_file in entire_file_list:
            if found_file.startswith("memory-report"):
                print "\nFound existing memory-report, renaming..."
                try:
                    os.rename(file_path + "/" + found_file, file_path + "/" + "old_" + found_file)
                except:
                    print "Unable to rename existing memory report: %s" %found_file

    def start_emu(self):
        # Startup the B2G emulator; location specified by $B2G_HOME
        print "\nStarting the B2G emulator..."
        return_code = subprocess.call(["$B2G_HOME/run-emulator.sh"], shell=True)
        if return_code:
            print "\nFailed to startup the B2G emulator. Ensure $B2G_HOME points to the emulator location."
            sys.exit(1)
        time.sleep(60)

        # Verify emulator is running
        proc = 'emulator64-arm'
        returned = os.popen("ps -Af").read()
        found = returned.count(proc)
        if found == 0:
            print("\nThe B2G emulator failed to start; process not found.")   
            sys.exit(1)

        # ADB forward to the emulator
        return_code = subprocess.call(["adb forward tcp:2828 tcp:2828"], shell=True)
        if return_code:
            print "\nFailed to forward adb port to the emulator."
            sys.exit(1)

    def delete_old_reports_from_emu(self):
        # Ensure there are no memory reports on the emulator (/data/local/tmp) left from a previous run
        print "\nEnsuring there are no memory-reports on the emulator from a previous run..."
        print "\n<TO-DO> ***** just delete the /tmp/memory-reports folder from the emulator via adb shell *****"

    def copy_test_onto_emu(self, orangutan_test):
        # Copy the given test script onto the emulator in /data/local
        print '\nCopying orangutan test onto the emulator: %s' %orangutan_test
        return_code = subprocess.call(["adb push %s /data/local/%s" %(orangutan_test, orangutan_test)], shell=True)
        if return_code:
            print "\nFailed to copy orangutan test script onto the emulator."
            sys.exit(1)

    def get_memory_report(self, dmd):
        # Use the get_about_memory script to grab a memory report
        if dmd:
            print "\nGetting about_memory report with DMD enabled..."
            return_code = subprocess.call(["$B2G_HOME/get_about_memory.py"], shell=True)
        else:
            print "\nGetting about_memory report without DMD..."
            return_code = subprocess.call(["$B2G_HOME/get_about_memory.py -n"], shell=True)
        if return_code:
            print "\nFailed to get memory report."
            sys.exit(1)

    def run_test(self, orangutan_test, cur_iteration, iterations):
        # Run the test one cycle; assuming test and orng already exist on emulator in /data/local
        print "\nStarting '%s' iteration %d of %d..." %(orangutan_test, cur_iteration, iterations)
        return_code = subprocess.call(["adb shell /data/local/orng /dev/input/event0 /data/local/%s" %orangutan_test], shell=True)
        if return_code:
            print "\nFailed to run the orangutan test."
            sys.exit(1)

    def drive(self, orangutan_test, iterations, sleep, nap_every, nap_time, checkpoint_at, dmd):
        # Actually drive the tests
        for cur_iteration in range(1, iterations + 1):
            self.run_test(orangutan_test, cur_iteration, iterations)
            time.sleep(sleep)
            # TODO: CHeck for nap
            # TODO: Check for checkpoint


class awsyOptionParser(OptionParser):
    def __init__(self, **kwargs):
        OptionParser.__init__(self, **kwargs)       
        self.add_option('--iterations',
                        action='store',
                        dest='iterations',
                        default=1,
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
        exit(1)

    print "Test to run: %s" %test_name
    print "Iterations: %d" %options.iterations
    print "Sleep for %d seconds between iterations." %options.sleep_between
    print "After every %d iterations take a nap for %d seconds." %(options.nap_after, options.nap_time)
    print "Get additional about_memory dumps after every %d iterations." %options.checkpoint_every
    if options.dmd:
        print "DMD will be included in the memory dumps.\n"
    else:
        print "DMD will not be included in the memory dumps.\n"

    print "Starting in 60 seconds..."
    time.sleep(60)

    # Create our test runner and begin
    awsy = AWSY()
    awsy.backup_existing_reports()
    awsy.start_emu()
    awsy.delete_old_reports_from_emu()
    awsy.copy_test_onto_emu(test_name)
    awsy.get_memory_report(options.dmd)

    # Actually run the test cycle(s)
    awsy.drive(orangutan_test,
               options.iterations,
               options.sleep_between,
               options.nap_after,
               options.nap_time,
               options.checkpoint_every,
               options.dmd)

    # Get the final memory report
    awsy.get_memory_report()
    print "\nFinished."


if __name__ == '__main__':
    cli()
