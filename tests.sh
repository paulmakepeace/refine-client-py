#!/bin/bash
# Script for running tests with different OpenRefine and Java versions based on Docker images.

# Copyright (c) 2011 Paul Makepeace, Real Programmers. All rights reserved.

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

# check system requirements
DOCKER="$(which docker 2> /dev/null)"
if [ -z "$DOCKER" ] ; then
    echo 1>&2 "This action requires you to have 'docker' installed and present in your PATH. You can download it for free at http://www.docker.com/"
    exit 1
fi
DOCKERINFO="$(docker info 2>/dev/null | grep 'Server Version')"
if [ -z "$DOCKERINFO" ] ; then
    echo 1>&2 "This action requires you to start the docker daemon. Try 'sudo systemctl start docker' or 'sudo start docker'. If the docker daemon is already running then maybe some security privileges are missing to run docker commands. Try to run the script with 'sudo ./openrefine-batch-docker.sh ...'"
    exit 1
fi
CURLINFO="$(which curl 2>/dev/null)"
if [ -z "$CURLINFO" ] ; then
    echo 1>&2 "This action requires you to have 'curl' installed and present in your PATH."
    exit 1
fi

# defaults:
tags=(3.2-java12 3.2-java11 3.2-java10 3.2-java9 3.2 3.1-java9 3.1 3.1-java7 3.0-java9 3.0 2.8-java9 2.8 2.8-java7 2.7 2.7-java7 2.5-java7 2.5-java6 2.1-java6 2.0-java6)
pause=false

# help screen
function usage () {
    cat <<EOF
Usage: sudo ./tests.sh [-t TAG] [-a] [-p] [-h]

Script for running tests with different OpenRefine and Java versions.
It uses docker images from https://hub.docker.com/r/felixlohmeier/openrefine.

Examples:
sudo ./tests.sh -t 3.2 # run tests with docker tag 3.2
sudo ./tests.sh -a # run all tests (requires a lot of downloads!)
sudo ./tests.sh -p # pause before and after tests (to examine OpenRefine GUI manually)
sudo ./tests.sh -h # this help screen

Available tags (java 8 if java not mentioned in tag):
EOF
    for t in ${tags[*]} ; do
        echo "$t"
    done
    exit 1
}

# check input
NUMARGS=$#
if [ "$NUMARGS" -eq 0 ]; then
  usage
fi

# get user input
options="at:ph"
while getopts $options opt; do
   case $opt in
   a )  ;;
   t )  tags=(${OPTARG}) ;;
   p )  pause=true ;;
   h )  usage ;;
   \? ) echo 1>&2 "Unknown option: -$OPTARG"; usage; exit 1;;
   :  ) echo 1>&2 "Missing option argument for -$OPTARG"; usage; exit 1;;
   *  ) echo 1>&2 "Unimplemented option: -$OPTARG"; usage; exit 1;;
   esac
done
shift $((OPTIND - 1))

# print config
echo "Tags: ${tags[*]}"
echo ""

# run setup.py tests for each docker tag
for t in ${tags[*]} ; do
    echo "=== Tests for $t ==="
    echo ""
    echo "Begin: $(date)"
    sudo docker run -d -p 3333:3333 --rm --name $t felixlohmeier/openrefine:$t
    until curl --silent -N http://localhost:3333 | cat | grep -q -o "Refine" ; do sleep 1; done
    if [ $pause = true ]; then read -p "Press [Enter] key to start tests..."; fi
    python setup.py test
    if [ $pause = true ]; then read -p "Press [Enter] key to stop OpenRefine..."; fi
    sudo docker stop $t
    echo "End: $(date)"
    echo ""
done
