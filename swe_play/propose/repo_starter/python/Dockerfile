# Dockerfile for a Conda-based development environment

# 1. Use an official Miniconda3 image as the base.
# Using conda/miniconda3 is the modern, officially supported image.
FROM conda/miniconda3:latest

# 2. Set the working directory inside the container.
WORKDIR /usr/src/app

# 3. Copy the environment file into the container.
COPY environment.yml .

# 4. Create the Conda environment from the .yml file.
# This installs all specified packages into an environment named 'dev-env'.
RUN conda env create -f environment.yml

# 5. Clean up Conda caches to reduce image size.
RUN conda clean -afy

# 6. Make bash the default shell and ensure our Conda env is activated on login.
# This is the magic that makes the container feel like a native dev environment.
SHELL ["/bin/bash", "--login", "-c"]
RUN echo "conda activate dev-env" >> ~/.bashrc

# 7. A command to keep the container alive.
CMD ["tail", "-f", "/dev/null"]