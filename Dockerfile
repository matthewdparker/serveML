FROM python:3

COPY app.py /src/app.py
COPY requirements.txt /src/requirements.txt
COPY products /src/products
RUN pip install -r src/requirements.txt

EXPOSE 5000

CMD [ "python", "./src/app.py"]
