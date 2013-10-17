# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import sys
import time
import subprocess

from optparse import OptionParser


class AWSY(object):

    emu_proc = 'emulator64-arm'

    def __init__(self):
        # Ensure $B2G_HOME is set
        try:
            self.b2g_home = os.environ["B2G_HOME"]
            print "\n$B2G_HOME points to: %s" %self.b2g_home
        except:
            print "\n$B2G_HOME env var must be set to point to the B2G emulator.\n"
            sys.exit(1)
        # Ensure run-emulator script exist
        if not os.path.exists("%s/run-emulator.sh" %self.b2g_home):
            print("\nThe emulator doesn't exist at the $B2G_HOME location.\n")
            sys.exit(1)
        # Ensure get_about_memory tool script exists
        if not os.path.exists("%s/tools/get_about_memory.py" %self.b2g_home):
            print("\nThe get_about_memory.py script doesn't exist in $B2G_HOME/tools.\n")
            sys.exit(1)
        # Ensure $AWSY_ORANG is set
        try:
            self.awsy_orang = os.environ["AWSY_ORANG"]
            print "\n$AWSY_ORANG points to: %s" %self.awsy_orang
        except:
            print "\n$AWSY_ORANG env var must be set to point to the orangutan binary.\n"
            sys.exit(1)
        # Ensure orang binary exists
        if not os.path.exists("%s/orng" %self.awsy_orang):
            print("\nThe orangutan binary doesn't exist at the $AWSY_ORANG location.\n")
            sys.exit(1)

    def backup_existing_reports(self):
        # If any about-memory reports exist, back them up
        #file_path = "./" %self.b2g_home
        print "\nBacking up any existing memory reports in %s" %os.getcwd()
        entire_file_list = os.listdir(os.getcwd())
        for found_file in entire_file_list:
            if found_file.startswith("about-memory"):
                try:
                    cur_time = time.strftime("%Y%m%d%H%M%S", time.localtime())
                    os.rename(found_file, "old_%s_%s" %(cur_time, found_file))
                except:
                    print "Unable to rename existing memory report: %s" %found_file    

    def start_emu(self):
        # Startup the B2G emulator; location specified by $B2G_HOME
        print "\nStarting emulator and sleeping a minute..."
        # Want emulator to start in own process but don't want this parent to wait for it to finish
        os.system("gnome-terminal -e $B2G_HOME/run-emulator.sh")
        # Sleep for emulator bootup
        # <TODO> Use adb wait for device instead of a static sleep??
        time.sleep(120)

        # Verify emulator is running
        returned = os.popen("ps -Af").read()
        found = returned.count(self.emu_proc)
        if found == 0:
            print("\nThe B2G emulator failed to start; process not found.")
            sys.exit(1)

        # ADB forward to the emulator
        return_code = subprocess.call(["adb forward tcp:2828 tcp:2828"], shell=True)
        if return_code:
            print "\nFailed to forward adb port to the emulator."
            sys.exit(1)

        # **** Important note ****
        # In order for the tests to run, currently the following are prerequisites and assumed
        # are true at the time of the b2g emulator startup. Set this in the build?!
        # 1) The FTU app is DISABLED so it won't start on emulator startup
        # 2) The lock-screen is DISABLED so the emulator screen won't ever lock
        # 3) The volume warning has already been accepted (fmradio app); maybe change test to click continue

    def delete_old_reports_from_emu(self):
        # Ensure there are no memory reports on the emulator (/data/local/tmp) left from a previous run
        print "\nRemoving any previous memory reports from the emulator..."
        try:
            subprocess.call(["adb shell rm -r /data/local/tmp/memory-reports"], shell=True)
        except:
            pass

    def copy_file_onto_emu(self, file_name):
        # Make sure the file has exe permissions first
        try:
            subprocess.call(["chmod 777 %s" %file_name], shell=True)
        except:
            pass

        # Copy the given file onto the emulator in /data/local
        print '\nCopying file onto the emulator: %s' %file_name
        return_code = subprocess.call(["adb push %s /data/local/%s" %(file_name, file_name)], shell=True)
        time.sleep(5)
        if return_code:
            print "\nFailed to copy file onto the emulator."
            sys.exit(1)

    def get_memory_report(self, dmd):
        # Use the get_about_memory script to grab a memory report

        # TEMP due to Bug 910847 DO NOT attempt to get DMD
        dmd = False

        if dmd:
            print "\nGetting about_memory report with DMD enabled..."
            return_code = subprocess.call(["$B2G_HOME/get_about_memory.py"], shell=True)
        else:
            print "\nGetting about_memory report without DMD..."
            return_code = subprocess.call(["$B2G_HOME/tools/get_about_memory.py --no-dmd --no-auto-open --no-gc-cc-log"], shell=True)
        if return_code:
            print "\nFailed to get memory report."
            sys.exit(1)

    def run_test(self, orangutan_test, cur_iteration, iterations):
        # Run the test one cycle; assuming test and orng already exist on emulator in /data/local/
        print "\nRunning '%s' iteration %d of %d..." %(orangutan_test, cur_iteration, iterations)
        return_code = subprocess.call(["adb shell /data/local/orangutan/orng /dev/input/event0 /data/local/%s" %orangutan_test], shell=True)
        if return_code:
            print "\nFailed to run the orangutan test."
            sys.exit(1)

    def drive(self, orangutan_test, iterations, sleep, nap_every, nap_time, checkpoint_at, dmd):
        # Actually drive the tests
        for cur_iteration in range(1, iterations + 1):
            self.run_test(orangutan_test, cur_iteration, iterations)
            print "\nIteration complete, sleeping for %d seconds..." %sleep
            time.sleep(sleep)
            # Checkpoint time?
            if ((cur_iteration % checkpoint_at) == 0) or cur_iteration == iterations:
                self.get_memory_report(dmd)
            # Nap time?
            if (cur_iteration % nap_every == 0):
                print "\nTaking extended nap for %d seconds..." %nap_time
                time.sleep(nap_time)

    def kill_emulator(self):
        # Tests are finished, kill the emulator
        print "\nKilling the emulator instance..."
        try:
            returned = os.popen("ps -Af").read()
            process_list = returned.split("\n")
            for i, s in enumerate(process_list):
                if self.emu_proc in s:
                    proc_details = process_list[i].split()
                    emu_pid = int(proc_details[1])
                    os.kill(emu_pid, 9)
        except:
            # Failed to kill emulator
            print "\nCouldn't kill the emulator process."

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
        sys.exit(1)

    print "Test to run: %s" %test_name
    print "Iterations: %d" %options.iterations
    print "Sleep for %d seconds between iterations." %options.sleep_between
    if options.nap_after <= options.iterations:
        print "After every %d iterations take a nap for %d seconds." %(options.nap_after, options.nap_time)
    if options.checkpoint_every <= options.iterations:
        print "Get extra about_memory dumps after every %d iterations." %options.checkpoint_every
    else:
        print "About_memory dumps will be retrieved at start and at the finish."
    if options.dmd:
        print "DMD will be included in the memory dumps."
    else:
        print "DMD will NOT be included in the memory dumps."

    # Create our test runner
    awsy = AWSY()

    # Begin by backuping up any existing about_memory reports
    awsy.backup_existing_reports()

    # Start up the emulator
    awsy.start_emu()

    # Ensure no old memory reports exist on the emulator
    awsy.delete_old_reports_from_emu()

    # Copy orangutan binary onto emulator
    awsy.copy_file_onto_emu('orangutan/orng')

    # Copy the FTU utility script onto the emulator
    awsy.copy_file_onto_emu('tests/navigateftu.dat')

    # Copy the orangutan test script onto the emulator
    awsy.copy_file_onto_emu(test_name)

    # First time the emulator starts up there is the FTU app;
    # run utility script to navigate and close the FTU
    awsy.run_test('tests/navigateftu.dat', 1, 1)
    time.sleep(5)

    # Get the starting about_memory
    awsy.get_memory_report(options.dmd)

    # Actually run the test cycle(s), and get_about_memory
    awsy.drive(test_name,
               options.iterations,
               options.sleep_between,
               options.nap_after,
               options.nap_time,
               options.checkpoint_every,
               options.dmd)

    # Kill the emulator instance
    awsy.kill_emulator()
    print "\nFinished."


if __name__ == '__main__':
    cli()
