FROM python:3.8-slim

WORKDIR /app

COPY . ./

RUN pip3 install -r req.txt --no-cache-dir

EXPOSE 8000

CMD ["gunicorn", "foodgram.wsgi:application", "--bind", "0:8000", "--access-logfile" ,"-"]
