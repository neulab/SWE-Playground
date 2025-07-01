# Dockerfile for a Node.js development environment

# Use a specific LTS version of the official Node.js image
FROM node:20-alpine

# Set the working directory inside the container
WORKDIR /usr/src/app

# Copy package.json (and package-lock.json if available) into the container
COPY package*.json ./

# Install dependencies
RUN npm install

# Create a non-root user for development
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nodejs -u 1001

# Change ownership of the app directory to the nodejs user
RUN chown -R nodejs:nodejs /usr/src/app
USER nodejs

# A command to keep the container running indefinitely for development
CMD ["tail", "-f", "/dev/null"] 