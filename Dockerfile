FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY api/ api/
COPY bot/ bot/
COPY utils/ utils/
COPY README.md .

CMD ["python", "-m", "bot.main"]
