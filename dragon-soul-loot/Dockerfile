FROM python:3.9-slim

WORKDIR /app

# Copy requirements first for better caching
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY app/ ./app/
COPY static/ ./static/
COPY data/ ./data/
COPY processed_data/ ./processed_data/
COPY run.py .

# Set environment variables
ENV PYTHONPATH=/app
ENV PORT=8000

# Expose the port
EXPOSE 8000

# Run the application
CMD ["python", "run.py", "--host", "0.0.0.0", "--port", "8000", "--process-data"] 