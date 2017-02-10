FROM gliderlabs/alpine:3.3
MAINTAINER Hypothes.is Project and contributors

# Install system build and runtime dependencies.
RUN apk add --no-cache ca-certificates python3 nodejs curl \
  && curl -sSL https://bootstrap.pypa.io/get-pip.py | python3 \
  && rm -rf /var/cache/apk/*

# Create the bouncer user, group, home directory and package directory.
RUN addgroup -S bouncer \
  && adduser -S -G bouncer -h /var/lib/bouncer bouncer
WORKDIR /var/lib/bouncer

# Copy packaging
COPY README.rst package.json requirements.txt ./

RUN npm install --production \
  && npm cache clean

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Persist the static directory.
VOLUME ["/var/lib/bouncer/bouncer/static"]

# Start the web server by default
EXPOSE 8000
USER bouncer
CMD ["gunicorn", "-b", "0.0.0.0:8000", "bouncer:app()"]
