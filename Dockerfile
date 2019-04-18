FROM python:3.7-buster

RUN mkdir /autowebcompat
WORKDIR /autowebcompat

ADD Pipfile Pipfile.lock ./
RUN pip install pipenv
RUN pipenv install --system --deploy --ignore-pipfile

ADD . ./

ENV PYTHONPATH "${PYTHONPATH}:/autowebcompat"
