# Dockerfile for a C++ development environment

# Use the official GCC image as a base. Version 13 is a modern choice.
# This image is based on Debian, so it still uses apt-get.
FROM gcc:13

# Prevent apt-get from asking interactive questions during the build
ENV DEBIAN_FRONTEND=noninteractive

# Install essential C++ build tools, need modification
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    gdb \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory inside the container
WORKDIR /usr/src/app

# A command to keep the container running indefinitely for development
CMD ["tail", "-f", "/dev/null"]