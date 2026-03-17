FROM python:3.11-slim

WORKDIR /app

# pyaudio 編譯所需：portaudio 音訊庫 + C 編譯工具鏈
RUN apt-get update && \
    apt-get install -y --no-install-recommends portaudio19-dev gcc libc6-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# unbuffered stdout for interactive mode
ENV PYTHONUNBUFFERED=1

CMD ["python", "main.py"]
