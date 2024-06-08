FROM registry.suse.com/bci/python:3.11

RUN zypper --non-interactive ar -G https://download.opensuse.org/repositories/multimedia:/libs/15.5/multimedia:libs.repo \
	&& zypper --non-interactive ar -G http://download.opensuse.org/distribution/leap/15.5/repo/oss/ repo-sle \
	&& zypper --non-interactive ar -G http://download.opensuse.org/update/leap/15.5/sle/ repo-update-sle \
	&& zypper --non-interactive ref

RUN zypper --non-interactive in -y libSDL2-2_0-0 ffmpeg-7 \
	&& zypper rr doo-multimedia-libs \
	&& rm -rf /var/cache/zypp*/

# Copy requirements
COPY requirements.txt ./requirements.txt
COPY CHECKSUMS.sha256sum /usr/src/whisper-packages.sha256sum

# Install.
# Note: passing both --requirement AND the wheel dir, if one misses a
# requirement when updating, it'll break the build.

# TODO(josegomezr): when hashes are added to the requirements.txt, add here: --require-hashes
RUN --mount=source=./dependencies/,type=bind,destination=/usr/src/py311-dependencies/,readonly=true pip3 install --no-index --no-deps --requirement requirements.txt /usr/src/py311-dependencies/*

WORKDIR /work
RUN --mount=source=./medium-model/,type=bind,destination=/pool/,readonly=true cp -r /pool/ ./model/
COPY run-model.py ./
COPY entry-point.sh /work/entry-point.sh

ENTRYPOINT /work/entry-point.sh $@
