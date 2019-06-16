# from https://stackoverflow.com/questions/16981921/relative-imports-in-python-3 to make the imports work when imported as submodule
import os, sys; sys.path.append(os.path.dirname(os.path.realpath(__file__)))
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

        if tags:
            for entry in tags:
                if 'loli' in entry.lower():
                    isRedacted = True
                elif "shota" in entry.lower():
                    isRedacted = True

        return [title, numberOfPages, artist, group, types, language, series, characters, tags, isRedacted]
    else:
        return []

def generateReplyString(processedData, galleryNumber, censorshipLevel=0, useError=False, generateLink=False):
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
            replyString += ">Hitomi.la: " + str(galleryNumber).zfill(5) + "\n\n"
            if processedData[0] == 'Redirect':
                replyString += "This gallery is trying to redirect and therfore doesn't exist anymore. Please try a different one."
                return replyString
            if processedData[0] == 404:
                replyString += "This gallery is returning a 404. The gallery has either been removed or doesn't exist yet."

        #Censorship engine
        if processedData[isRedacted]:
            if censorshipLevel > 5:
                return ""
            #Level 2
            if censorshipLevel > 1:
                if processedData[artist]:
                    processedData[artist] = "[REDACTED]"
                if processedData[title]:
                    processedData[title] = "[REDACTED]"
                if processedData[group]:
                    processedData[group] = ["[REDACTED]" for element in processedData[group]]
            #Level 3
            if censorshipLevel > 2:
                if processedData[series]:
                    processedData[series] = ["[REDACTED]" for element in processedData[series]]
                if processedData[characters]:
                    processedData[characters] = ["[REDACTED]" for element in processedData[characters]]
            #Level 4
            if censorshipLevel > 3:
                if processedData[tags]:
                    processedData[tags] = ["[REDACTED]" if not any(tag in element.lower() for tag in ['loli','shota']) else element for element in processedData[tags]]
            #Level 5
            if censorshipLevel > 4:
                if processedData[pages] > 0:
                    processedData[pages] = 0
                if processedData[types]:
                    processedData[types] = ["[REDACTED]" for element in processedData[types]]
                if processedData[language]:
                    processedData[language] = ["[REDACTED]" for element in processedData[language]]



        if processedData[isRedacted]:
            if censorshipLevel > 0:
                replyString += ">Hitomi.la: [REDACTED]\n\n"
            else:
                replyString += f">Hitomi.la: {str(galleryNumber).zfill(5)}&#32;\n\n"
                if useError:
                    replyString += f"{commentpy.generate450string('Hitomi.la')}\n\n"
                    return replyString
        elif generateLink:
            replyString += f">Hitomi.la: [{str(galleryNumber).zfill(5)}]({API_URL_HITOMILA}{galleryNumber}.html)\n\n"
        else:
            replyString += ">Hitomi.la: " + str(galleryNumber).zfill(5) + "\n\n"

        if processedData[title]:
            replyString += "**Title**: " + processedData[title] + "\n\n"
        if processedData[pages] > 0:
            replyString += "**Number of pages**: " + str(processedData[pages]) + "\n\n"
        if processedData[artist]:
            replyString += "**Artist**: " + processedData[artist] + "\n\n"
        
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
    numbers = re.findall(r'(?<=(?<!\>)\!)\d{5,8}(?=\!(?!\<))', comment)
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
        hitomilaNumbers = [re.search(r'\d+', link).group(0) for link in hitomilaLinks]
    except AttributeError:
        print("No Tsumino links")
    try:
        hitomilaNumbers = [int(number) for number in hitomilaNumbers]
    except ValueError:
        hitomilaNumbers = []
    hitomilaNumbers = commentpy.removeDuplicates(hitomilaNumbers)
    return hitomilaNumbers