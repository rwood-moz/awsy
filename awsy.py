# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import sys
import time
import subprocess

from optparse import OptionParser


class AWSY(object):

    emu_proc = 'out/host/linux-x86/bin/emulator64-arm'
    emu_proc2 = 'out/host/linux-x86/bin/emulator-arm'

    def __init__(self):
        # Ensure $B2G_HOME is set
        try:
            self.b2g_home = os.environ["B2G_HOME"]
            print "\n$B2G_HOME points to: %s" %self.b2g_home
        except:
            print "\n$B2G_HOME env var must be set to point to the B2G folder.\n"
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
        # Ensure $B2G_DISTRO is set
        try:
            self.b2g_distro = os.environ["B2G_DISTRO"]
            print "\n$B2G_DISTRO points to: %s" %self.b2g_distro
        except:
            print "\n$B2G_DISTRO env var must be set to point to the emulator.\n"
            sys.exit(1)
        # Ensure run-emulator script exist
        if not os.path.exists("%s/run-emulator.sh" %self.b2g_distro):
            print("\nThe emulator doesn't exist at the $B2G_DISTRO location.\n")
            sys.exit(1)
        # Have output printed live in jenkins
        sys.stdout.flush()

    def backup_existing_reports(self):
        # If any about-memory reports exist, back them up
        print "\nBacking up any existing memory reports in %s" %os.getcwd()
        entire_file_list = os.listdir(os.getcwd())
        for found_file in entire_file_list:
            if found_file.startswith("about-memory"):
                try:
                    cur_time = time.strftime("%Y%m%d%H%M%S", time.localtime())
                    os.rename(found_file, "old_%s_%s" %(cur_time, found_file))
                except:
                    print "Unable to rename existing memory report: %s" %found_file
        sys.stdout.flush()

    def start_emu(self):
        # Startup the B2G emulator; location specified by $B2G_DISTRO
        print "\nStarting emulator..."
        sys.stdout.flush()
        # Want emulator to start in own process but don't want this parent to wait for it to finish
        os.system("gnome-terminal -e $B2G_DISTRO/run-emulator.sh &")
        # Sleep for emulator bootup
        sys.stdout.flush()
        os.system("adb wait-for-device")
        print "\nSleeping several minutes, to allow full emulator and gaia boot-up..."
        sys.stdout.flush()
        time.sleep(300)

        # Verify emulator is running
        returned = os.popen("adb devices").read()
        if "emulator" in returned:
            print "\nEmulator is booted and listed by adb devices"
        else:
            print "\nEmulator not found by 'adb devices'."
            sys.stdout.flush()
            sys.exit(1)

    def adb_forward(self):
        # ADB forward to the emulator
        print "\nForwarding adb port..."
        return_code = subprocess.call(["adb forward tcp:2828 tcp:2828"], shell=True)
        if return_code:
            print "\nFailed to forward adb port to the emulator."
            sys.stdout.flush()
            sys.exit(1)

    def delete_old_reports_from_emu(self):
        # Ensure there are no memory reports on the emulator (/data/local/tmp) left from a previous run
        print "\nRemoving any previous memory reports from the emulator..."
        try:
            subprocess.call(["adb shell rm -r /data/local/tmp/memory-reports"], shell=True)
        except:
            pass
        sys.stdout.flush()

    def copy_file_onto_emu(self, file_name):
        # Make sure the file has exe permissions first
        try:
            subprocess.call(["chmod 777 %s" %file_name], shell=True)
        except:
            pass

        # Copy the given file onto the emulator in /data/local
        print '\nCopying file onto the emulator: %s' %file_name
        sys.stdout.flush()
        return_code = subprocess.call(["adb push %s /data/local/%s" %(file_name, file_name)], shell=True)
        time.sleep(5)
        if return_code:
            print "\nFailed to copy file onto the emulator."
            sys.stdout.flush()
            sys.exit(1)

    def start_logcat(self):
        print ("\nStarting adb logcat...")
        sys.stdout.flush()
        os.system("gnome-terminal -e adb logcat > logcat.log &")
        time.sleep(5)

    def get_memory_report(self, dmd, cycles_done):
        # Use the get_about_memory script to grab a memory report

        # TEMP due to Bug 910847 DO NOT attempt to get DMD
        dmd = False

        # Name output folder appropriately
        if cycles_done == 0:
            folder_name = "about-memory-start-idle"
        elif cycles_done == 1:
            folder_name = "about-memory-after-%d-cycle" %cycles_done
        else:
            folder_name = "about-memory-after-%d-cycles" %cycles_done

        if dmd:
            print "\nGetting about_memory report with DMD enabled..."
            sys.stdout.flush()
            return_code = subprocess.call(["$B2G_HOME/get_about_memory.py"], shell=True)
        else:
            print "\nGetting about_memory report without DMD..."
            sys.stdout.flush()
            # Bug 961847: The --dir option doesn't work
            #cmd = ("$B2G_HOME/tools/get_about_memory.py --no-dmd --no-auto-open --no-gc-cc-log -d %s" %folder_name)
            cmd = "$B2G_HOME/tools/get_about_memory.py --no-dmd --no-auto-open --no-gc-cc-log"
            return_code = subprocess.call([cmd], shell=True)
        if return_code:
            print "\nFailed to get memory report."
            sys.stdout.flush()
            sys.exit(1)
        sys.stdout.flush()

        # Temporary because of 961847; rename the folder
        try:
            subprocess.call(["mv about-memory-0 %s"%folder_name], shell=True)
            print "\nRenamed the about-memory folder to %s" %folder_name
        except:
            print "\nFailed to rename about-memory folder"
            sys.stdout.flush()
            sys.exit(1)
        sys.stdout.flush()

    def run_test(self, orangutan_test, cur_cycle, cycles):
        # Run the test one cycle; assuming test and orng already exist on emulator in /data/local/
        print "\nRunning '%s' cycle %d of %d..." %(orangutan_test, cur_cycle, cycles)
        # Have output printed live in jenkins
        sys.stdout.flush()
        return_code = subprocess.call(["adb shell /data/local/orangutan/orng /dev/input/event0 /data/local/%s" %orangutan_test], shell=True)
        sys.stdout.flush()
        if return_code:
            print "\nFailed to run the orangutan test."
            sys.stdout.flush()
            sys.exit(1)

    def drive(self, orangutan_test, cycles, sleep, nap_every, nap_time, checkpoint_at, dmd):
        # Actually drive the tests
        for cur_cycle in range(1, cycles + 1):
            self.run_test(orangutan_test, cur_cycle, cycles)
            print "\nCycle complete, sleeping for %d seconds..." %sleep
            sys.stdout.flush()
            time.sleep(sleep)
            # Get memory report after 1 cycle, then as specified, then after done
            if ((cur_cycle % checkpoint_at) == 0) or (cur_cycle == 1) or (cur_cycle == cycles):
                self.get_memory_report(dmd, cur_cycle)
            # Nap time?
            if (cur_cycle % nap_every == 0):
                print "\nTaking extended nap for %d seconds..." %nap_time
                sys.stdout.flush()
                time.sleep(nap_time)

    def kill_emulator(self):
        # Tests are finished, kill the emulator
        print "\nKilling the emulator instance..."
        sys.stdout.flush()
        try:
            returned = os.popen("ps -Af").read()
            process_list = returned.split("\n")
            for i, s in enumerate(process_list):
                if self.emu_proc in s:
                    proc_details = process_list[i].split()
                    emu_pid = int(proc_details[1])
                    os.kill(emu_pid, 9)
                elif self.emu_proc2 in s:
                    proc_details = process_list[i].split()
                    emu_pid = int(proc_details[1])
                    os.kill(emu_pid, 9)
        except:
            # Failed to kill emulator
            print "\nCouldn't kill the emulator process."
        sys.stdout.flush()


class awsyOptionParser(OptionParser):
    def __init__(self, **kwargs):
        OptionParser.__init__(self, **kwargs)
        self.add_option('--emulator-running',
                        action='store_true',
                        dest='emu_running',
                        default=False,
                        help='Emulator is already running, connect to existing instance')
        self.add_option('--cycles',
                        action='store',
                        dest='cycles',
                        default=1,
                        metavar='int',
                        type='int',
                        help='Number of cycles to run the orangutan test script')
        self.add_option('--sleep-between',
                        action='store',
                        dest='sleep_between',
                        default=30,
                        metavar='int',
                        type='int',
                        help='Sleep for x seconds between each cycle')
        self.add_option('--nap-every',
                        action='store',
                        dest='nap_after',
                        default=10,
                        metavar='int',
                        type='int',
                        help='Take an extended nap after every x cycles')
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
                        help='Get about_memory dumps after every x cycles')
        self.add_option('--dmd',
                        action='store_true',
                        dest='dmd',
                        default=False,
                        help='Include DMD when get memory dumps')
        self.add_option('--ftu',
                        action='store_true',
                        dest='ftu',
                        default=False,
                        help='Run FTU utility on first emulator bootup')


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
    print "Cycles: %d" %options.cycles
    print "Sleep for %d seconds between cycles." %options.sleep_between
    if options.nap_after <= options.cycles:
        print "After every %d cycles take a nap for %d seconds." %(options.nap_after, options.nap_time)
    if options.checkpoint_every <= options.cycles:
        print "Get extra about_memory dumps after every %d cycles." %options.checkpoint_every
    else:
        print "About_memory dumps will be retrieved at start and at the finish."
    if options.dmd:
        print "DMD will be included in the memory dumps."
    else:
        print "DMD will NOT be included in the memory dumps."
    if options.emu_running:
        print "The emulator is already running, will connect to existing instance."
    else:
        print "The emulator is not already running so will be started."
    if options.ftu:
        print "FTU utility script will run first."
    else:
        print "NOT running the FTU utility script."

    # Flush so jenkins will display output live
    sys.stdout.flush()

    # Create our test runner
    awsy = AWSY()

    # Begin by backing up any existing about_memory reports
    awsy.backup_existing_reports()

    # Start up the emulator if it is not already running
    if not options.emu_running:
        awsy.start_emu()

    # Ensure the emulator port is fw
    awsy.adb_forward()

    # Ensure no old memory reports exist on the emulator
    awsy.delete_old_reports_from_emu()

    # Copy orangutan binary onto emulator
    awsy.copy_file_onto_emu('orangutan/orng')

    # Copy the FTU utility script onto the emulator
    if options.ftu:
        awsy.copy_file_onto_emu('tests/navigateftu.dat')

    # Copy the orangutan test script onto the emulator
    awsy.copy_file_onto_emu(test_name)

    # First time the emulator starts up there is the FTU app;
    # run utility script to navigate and close the FTU
    if options.ftu:
        awsy.run_test('tests/navigateftu.dat', 1, 1)
        time.sleep(10)

    # Start adb logcat
    awsy.start_logcat()

    # Get the starting about_memory
    awsy.get_memory_report(options.dmd, 0)

    # Actually run the test cycle(s), and get_about_memory
    # NOTE: The gaia lock screen MUST BE disabled, otherwise the emulator
    # will lock during sleeps and while getting the memory reports
    awsy.drive(test_name,
               options.cycles,
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
