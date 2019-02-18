import commentpy
import requests
import json
import re
from bs4 import BeautifulSoup

API_URL_HITOMILA = 'https://hitomi.la/galleries/' # needs .html appended

def analyseNumber(galleryNumber):
    title = ''
    numberOfPages = 0
    artist = ''
    group = []
    types = []
    language = []
    series = []
    characters = []
    tags = []
    isRedacted = False

    response = requests.get(API_URL_HITOMILA+str(galleryNumber)+".html")
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, features="html.parser")
        # reduce the html to the most relevant part
        relevant = soup.find('div', class_="gallery")
        try:
            title = relevant.h1.string.title()
            print(title)
        except:
            print("No Title")
        try:
            artist = relevant.h2.li.string.title()
            print(artist)
        except:
            print("No Artist")

        # Page count works by finding and counting the loaded thumbnail images
        numbersText = re.findall(r'tn\.hitomi\.la\/smalltn\/', response.text)
        numberOfPages = len(numbersText)

        # reduce scope to the different remaining categories
        categories = relevant.find('div', class_="gallery-info")

        try:
            group = [a.string.title() for a in categories.table.findAll('a', href=re.compile(r'\/group\/'))]
            print(title)
        except:
            print("No Title")

        try:
            types = [re.search(r'\S+\s?\S+', a.string).group(0).title() for a in categories.table.findAll('a', href=re.compile(r'\/type\/'))]
            print(types)
        except:
            print("No type")

        try:
            language = [a.string for a in categories.table.findAll('a', href=re.compile(r'\/index\-'))]
            print(language)
        except:
            print("No language")

        try:
            series = [a.string.title() for a in categories.table.findAll('a', href=re.compile(r'\/series\/'))]
            print(series)
        except:
            print("No Series")

        try:
            characters = [a.string.title() for a in categories.table.findAll('a', href=re.compile(r'\/character\/'))]
            print(characters)
        except:
            print("No Characters")

        try:
            tags = [a.string.title() for a in categories.table.findAll('a', href=re.compile(r'\/tag\/'))]
            print(tags)
        except:
            print("No Tags")

        return [title, numberOfPages, artist, group, types, language, series, characters, tags, isRedacted]
    else:
        return []