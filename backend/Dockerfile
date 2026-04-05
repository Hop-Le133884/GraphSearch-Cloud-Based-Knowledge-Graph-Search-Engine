# -- Stage: base Python image
FROM python:3.12-slim

# Set working directory inside the container
WORKDIR /app

# Copy dependency list first (before the rest of the code)
COPY requirements.txt .

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the backend code
COPY . .

# Tell Docker thsi container listens on port 5000
EXPOSE 5000

# Command to run when the container starts
CMD ["python", "run.py"]