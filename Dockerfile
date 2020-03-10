FROM python:3.6.9-alpine3.10
MAINTAINER Hypothes.is Project and contributors

# Install system build and runtime dependencies.
RUN apk add --no-cache \
  curl \
  nodejs \
  nodejs-npm \
  supervisor

# Create the bouncer user, group, home directory and package directory.
RUN addgroup -S bouncer \
  && adduser -S -G bouncer -h /var/lib/bouncer bouncer
WORKDIR /var/lib/bouncer

# Copy packaging
COPY README.md package.json requirements.txt ./

RUN npm install --production

RUN pip3 install --no-cache-dir -U pip \
  && pip3 install --no-cache-dir -r requirements.txt

COPY . .

# Start the web server by default
EXPOSE 8000
USER bouncer
CMD ["bin/init-env", "supervisord", "-c" , "conf/supervisord.conf"]
