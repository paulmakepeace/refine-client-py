FROM alpine:latest
MAINTAINER felixlohmeier <felixlohmeier@opencultureconsulting.com>
# The OpenRefine Python Client Library from PaulMakepeace provides an interface to communicating with an OpenRefine server. This fork extends the CLI with some options to create new OpenRefine projects from files.
# Source: https://github.com/felixlohmeier/openrefine-client

# Install python, pip, wget, unzip and bash
RUN apk add --no-cache \
	bash \
	curl \
	grep \
	python \
	py-pip \
	wget \
	unzip

# Install dependency urllib2_file
RUN pip install urllib2_file==0.2.1

# Download and build openrefine-client-master
WORKDIR /app
RUN wget --no-check-certificate https://github.com/felixlohmeier/openrefine-client/archive/master.zip
RUN unzip master.zip && rm master.zip
RUN python openrefine-client-master/setup.py build
RUN python openrefine-client-master/setup.py install

# Change docker WORKDIR (shall be mounted)
WORKDIR /data

# Execute refine.py
ENTRYPOINT ["/app/openrefine-client-master/refine.py"]

# Default command: print help
CMD ["-h"]
