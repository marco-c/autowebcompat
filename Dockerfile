FROM python:3.7-buster

RUN mkdir /autowebcompat
WORKDIR /autowebcompat

ADD pip.conf Pipfile Pipfile.lock ./
ENV PYTHONUNBUFFERED=yes PIP_CONFIG_FILE=/autowebcompat/pip.conf
RUN pip install pipenv \
 && pipenv install --system --deploy --ignore-pipfile \
 && pip uninstall --yes pipenv

ADD . ./

ENV PYTHONUNBUFFERED=yes
ENV PYTHONPATH "${PYTHONPATH}:/autowebcompat"
