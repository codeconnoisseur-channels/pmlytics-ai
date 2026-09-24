FROM python:3.11-slim

WORKDIR /app

# Pinned commit: 704b3ce1e3bac0c21c46b9a850abefd1acf33da2
COPY mocks/zendesk/upstream /app/upstream
COPY mocks/zendesk/compat_handler.py /app/compat_handler.py
COPY mocks/zendesk/server.py /app/server.py

ENV PYTHONPATH=/app:/app/upstream
ENV MOCK_ZENDESK_USERNAME=mock@pocket.test
ENV MOCK_ZENDESK_API_KEY=mock-zendesk-token-pocket
ENV MOCK_ZENDESK_PORT=8080

EXPOSE 8080

CMD ["python", "-m", "server"]
