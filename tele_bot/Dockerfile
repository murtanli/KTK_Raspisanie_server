FROM python:3.11

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /usr/src/tele_bot

COPY ./requirements.txt /usr/src/requirements.txt
RUN pip install -r /usr/src/requirements.txt

COPY . /usr/src/tele_bot

EXPOSE 8050
#RUN python manage.py makemigrations
#RUN python manage.py migrate
CMD ["python bot.py"]