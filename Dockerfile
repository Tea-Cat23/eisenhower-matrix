# Use an official Python image as a base
FROM python:3.11

# Set working directory
WORKDIR /app

# Install Node.js and npm
RUN apt-get update && apt-get install -y curl \
  && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
  && apt-get install -y nodejs

# Copy requirements and install Python dependencies
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && pip install -r backend/requirements.txt

# Copy the entire project into the container
COPY . .

# Install frontend dependencies
RUN npm install -g npm && npm ci

# Build the frontend
RUN npm run build

# Expose the port for FastAPI
EXPOSE 8080

# Start the backend
CMD ["python3", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8080"]