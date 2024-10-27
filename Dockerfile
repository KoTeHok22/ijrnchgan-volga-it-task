FROM python:latest

ADD main.py .

COPY requirements.txt .

EXPOSE 5000

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

COPY setup_db.py .

CMD ["python", "./main.py"]