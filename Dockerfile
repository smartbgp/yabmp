FROM python:2.7.14-alpine

LABEL maintainer="lupzhu <lupzhu@cisco.com>"

RUN apk add --no-cache gcc musl-dev g++

ENV BMP_BIND_PORT=20000

ADD ./ /yabmp

WORKDIR /yabmp

RUN pip install -r requirements.txt && chmod +x bin/yabmpd && chmod +x start.sh

EXPOSE 20000

VOLUME ["~/data"]

ENTRYPOINT ["./start.sh"]
