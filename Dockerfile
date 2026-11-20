FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg curl && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY transmissor.py .
EXPOSE 8080
CMD ["python", "-u", "transmissor.py"]
