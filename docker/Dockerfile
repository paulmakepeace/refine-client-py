FROM alpine:latest
LABEL maintainer="felixlohmeier@opencultureconsulting.com"
# The OpenRefine client provides an interface to communicating with an OpenRefine server and supports batch processing. It is focused on the command line interface (CLI) but may also be used as a Python library.
# Source: https://github.com/opencultureconsulting/openrefine-client

# Install python, pip, unzip, curl and grep
RUN apk add --no-cache \
	python \
	py-pip \
	curl \
	grep

# Install dependency urllib2_file
RUN pip install urllib2_file==0.2.1

# Copy python scripts
WORKDIR /app
COPY refine/* ./

# Change docker WORKDIR (shall be mounted by user)
WORKDIR /data

# Execute main python script
ENTRYPOINT ["/app/__main__.py"]

# Default command: print help
CMD ["-h"]
