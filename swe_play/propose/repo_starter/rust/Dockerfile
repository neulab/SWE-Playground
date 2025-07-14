# Dockerfile for a Rust development environment

# Use a specific, slim version of the official Rust image
FROM rust:1.79-slim

# Do not modify, install vim
RUN apt-get update && apt-get install -y vim

# Set the working directory
WORKDIR /usr/src/app

# Do not modify it, it is used for copying the project files into the container
COPY . .

# (Optional) If your project needed other system libraries (like OpenSSL),
# you would install them here with apt-get.
# RUN apt-get update && apt-get install -y libssl-dev pkg-config

# A command to keep the container running indefinitely for development
CMD ["tail", "-f", "/dev/null"]