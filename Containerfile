FROM lsiobase/alpine:3.17 as base

WORKDIR /usr/src/app

RUN \
	apk add --no-cache \
		python3 \
		py3-pip
RUN \
	python3 -m ensurepip && \
  pip3 install -U --no-cache-dir \
	  pip \
	  wheel
RUN \
  pip3 install /usr/src/app


EXPOSE 8080

ENTRYPOINT python3 -m soccerwithyourfriends
