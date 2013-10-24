AWSY (Are We Slim Yet)
======================

The purpose of the AWSY test driver is to automate the execution of B2G emulator tests, with the ultimate goal of detecting Firefox OS memory leaks. The tests themselves are based on the Orangutan (https://github.com/wlach/orangutan) testing tool. This driver will startup the B2G emulator, copy the required files onto the emulator, run the tests and grab B2G memory information using the get_about_memory B2G tool.

Installation
============

The following will guide you through the AWSY installation (Ubuntu x64).

1) B2G Emulator and Tools:

It is assumed that you already have a B2G build environment setup, with a successful build of the B2G emulator already available. Also within the standard B2G build folder is the B2G/tools folder, which contains the get_about_memory.py script.

The B2G_HOME environment variable MUST be set and exported in order for AWSY to locate the about_memory script:

        ie. B2G_HOME = /home/rwood/B2G
        export B2G_HOME

The B2G_DISTRO environment variable MUST be set and exported in order for AWSY to locate the emulator (the emulator may be downloaded and not in B2G_HOME):

        ie. B2G_DISTRO = /home/rwood/b2g-distro
        export B2G_DISTRO

2) Orangutan:

Please see the instructions on building the Orangutan binary in the readme here:

        https://github.com/wlach/orangutan

Once you have an orangutan binary, the AWSY_ORANG environment variable must be set and exported to in order for AWSY to lcoate your orangutan binary:

        ie. AWSY_ORANG = /home/rwood/awsy/orangutan
        export AWSY_ORANG

3) This test driver:

        git clone https://github.com/rwood-moz/awsy.git

B2G Emulator Build Prerequisites
================================
In order for the orangutan test(s) to be able to run on the emulator, the FTU (first time user) app must not appear on first time startup; and the emulator screen can never be locked.

Both of these requirements can be taken care of by changing some default pre-build settings.

To turn off the FTU app in the build:

        Edit the 'B2G/gaia/Makefile'

        Change the 'NOFTU?=0' (around line 60) to read 'NOFTU=1'

To ensure the lock-screen option is disabled:

        Edit 'B2G/gaia/build/settings.js'

        Set 'lockscreen.locked': false,

        Set 'lockscreen.enabled': false,

Then build the emulator as usual.

Running the Tests
=================

First ensure installation is complete and the B2G_HOME and AWSY_ORANG environment variables have been set as indicated in the installation section above.

Secondly, startup the emulator manually, and ensure the prerequistes are met as described above, and then SHUT DOWN the emulator before continuing. Ensure that no emulator instances are running before continuing.

Note: Currently DMD processing of emulator DMD memeory dumps doesn't work (Bug 910847). Therefore DMD processing will not be included (the command line option is temporarily over-ridden to ensure DMD is not included).

Third, open a terminal and start the driver. For example, to run one iteration of the 'runningAppsEmulator' test, with DMD processing turned off, do the following:

        cd awsy
        python awsy.py tests/runningAppsEmulator.dat
        
For more information on the optional command line arguments:

        python awsy.py --help

It currently takes a large amount of time for the get_about_memory tool to pull the GC/cc files off of the emulator; the driver may seem to get stuck at "Got N/N files." Since it takes so long, this has currently been disabled (using the --no-gc-cc-log option). See Bug 897301.

The resulting about-memory files will be found in the local folder where AWSY was cloned to.

