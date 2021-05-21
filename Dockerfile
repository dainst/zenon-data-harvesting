FROM python:3.6

WORKDIR /usr/src/app

COPY requirements_frozen.txt ./requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

CMD [ "python", "-u", "./harvest_new_records.py" ]
