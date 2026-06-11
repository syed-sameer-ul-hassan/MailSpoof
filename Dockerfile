FROM python:3.11-alpine

WORKDIR /app
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN pip install --no-cache-dir .

ENTRYPOINT ["mailspoof"]
CMD ["-h"]
