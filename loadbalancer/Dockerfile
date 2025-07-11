FROM python:3.10-slim

WORKDIR /app

COPY . .

RUN pip install flask requests

CMD ["python", "load_balancer.py"]
