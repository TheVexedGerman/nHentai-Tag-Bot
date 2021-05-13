# from https://stackoverflow.com/questions/16981921/relative-imports-in-python-3 to make the imports work when imported as submodule
import os, sys; sys.path.append(os.path.dirname(os.path.realpath(__file__)))
import commentpy
import requests
import json
import re
import datetime
from bs4 import BeautifulSoup

# from DBConn import Database 

# db = Database()
API_URL_HITOMILA = 'https://hitomi.la/galleries/' # needs .html appended


# Needs complete rework probably using https://ltn.hitomi.la/galleryblock/719638.html or https://ltn.hitomi.la/galleryblock/719638.html endpoints.
class Hitomila():

    def __init__(self, database):
        self.database = database

    def analyseNumber(self, galleryNumber):
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

        # response = requests.get(API_URL_HITOMILA+str(galleryNumber)+".html")
        response = self.getHTML(galleryNumber)
        if response == 404:
            return [404]
        if response:
            soup = BeautifulSoup(response, features="html.parser")

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
            numbersText = re.findall(r'tn\.hitomi\.la\/smalltn\/', response)
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

            return {
                "title": title,
                "numberOfPages": numberOfPages,
                "artist": artist, 
                "group": group,
                "types": types,
                "language": language, 
                "series": series, 
                "characters": characters, 
                "tags": tags,
                "isRedacted": isRedacted
            }
        else:
            return []

    def generateLinks(self, number):
        tags = self.analyseNumber(number)
        if tags.get('isRedacted'):
            return "This number contains restricted tags and therefore cannot be linked"
        if len(tags) > 1:
            return API_URL_HITOMILA + str(number) + ".html"

    def generateReplyString(self, processedData, galleryNumber, censorshipLevel=0, useError=False, generateLink=False):
        replyString = ''

        if processedData:
            if not len(processedData) > 2:
                replyString += f">Hitomi.la: {str(galleryNumber).zfill(5)}\n\n"
                if processedData[0] == 'Redirect':
                    replyString += "This gallery is trying to redirect and therfore doesn't exist anymore. Please try a different one."
                    return replyString
                if processedData[0] == 404:
                    replyString += "This gallery is returning a 404. The gallery has either been removed or doesn't exist yet."

            #Censorship engine
            if processedData.get('isRedacted'):
                if censorshipLevel > 5:
                    return ""
                #Level 2
                if censorshipLevel > 1:
                    if processedData.get('artist'):
                        processedData['artist'] = "[REDACTED]"
                    if processedData.get('title'):
                        processedData['title'] = "[REDACTED]"
                    if processedData.get('group'):
                        processedData['group'] = ["[REDACTED]" for element in processedData.get('group')]
                #Level 3
                if censorshipLevel > 2:
                    if processedData.get('series'):
                        processedData['series'] = ["[REDACTED]" for element in processedData.get('series')]
                    if processedData.get('characters'):
                        processedData['characters'] = ["[REDACTED]" for element in processedData.get('characters')]
                #Level 4
                if censorshipLevel > 3:
                    if processedData.get('tags'):
                        processedData['tags'] = ["[REDACTED]" if not any(tag in element.lower() for tag in ['loli','shota']) else element for element in processedData.get('tags')]
                #Level 5
                if censorshipLevel > 4:
                    if processedData.get('pages') > 0:
                        processedData['pages'] = 0
                    if processedData.get('types'):
                        processedData['types'] = ["[REDACTED]" for element in processedData.get('types')]
                    if processedData.get('language'):
                        processedData['language'] = ["[REDACTED]" for element in processedData.get('language')]

            if processedData.get('isRedacted'):
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
                replyString += f">Hitomi.la: {str(galleryNumber).zfill(5)}\n\n"

            if processedData.get('title'):
                replyString += f"**Title**: {processedData.get('title')}\n\n"
            if processedData.get('pages') > 0:
                replyString += f"**Number of pages**: {str(processedData.get('pages'))}\n\n"
            if processedData.get('artist'):
                replyString += f"**Artist**: {processedData.get('artist')}\n\n"
            
            if processedData.get('group'):
                replyString += commentpy.additionalTagsString(processedData.get('group'), "Group", False) + "\n\n"
            if processedData.get('types'):
                replyString += commentpy.additionalTagsString(processedData.get('types'), "Type", False) + "\n\n"
            if processedData.get('language'):
                replyString += commentpy.additionalTagsString(processedData.get('language'), "Language", False) + "\n\n"
            if processedData.get('series'):
                replyString += commentpy.additionalTagsString(processedData.get('series'), "Series", False) + "\n\n"
            if processedData.get('characters'):
                replyString += commentpy.additionalTagsString(processedData.get('characters'), "Characters", False) + "\n\n"
            if processedData.get('tags'):
                replyString += commentpy.additionalTagsString(processedData.get('tags'), "Tag", False) + "\n\n"
        return replyString


    def getHTML(self, galleryNumber):
        self.database.execute("SELECT * FROM hitomila WHERE (gallery_number = %s)", [galleryNumber])
        cachedEntry = self.database.fetchone()
        if cachedEntry and ((datetime.datetime.now() - cachedEntry[1]) // datetime.timedelta(days=7)) < 1:
            print("cache used")
            return cachedEntry[2]
        response = requests.get(API_URL_HITOMILA+str(galleryNumber)+".html")
        if not cachedEntry and response.status_code == 404:
            return 404
        if response.status_code == 200:
            if cachedEntry:
                print("update cache")
                self.database.execute("UPDATE hitomila SET last_update = %s, html = %s WHERE (gallery_number = %s)", (datetime.datetime.now(), response.text, galleryNumber))
            else:
                print("create cache")
                self.database.execute("INSERT INTO hitomila (gallery_number, last_update, html) VALUES (%s, %s, %s)", (galleryNumber, datetime.datetime.now(), response.text))
            self.database.commit()
            return response.text


    def getNumbers(self, comment):
        numbers = re.findall(r'(?<=(?<!\>)\!)\d{5,8}(?=\!(?!\<))', comment)
        try:
            numbers = [int(number) for number in numbers]
        except ValueError:
            numbers = []
        numbers = commentpy.removeDuplicates(numbers)
        return [{'number': number, 'type': 'hitomila'} for number in numbers]


    def remove_and_return_old_results_from_comment(self, comment):
        hitomilaNumbers = re.findall(r'(?<=>Hitomi.la: )\d{5,8}', comment)
        try:
            hitomilaNumbers = [int(number) for number in hitomilaNumbers]
        except ValueError:
            hitomilaNumbers = []
        comment = re.sub(r'(?<=>Hitomi.la: )\d{5,8}', '', comment)
        return [{'number': number, 'type': 'hitomila'} for number in hitomilaNumbers], comment


    def scanURL(self, comment):
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
        return [{'number': number, 'type': 'hitomila'} for number in hitomilaNumbers]
