FROM python:3.9-slim

# Install dependencies for SQL Anywhere
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    libaio1 \
    libncurses5 \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Download and install SQL Anywhere 17 client
# Note: In a real deployment, you would need to use official SQL Anywhere client files
# This is a placeholder - replace with actual SQL Anywhere download URL
RUN mkdir -p /opt/sqlanywhere17 && \
    cd /opt/sqlanywhere17 && \
    wget -q https://d5d4ifzl0yqka.cloudfront.net/sqlanywhere/17.0/sqla17client_linuxx64.tar.gz -O sqla_client.tar.gz && \
    tar -xzf sqla_client.tar.gz && \
    ./setup.bin -silent -nogui && \
    rm sqla_client.tar.gz

# Set SQL Anywhere environment variables
ENV SQLANY_API64=/opt/sqlanywhere17/lib64
ENV LD_LIBRARY_PATH=/opt/sqlanywhere17/lib64:$LD_LIBRARY_PATH
ENV PATH=/opt/sqlanywhere17/bin64:$PATH

# Copy application files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port
EXPOSE 8080

# Run the application
CMD gunicorn app:app
