import commentpy
import requests
import json
import re
from bs4 import BeautifulSoup

API_URL_NHENTAI = 'https://nhentai.net/api/gallery/'
API_URL_TSUMINO = 'https://www.tsumino.com/Book/Info/'
API_URL_EHENTAI = "https://api.e-hentai.org/api.php"
LINK_URL_NHENTAI = "https://nhentai.net/g/"
LINK_URL_EHENTAI = "https://e-hentai.org/g/"

def analyseNumber(galleryNumber):
    title = ''
    numberOfPages = 0
    rating = ''
    category = []
    group = []
    artist = []
    parody = []
    tag = []
    collection = []
    isLoli = False

    response = requests.get(API_URL_TSUMINO+str(galleryNumber))
    print(response)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, features="html.parser")
        # title finder
        try:
            title = soup.find('div', id="Title").string.replace('\n','')
            print(title)
        except:
            print("No Title")

        # pages finder
        try:
            numberOfPages = soup.find('div', id="Pages").string.replace('\n','')
            print(numberOfPages)
        except:
            print("No Pages")

        # rating finder
        try:
            rating = soup.find('div', id="Rating").string.replace('\n','')
            print(rating)
        except:
            print("No Rating")

        # category finder
        try:
            category = [a.get('data-define') for a in soup.find('div', id="Category").findAll('a')]
            print(category)
        except:
            print("No Category")

        # group finder
        try:
            group = [a.get('data-define') for a in soup.find('div', id="Group").findAll('a')]
            print(group)
        except:
            print("No Group")

        # artist finder
        try:
            artist = [a.get('data-define') for a in soup.find('div', id="Artist").findAll('a')]
            print(artist)
        except:
            print("No Artist")

        # collection finder
        try:
            collection = [a.get('data-define') for a in soup.find('div', id="Collection").findAll('a')]
            print(collection)
        except:
            print("No Collection")

        # parody finder
        try:
            parody = [a.get('data-define') for a in soup.find('div', id="Parody").findAll('a')]
            print(parody)
        except:
            print("No Parody")

        # character finder
        try:
            character = [a.get('data-define') for a in soup.find('div', id="Character").findAll('a')]
            print(character)
        except:
            print("No Character")

        # tag finder
        try:
            tag = [a.get('data-define') for a in soup.find('div', id="Tag").findAll('a')]
            print(tag)
        except:
            print("No Tags")

        if tag:
            for entry in tag:
                if 'Lolicon' in entry:
                    isLoli = True
                elif 'Shotacon' in entry:
                    isLoli = True

        return [title, numberOfPages, rating, category, group, artist, parody, tag, collection, isLoli]
    else:
        return []


def generateReplyString(processedData, galleryNumber):
    # Title
    # Uploader (Rejected)
    # Uploaded (Rejected)
    # Pages
    # Rating
    # My Rating (Rejected)
    # Category
    # Group
    # Collection (optional)
    # Artist
    # Parody (optional)
    # Character
    # Tag
    # [title, numberOfPages, rating, category, group, artist, parody, tag, collection]
    title = 0
    pages = 1
    rating = 2
    category = 3
    group = 4
    artist = 5
    parody = 6
    tag = 7
    collection = 8
    isLoli = 9
    replyString = ""
    print("Tsumino replyStringGenerator Start")

    if processedData:
        if processedData[isLoli]:
            replyString += ">Tsumino: [REDACTED]\n\n"
        else:
            replyString += ">Tsumino: " + str(galleryNumber).zfill(5) + "\n\n"
        if processedData[title]:
            replyString += "**Title**: " + processedData[title] + "\n\n"
        replyString += "**Number of pages**: " + str(processedData[pages]) + "\n\n"
        if processedData[rating]:
            replyString += "**Rating**: " + processedData[rating] + "\n\n"

        if processedData[category]:
            replyString += commentpy.additionalTagsString(processedData[category], "Category", False) + "\n\n"
        if processedData[group]:
            replyString += commentpy.additionalTagsString(processedData[group], "Group", False) + "\n\n"
        if processedData[collection]:
            replyString += commentpy.additionalTagsString(processedData[collection], "Collection", False) + "\n\n"
        if processedData[artist]:
            replyString += commentpy.additionalTagsString(processedData[artist], "Artist", False) + "\n\n"
        if processedData[parody]:
            replyString += commentpy.additionalTagsString(processedData[parody], "Parody", False) + "\n\n"
        if processedData[tag]:
            replyString += commentpy.additionalTagsString(processedData[tag], "Tag", False) + "\n\n"
    print("Tsumino replyStringGenerator End")
    return replyString


def getNumbers(comment):
    numbers = re.findall(r'(?<=\))\d{5}(?=\()', comment)
    try:
        numbers = [int(number) for number in numbers]
    except ValueError:
        numbers = []
    numbers = commentpy.removeDuplicates(numbers)
    return numbers