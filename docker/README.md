## batch processing with python-client

There are some client libraries for OpenRefine that communicate with the [OpenRefine API](https://github.com/OpenRefine/OpenRefine/wiki/OpenRefine-API). I have prepared a docker container on top of the [Python Library from PaulMakepeace](https://github.com/PaulMakepeace/refine-client-py/) and extended the CLI with some options to create new OpenRefine projects from files.

### basic usage

1) start server:
```docker run -d --name=openrefine felixlohmeier/openrefine```

2) start client (prints help screen):
```docker run --rm --link openrefine felixlohmeier/openrefine-client -H openrefine```

### example for customized run commands in interactive mode (e.g. for usage in terminals)

1) start server in terminal A:
```docker run --rm --name=openrefine -p 80:3333 -v /home/felix/refine:/data:z felixlohmeier/openrefine -i 0.0.0.0 -m 4G -d /data```
* automatically remove docker container when it exits
* set name "openrefine" for docker container
* publish internal port 3333 to host port 80
* mount host directory /home/felix/refine as working directory
* make openrefine available in the network
* increase java heap size to 4 GB
* set refine workspace to /data
* OpenRefine should be available at http://localhost

2) start client in terminal B (prints help screen):
```docker run --rm --link openrefine -v /home/felix/refine:/data:z felixlohmeier/openrefine-client -H openrefine```
* automatically remove docker container when it exits
* build up network connection with docker container "openrefine"
* mount host directory /home/felix/refine as working directory
* apply history in file /home/felix/refine/history.json to project with id 1234567890123

### example for customized run commands in detached mode (e.g. for usage in shell scripts)

1) define variables
* ```workingdir=/home/felix/refine```
* ```inputfile=example.csv```
* ```jsonfile=test.json```


2) start server
 ```docker run --d --name=openrefine -v ${workingdir}:/data:z felixlohmeier/openrefine -i 0.0.0.0 -m 4G -d /data```

3) create project (import file)
```docker run --rm --link openrefine -v ${workingdir}:/data:z felixlohmeier/openrefine-client -H openrefine -c $inputfile```

4) get project id
```project=($(docker run --rm --link openrefine -v ${workingdir}:/data felixlohmeier/openrefine-client -H openrefine --list | cut -c 2-14))```

5) apply transformations from json file
```docker run --rm --link -v ${workingdir}:/data felixlohmeier/openrefine-client -H openrefine -f ${jsonfile} ${project}```

6) export project to file
```docker run --rm --link openrefine -v ${workingdir}:/data felixlohmeier/openrefine-client -E --output=${project}.tsv ${project}```

7) cleanup
* ```docker stop -t=500 openrefine```
* ```docker rm openrefine```
