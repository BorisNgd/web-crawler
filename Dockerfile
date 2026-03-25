FROM python:3.12-slim

# Install Playwright/Chromium system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl wget gnupg ca-certificates \
    # Chromium runtime deps
    libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 \
    libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 \
    libxrandr2 libgbm1 libasound2 libxfixes3 libpango-1.0-0 \
    libcairo2 libx11-xcb1 libxcb-dri3-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright Chromium browser (only Chromium to minimise image size)
RUN playwright install chromium
RUN playwright install-deps chromium

# Copy application source
COPY . .

# Output directory
RUN mkdir -p /app/output

ENTRYPOINT ["python", "crawl.py"]
CMD ["--help"]
