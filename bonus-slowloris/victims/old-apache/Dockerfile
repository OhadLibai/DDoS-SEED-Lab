FROM httpd:2.2.34

# Create a simple index.html file in the default web root directory.
# This ensures the server has a page to serve for the health check.
RUN echo '<html><body><h1>Hi from old Apache server!</h1></body></html>' > /usr/local/apache2/htdocs/index.html

# The base image already listens on port 80, so no "Listen 80" is needed.
# Just expose the port.
EXPOSE 80