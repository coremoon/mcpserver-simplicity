FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy server code
COPY server.py .

# Make server executable
RUN chmod +x server.py

# pysimplicityhl will be installed via requirements.txt

# The server runs on stdio, so we'll use it as entrypoint
ENTRYPOINT ["python", "server.py"]
