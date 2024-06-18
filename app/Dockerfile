# Use an official Python runtime as an image
FROM python:3.12-alpine


EXPOSE 5000

WORKDIR /app

# Install any needed packages specified in requirements.txt
COPY requirements.txt /app
RUN pip install -r requirements.txt

COPY main.py entrypoint.sh /app/

ENV FLASK_APP=main.py
ENV FLASK_ENV=development

ENTRYPOINT ["/bin/sh", "/app/entrypoint.sh"]
