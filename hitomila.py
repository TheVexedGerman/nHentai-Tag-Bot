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
    if response.status_code == 404:
        return [404]
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, features="html.parser")

        # Check for redirect
        if soup.title.string == 'Redirect':
            return ['Redirect']

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

        return [title, numberOfPages, [artist], group, types, language, series, characters, tags, isRedacted]
    else:
        return []

def generateReplyString(processedData, galleryNumber):
    title = 0
    pages = 1
    artist = 2
    group = 3
    types = 4
    language = 5
    series = 6
    characters = 7
    tags = 8
    isRedacted = 9
    replyString = ''

    if processedData:
        if not len(processedData) > 2:
            replyString += ">Hitomi.la: " + str(galleryNumber) + "\n\n"
            if processedData[0] == 'Redirect':
                replyString += "This gallery is trying to redirect and therfore doesn't exist anymore. Please try a different one."
                return replyString
            if processedData[0] == 404:
                replyString += "This gallery is returning a 404. The gallery has either been removed or doesn't exist yet."
        if processedData[isRedacted]:
            replyString += ">Hitomi.la: [REDACTED]\n\n"
        else:
            replyString += ">Hitomi.la: " + str(galleryNumber) + "\n\n"
        if processedData[title]:
            replyString += "**Title**: " + processedData[title] + "\n\n"
        if processedData[pages] > 0:
            replyString += "**Number of pages**: " + str(processedData[pages]) + "\n\n"
        
        if processedData[artist]:
            replyString += commentpy.additionalTagsString(processedData[artist], "Artist", False) + "\n\n"
        if processedData[group]:
            replyString += commentpy.additionalTagsString(processedData[group], "Group", False) + "\n\n"
        if processedData[types]:
            replyString += commentpy.additionalTagsString(processedData[types], "Type", False) + "\n\n"
        if processedData[language]:
            replyString += commentpy.additionalTagsString(processedData[language], "Language", False) + "\n\n"
        if processedData[series]:
            replyString += commentpy.additionalTagsString(processedData[series], "Series", False) + "\n\n"
        if processedData[characters]:
            replyString += commentpy.additionalTagsString(processedData[characters], "Characters", False) + "\n\n"
        if processedData[tags]:
            replyString += commentpy.additionalTagsString(processedData[tags], "Tag", False) + "\n\n"
    return replyString

def getNumbers(comment):
    numbers = re.findall(r'(?<=\!)\d{5,8}(?=\!', comment)
    try:
        numbers = [int(number) for number in numbers]
    except ValueError:
        numbers = []
    numbers = commentpy.removeDuplicates(numbers)
    return numbers

def scanURL(comment):
    hitomilaNumbers = []
    # https://hitomi.la/galleries/1367588.html
    # https://hitomi.la/reader/1367588.html#2
    hitomilaLinks = re.findall(r'https?:\/\/(?:www.)?hitomi.la\/galleries\/\d{1,8}', comment)
    hitomilaLinks += re.findall(r'https?:\/\/(?:www.)?hitomi.la\/reader\/\d{1,8}', comment)
    try:
        tsuminohitomilaNumbersNumbers = [re.search(r'\d+', link).group(0) for link in hitomilaLinks]
    except AttributeError:
        print("No Tsumino links")
    try:
        hitomilaNumbers = [int(number) for number in hitomilaNumbers]
    except ValueError:
        hitomilaNumbers = []
    hitomilaNumbers = commentpy.removeDuplicates(hitomilaNumbers)
    return hitomilaNumbers