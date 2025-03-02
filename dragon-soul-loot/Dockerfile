FROM python:3.9-slim

WORKDIR /app

# Copy requirements first for better caching
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY app/ ./app/
COPY static/ ./static/
COPY data/ ./data/
COPY processed_data/ ./processed_data/
COPY run.py .

# Set environment variables
ENV PYTHONPATH=/app
ENV PORT=8080

# Expose the port that Cloud Run will use
EXPOSE ${PORT}

# Run the application using run.py
CMD python run.py --host 0.0.0.0 --port ${PORT} --process-data 