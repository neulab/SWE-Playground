# Dockerfile for a Conda-based development environment

# Use an official Miniconda3 image as the base.
# Using conda/miniconda3 is the modern, officially supported image.
FROM conda/miniconda3:latest

# Do not modify, install vim
RUN apt-get update && apt-get install -y vim

# Set the working directory inside the container.
WORKDIR /usr/src/app

# Do not modify it, used for copying the project files into the container
COPY . .

# Do not modify it, used for avoiding solving issues
RUN conda update conda

# Create the Conda environment from the .yml file.
# This installs all specified packages into an environment named 'dev-env'.
RUN conda env create -f environment.yml

# Clean up Conda caches to reduce image size.
RUN conda clean -afy

# Make bash the default shell and ensure our Conda env is activated on login.
# This is the magic that makes the container feel like a native dev environment.
SHELL ["/bin/bash", "--login", "-c"]
RUN echo "conda activate dev-env" >> ~/.bashrc

# A command to keep the container alive.
CMD ["tail", "-f", "/dev/null"]