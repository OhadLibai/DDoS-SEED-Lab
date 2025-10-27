FROM httpd:latest

# Modern Apache server with HTTP/1.1 support
# Note: This lab demonstrates HTTP/1.1 slowloris attacks, not HTTP/2

# Enable standard modules
RUN sed -i 's/#LoadModule rewrite_module/LoadModule rewrite_module/' /usr/local/apache2/conf/httpd.conf

RUN echo '<html><body><h1>Hi from latest Apache image!</h1></body></html>' > /usr/local/apache2/htdocs/index.html

EXPOSE 80