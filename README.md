AWSY (Are We Slim Yet)
======================

The purpose of the AWSY test driver is to automate the execution of B2G emulator tests, with the ultimate goal of detecting Firefox OS memory leaks. The tests themselves are based on the Orangutan (https://github.com/wlach/orangutan) testing tool. This driver will startup the B2G emulator, copy the required files onto the emulator, run the tests and grab B2G memory information using the get_about_memory B2G tool.

Installation
============

The following will guide you through the AWSY installation (Ubuntu x64).

1) B2G Emulator and Tools:

It is assumed that you already have a B2G build environment setup, with a successful build of the B2G emulator already completed. Also within the standard B2G build folder is the B2G/tools folder, which contains the get_about_memory.py script.

The following environment variable MUST be set and exported in order for AWSY to locate your emulator build and the about_memory script:

B2G_HOME = <path to your B2G build> i.e. /home/rwood/B2G

2) Orangutan:

Please see the instructions on building the Orangutan binary in the readme here:

        https://github.com/wlach/orangutan

Once you have an orangutan binary, the following environment variable must be set and exported to in order for AWSY to lcoate your orangutan binary:

AWSY_ORANG = <path to your orangutan binary> i.e. /home/rwood/awsy/orangutan

3) This test driver:

        git clone https://github.com/rwood-moz/awsy.git

B2G Emulator Prerequisites
==========================
Currently some manual setup of the B2G emulator is required, at least until these items are automated in the future, via prerences or build requirements. For now, in order for the AWSY emulator tests to run, the following B2G emulator items must be manually set:

1) The FTU (First Time Use) application must NOT appear on emulator boot-up. Just run the emulator for the first time, and manually run through the FTU app so it doesn't appear on subsequent emulator start-ups.

2) The FirefoxOS phone lock must be disabled so that the emulator/phone doesn't lock up during the sleeps between tests or when grabbing the memory information. Just go into the Settings app on the emulator and choose to disable the phone lock. Also, it is good to set the screen timeout to 'never' so that the screen display will not sleep/turn off.

3) Ensure that the volume warning has already been accepted. To do this, start the FM Radio app on the emulator; the first time this app appears there is a volume warning; click the 'continue' button and then after the radio app starts, just close the app.

Running the Tests
=================

First ensure installation is complete and the B2G_HOME and AWSY_ORANG environment variables have been set as indicated in the installation section above.

Secondly, startup the emulator manually, and ensure the prerequistes are met as described above, and then SHUT DOWN the emulator before continuing. Ensure that no emulator instances are running before continuing.

Note: Currently DMD processing of emulator DMD memeory dumps doesn't work (Bug 910847). Therefore by default DMD processing is currenlty turned OFF.

Third, open a terminal and start the driver. For example, to run one iteration of the 'runningAppsEmulator' test, with DMD processing turned off, do the following:

        cd awsy
        python awsy.py tests/runningAppsEmulator.dat
        
For more information on the optional command line arguments:

        python awsy.py --help

It currently takes a large amount of time for the get_about_memory tool to pull the GC/cc files off of the emulator; the driver may seem to get stuck at "Got N/N files." Since it takes so long, this has currently been disabled (using the --no-gc-cc-log option).

The resulting about-memory files will be found in the local folder where AWSY was cloned to.

