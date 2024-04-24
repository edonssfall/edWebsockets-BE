FROM python:3.11.5

WORKDIR /app

COPY . .

RUN pip install --upgrade pip  &&\
    pip install -r requirements.txt