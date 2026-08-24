# Use the official Microsoft Playwright image as the base
# This image comes pre-installed with all OS-level dependencies for headless Chromium
FROM mcr.microsoft.com/playwright:v1.44.0-jammy

# Set working directory
WORKDIR /app

# Install Python 3.10 and pip (Jammy comes with Python 3.10)
RUN apt-get update && apt-get install -y python3 python3-pip python3-venv \
    && rm -rf /var/lib/apt/lists/*

# Create and activate a virtual environment
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install the Playwright browsers in the python environment (just to link it)
RUN playwright install chromium

# Copy the rest of the application
COPY . .

# Set environment variables for production
ENV PYTHONUNBUFFERED=1
ENV HOST=0.0.0.0
# Render dynamic port assignment fallback
ENV PORT=8000

# Expose the default port (Render will override this dynamically)
EXPOSE 8000

# Command to run the application using Gunicorn with Uvicorn workers
CMD ["sh", "-c", "gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind $HOST:$PORT --timeout 120"]
