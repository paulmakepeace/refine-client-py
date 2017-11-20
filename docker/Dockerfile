FROM alpine:latest
MAINTAINER felixlohmeier <felixlohmeier@opencultureconsulting.com>
# The OpenRefine Python Client Library from PaulMakepeace provides an interface to communicating with an OpenRefine server. This fork extends the command line interface (CLI) and supports communication between docker containers.
# Source: https://github.com/felixlohmeier/openrefine-client

# Install python, pip, unzip, curl and grep
RUN apk add --no-cache \
	python \
	py-pip \
	unzip \
	curl \
	grep

# Install dependency urllib2_file
RUN pip install urllib2_file==0.2.1

# Download and build openrefine-client-master
WORKDIR /app
RUN curl -L -o tmp.zip https://github.com/felixlohmeier/openrefine-client/archive/master.zip
RUN unzip tmp.zip && rm tmp.zip

# Change docker WORKDIR (shall be mounted by user)
WORKDIR /data

# Execute refine.py
ENTRYPOINT ["/app/openrefine-client-master/refine.py"]

# Default command: print help
CMD ["-h"]
