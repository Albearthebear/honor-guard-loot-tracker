FROM python:3.9-slim

WORKDIR /app

# Copy requirements first for better caching
COPY dragon-soul-loot/app/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY dragon-soul-loot/app/ ./app/
COPY dragon-soul-loot/static/ ./static/
COPY dragon-soul-loot/data/ ./data/
COPY dragon-soul-loot/processed_data/ ./processed_data/
COPY dragon-soul-loot/run.py ./run.py

# Set environment variables
ENV PYTHONPATH=/app
# Use PORT environment variable from Cloud Run, default to 8080 if not set
ENV PORT=8080

# Expose the port
EXPOSE ${PORT}

# Run the application with the PORT environment variable
CMD python run.py --host 0.0.0.0 --port ${PORT} --process-data 