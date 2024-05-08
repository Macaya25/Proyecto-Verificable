# Use an official Python runtime as an image
FROM python:3.12-alpine


EXPOSE 5000

WORKDIR /app

# Install any needed packages specified in requirements.txt
COPY requirements.txt /app
RUN pip install -r requirements.txt

COPY app.py entrypoint.sh /app/
# Grant executable permissions to the entrypoint script
RUN chmod +x /app/entrypoint.sh

# Run the entrypoint script using shell explicitly
ENTRYPOINT ["/bin/sh", "/app/entrypoint.sh"]
