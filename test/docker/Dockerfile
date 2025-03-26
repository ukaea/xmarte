FROM python:3.9-slim

ENV PYTHONDONTWRITEBYTECODE 1

ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get install -y \
    software-properties-common mkdocs libgl1-mesa-glx libxcb-xinerama0 binutils gnupg \
    build-essential cmake git nano wget bc libxml2 libxml2-dev libncurses-dev libreadline6-dev \
    dos2unix && rm -rf /var/lib/apt/lists/*

RUN mkdir /root/Projects

COPY ./test/docker/marte.sh /root/Projects/marte.sh

RUN dos2unix /root/Projects/marte.sh

RUN chmod a+x /root/Projects/marte.sh

WORKDIR /root/Projects

RUN git clone https://vcis-gitlab.f4e.europa.eu/aneto/MARTe2.git MARTe2-dev -b v1.9.2

RUN git clone https://vcis-gitlab.f4e.europa.eu/aneto/MARTe2-components.git -b v1.8.0

RUN git clone http://gitlab.edward-jones.co.uk:8181/iaea-examples/marte2-extra-components.git

ENV MARTe2_DIR=/root/Projects/MARTe2-dev

ENV MARTe2_Components_DIR=/root/Projects/MARTe2-components

ENV MARTe2_EXTRA_Components_DIR=/root/Projects/marte2-extra-components

RUN cd MARTe2-dev && make -f Makefile.x86-linux core CFLAGS="-fPIC -Wall -std=c++98 -Werror -Wno-invalid-offsetof -Wno-unused-variable -fno-strict-aliasing -Wno-uninitialized"

RUN cd MARTe2-components && make -f Makefile.x86-linux core

RUN cd marte2-extra-components && make -f Makefile.x86-linux

WORKDIR /

RUN mkdir /app

COPY ./xmarte/ /app/xmarte/

COPY pyproject.toml /app/

COPY README.md /app/

WORKDIR /app/

RUN pip install ./ coverage pylint pytest-cov pylint-gitlab sphinx sphinx_rtd_theme breathe

WORKDIR /

RUN rm -rf /app/

ENV QT_QPA_PLATFORM=offscreen DISPLAY=99.0

ENV PYTHONPATH=/xmarte:$PYTHONPATH
