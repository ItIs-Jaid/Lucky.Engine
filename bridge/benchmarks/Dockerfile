FROM python:3.11-slim

WORKDIR /app

# Copy required files
COPY engine.py .
COPY lucky-config.yaml .
COPY bridge_nodes.json .
COPY benchmarks/ ./benchmarks/

# Install dependencies (if any)
RUN pip install pyyaml

# Run stress test
CMD ["python", "benchmarks/stress_test.py"]
