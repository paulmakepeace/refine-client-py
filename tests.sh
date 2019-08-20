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

# defaults:
all=(3.2-java12 3.2-java11 3.2-java10 3.2-java9 3.2 3.1-java9 3.1 3.0-java9 3.0 2.8-java9 2.8 2.8-java7 2.7 2.7-java7 2.5-java7 2.5-java6 2.1-java6 2.0-java6)
main=(3.2 3.1 3.0 2.8 2.7 2.5-java6 2.1-java6 2.0-java6)
interactively=false
port="3333"

# help screen
function usage () {
    cat <<EOF
Usage: ./tests.sh [-t TAG] [-i] [-p] [-a] [-h]

Script for running tests with different OpenRefine and Java versions.
It uses docker images from https://hub.docker.com/r/felixlohmeier/openrefine.

Examples:
./tests.sh -a            # run tests on all OpenRefine versions (from 2.0 up to 3.2)
./tests.sh -t 3.2        # run tests on tag 3.2
./tests.sh -t 3.2 -i     # run tests on tag 3.2 interactively (pause before and after tests)
./tests.sh -t 3.2 -t 2.7 # run tests on tags 3.2 and 2.7

Advanced:
./tests.sh -j                # run tests on all OpenRefine versions and each with all supported Java versions (requires a lot of docker images to be downloaded!)
./tests.sh -t 3.1 -i -p 3334 # run tests on tag 3.1 interactively on port 3334

Running tests interactively (-i) allows you to examine OpenRefine GUI at http://localhost:3333.
Execute the script concurrently in another terminal on another port (-p 3334) to compare changes in the OpenRefine GUI at http://localhost:3333 and http://localhost:3334.

Available tags (java 8 if java not mentioned in tag):
EOF
    for t in ${all[*]} ; do
        echo "$t"
    done
    exit 1
}

# check input
NUMARGS=$#
if [ "$NUMARGS" -eq 0 ]; then
  usage
fi

# check system requirements
DOCKER="$(command -v docker 2> /dev/null)"
if [ -z "$DOCKER" ] ; then
    echo 1>&2 "This action requires you to have 'docker' installed and present in your PATH. You can download it for free at http://www.docker.com/"
    exit 1
fi
DOCKERINFO="$(docker info 2>/dev/null | grep 'Server Version')"
if [ -z "$DOCKERINFO" ]
then
    echo "command 'docker info' failed, trying again with sudo..."
    DOCKERINFO="$(sudo docker info 2>/dev/null | grep 'Server Version')"
    echo "OK"
    docker=(sudo docker)
    if [ -z "$DOCKERINFO" ] ; then
        echo 1>&2 "This action requires you to start the docker daemon. Try 'sudo systemctl start docker' or 'sudo start docker'. If the docker daemon is already running then maybe some security privileges are missing to run docker commands.'"
        exit 1
    fi
else
    docker=(docker)
fi
CURLINFO="$(command -v curl 2>/dev/null)"
if [ -z "$CURLINFO" ] ; then
    echo 1>&2 "This action requires you to have 'curl' installed and present in your PATH."
    exit 1
fi

# get user input
options="t:p:iajh"
while getopts $options opt; do
   case $opt in
   t )  tags+=("${OPTARG}");;
   p )  port="${OPTARG}";export OPENREFINE_PORT="$port";;
   i )  interactively=true;;
   a )  tags=("${main[*]}");;
   j )  tags=("${all[*]}");;
   h )  usage ;;
   \? ) echo 1>&2 "Unknown option: -$OPTARG"; usage; exit 1;;
   :  ) echo 1>&2 "Missing option argument for -$OPTARG"; usage; exit 1;;
   *  ) echo 1>&2 "Unimplemented option: -$OPTARG"; usage; exit 1;;
   esac
done
shift $((OPTIND - 1))

# print config
echo "Tags: ${tags[*]}"
echo "Port: $port"
echo ""

# safe cleanup handler
cleanup()
{
    echo "cleanup..."
    ${docker[*]} stop "$t"
}
trap "cleanup;exit" SIGHUP SIGINT SIGQUIT SIGTERM

# run setup.py tests for each docker tag
for t in ${tags[*]} ; do
    echo "=== Tests for $t ==="
    echo ""
    echo "Begin: $(date)"
    ${docker[*]} run -d -p "$port":3333 --rm --name "$t" felixlohmeier/openrefine:"$t"
    until curl --silent -N http://localhost:"$port" | cat | grep -q -o "Refine" ; do sleep 1; done
    echo "Refine running at http://localhost:${port}"
    if [ $interactively = true ]; then read -r -p "Press [Enter] key to start tests..."; fi
    python2 setup.py test
    if [ $interactively = true ]; then read -r -p "Press [Enter] key to stop OpenRefine..."; fi
    ${docker[*]} stop "$t"
    echo "End: $(date)"
    echo ""
done
