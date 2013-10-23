#!/usr/bin/env python

# Requires the Beautiful Soup python module
# New mozilla-central TBPL builds are placed in a unique folder name. Find out the name of the
# latest TBPL build folder, so it can be used by mozdownload to grab the latest TBPL build.
# Note: The TBPL builds page must be available as a local HTML file and provided as cmd line argument
# Call from jenkins shell: buildloc=$(python get_latest_tbpl_loc.py <local_tbpl_builds_page.html>)

import sys
from bs4 import BeautifulSoup


def cli():
    # Ensure url has been provided
    if len(sys.argv) < 2:
        print("Missing URL argument")
        exit(1)

    local_page = sys.argv[1]

    # Parse the grabbed html to find the latest build folder
    try:
        soup = BeautifulSoup(open(local_page))
        for link in soup.find_all('a'):
            newest_build = link.get('href')
        print newest_build
    except:
        print "Failed to get latest build link"
        exit(1)

if __name__ == '__main__':
    cli()
