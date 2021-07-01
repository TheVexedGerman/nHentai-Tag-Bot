FROM python:3.9-buster

WORKDIR /home/python

RUN git clone https://github.com/TheVexedGerman/nHentai-Tag-Bot.git

RUN pip install --no-cache-dir -r requirements.txt
COPY praw.ini postgres_credentials.py ./

CMD [ "bash", "/home/python/start.sh"]