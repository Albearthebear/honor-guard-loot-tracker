FROM python:3.9-slim

WORKDIR /app

# Copy requirements first for better caching
COPY dragon-soul-loot/app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY dragon-soul-loot/app/ ./app/
COPY dragon-soul-loot/static/ ./static/
COPY dragon-soul-loot/data/ ./data/
COPY dragon-soul-loot/processed_data/ ./processed_data/
COPY dragon-soul-loot/run.py .

# Set environment variables
ENV PYTHONPATH=/app
ENV PORT=8000

# Expose the port
EXPOSE 8000

# Run the application
CMD ["python", "run.py", "--host", "0.0.0.0", "--port", "8000", "--process-data"] 