# Dockerfile for a Rust development environment

# Use a specific, slim version of the official Rust image
FROM rust:1.79-slim

# Set the working directory
WORKDIR /usr/src/app

# (Optional) If your project needed other system libraries (like OpenSSL),
# you would install them here with apt-get.
# RUN apt-get update && apt-get install -y libssl-dev pkg-config

# A command to keep the container running indefinitely for development
CMD ["tail", "-f", "/dev/null"]