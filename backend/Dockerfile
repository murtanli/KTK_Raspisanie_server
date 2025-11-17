FROM python:3.11

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /usr/src/backend

COPY ./requirements.txt /usr/src/requirements.txt
RUN pip install -r /usr/src/requirements.txt

COPY . /usr/src/backend

EXPOSE 8000
#RUN python manage.py makemigrations
#RUN python manage.py migrate
CMD ["python manage.py runserver 0.0.0.0:8100"]