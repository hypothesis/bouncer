FROM alpine:3.9.4
MAINTAINER Hypothes.is Project and contributors

# Install system build and runtime dependencies.
RUN apk add --no-cache \
  ca-certificates \
  collectd \
  collectd-disk \
  curl \
  nodejs \
  nodejs-npm \
  python3 \
  supervisor

# Create the bouncer user, group, home directory and package directory.
RUN addgroup -S bouncer \
  && adduser -S -G bouncer -h /var/lib/bouncer bouncer
WORKDIR /var/lib/bouncer

# Copy packaging
COPY README.rst package.json requirements.txt ./

RUN npm install --production

RUN pip3 install --no-cache-dir -U pip \
  && pip3 install --no-cache-dir -r requirements.txt

# Copy collectd config
COPY conf/collectd.conf /etc/collectd/collectd.conf
RUN mkdir /etc/collectd/collectd.conf.d \
 && chown bouncer:bouncer /etc/collectd/collectd.conf.d

COPY . .

# Start the web server by default
EXPOSE 8000
USER bouncer
CMD ["bin/init-env", "supervisord", "-c" , "conf/supervisord.conf"]
