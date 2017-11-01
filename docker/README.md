## batch processing with python-client

There are some client libraries for OpenRefine that communicate with the [OpenRefine API](https://github.com/OpenRefine/OpenRefine/wiki/OpenRefine-API). I have prepared a docker container on top of the [Python Library from PaulMakepeace](https://github.com/PaulMakepeace/refine-client-py/) and extended the CLI with some options to create new OpenRefine projects from files.

If you are looking for a ready to use command line interface to OpenRefine for batch processing then you might be interested in the following bash shell script: [felixlohmeier/openrefine-batch](https://github.com/felixlohmeier/openrefine-batch)

### basic usage

**1) start server:**
> docker run -d --name=openrefine-server felixlohmeier/openrefine

**2) run client with one of the following commands:**

list projects:
> docker run --rm --link openrefine-server felixlohmeier/openrefine-client --list

create project from file:
> docker run --rm --link openrefine-server felixlohmeier/openrefine-client --create [FILE]

apply [rules from json file](http://kb.refinepro.com/2012/06/google-refine-json-and-my-notepad-or.html):
> docker run --rm --link openrefine-server felixlohmeier/openrefine-client --apply [FILE.json] [PROJECTID]

export project to file:
> docker run --rm --link openrefine-server felixlohmeier/openrefine-client --export [PROJECTID] --output=FILE.tsv

check help screen for more options:
> docker run --rm --link openrefine-server felixlohmeier/openrefine-client --help

**3) cleanup:**
> docker stop openrefine-server && docker rm openrefine-server

### example for customized run commands in interactive mode (e.g. for usage in terminals)

**1) start server in terminal A:**

```docker run --rm --name=openrefine-server -p 80:3333 -v /home/felix/refine:/data:z felixlohmeier/openrefine -i 0.0.0.0 -m 4G -d /data```

* automatically remove docker container when it exits
* set name "openrefine" for docker container
* publish internal port 3333 to host port 80
* mount host directory /home/felix/refine as working directory
* make openrefine available in the network
* increase java heap size to 4 GB
* set refine workspace to /data
* OpenRefine should be available at http://localhost

**2) start client in terminal B (prints help screen):**

```docker run --rm --link openrefine-server -v /home/felix/refine:/data:z felixlohmeier/openrefine-client```

* automatically remove docker container when it exits
* build up network connection with docker container "openrefine"
* mount host directory /home/felix/refine as working directory
* apply history in file /home/felix/refine/history.json to project with id 1234567890123

### example for customized run commands in detached mode (e.g. for usage in shell scripts)

**1) define variables (bring your own example data)**
> workingdir=/home/felix/refine
> inputfile=example.csv
> jsonfile=test.json

**2) start server**

 ```docker run -d --name=openrefine-server -v ${workingdir}:/data:z felixlohmeier/openrefine -i 0.0.0.0 -m 4G -d /data```

**3) wait until server is ready**

```until docker run --rm --link openrefine-server --entrypoint /usr/bin/curl felixlohmeier/openrefine-client --silent -N http://openrefine-server:3333 | cat | grep -q -o "OpenRefine" ; do sleep 1; done```

**4) create project (import file)**

```docker run --rm --link openrefine-server -v ${workingdir}:/data:z felixlohmeier/openrefine-client --create $inputfile```

**5) get project id**

```project=($(docker run --rm --link openrefine-server -v ${workingdir}:/data felixlohmeier/openrefine-client --list | cut -c 2-14))```

**6) apply transformations from json file**

```docker run --rm --link openrefine-server -v ${workingdir}:/data felixlohmeier/openrefine-client --apply ${jsonfile} ${project}```

**7) export project to file**

```docker run --rm --link openrefine-server -v ${workingdir}:/data felixlohmeier/openrefine-client --export --output=${project}.tsv ${project}```

**8) cleanup**

```docker stop -t=500 openrefine-server && docker rm openrefine-server```
