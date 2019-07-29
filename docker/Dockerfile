FROM alpine:latest
LABEL maintainer="felixlohmeier@opencultureconsulting.com"
# The OpenRefine Python Client Library from PaulMakepeace provides an interface to communicating with an OpenRefine server. This fork extends the command line interface (CLI) and supports communication between docker containers.
# Source: https://github.com/opencultureconsulting/openrefine-client

# Install python and pip
RUN apk add --no-cache \
	python \
	py-pip

# Install dependency urllib2_file
RUN pip install urllib2_file==0.2.1

# Download and build openrefine-client-master
WORKDIR /app
COPY google google
COPY refine.py .

# Change docker WORKDIR (shall be mounted by user)
WORKDIR /data

# Execute refine.py
ENTRYPOINT ["/app/refine.py"]

# Default command: print help
CMD ["-h"]
