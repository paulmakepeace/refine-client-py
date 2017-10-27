FROM alpine:latest
MAINTAINER felixlohmeier <felixlohmeier@opencultureconsulting.com>
# The OpenRefine Python Client Library from PaulMakepeace provides an interface to communicating with an OpenRefine server. This fork extends the CLI with some options to create new OpenRefine projects from files.
# Source: https://github.com/felixlohmeier/openrefine-client

# Install python, wget, unzip, curl and grep
RUN apk add --no-cache \
	python \
	wget \
	unzip \
	curl \
    grep

# Download and build openrefine-client-master
WORKDIR /app
RUN wget --no-check-certificate https://github.com/felixlohmeier/openrefine-client/archive/master.zip
RUN unzip master.zip && rm master.zip

# Change docker WORKDIR (shall be mounted)
WORKDIR /data

# Execute refine.py
RUN chmod +x /app/openrefine-client-master/refine.py
ENTRYPOINT ["/app/openrefine-client-master/refine.py"]

# Default command: print help
CMD ["-h"]
