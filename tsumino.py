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

# API_URL_TSUMINO = 'https://www.tsumino.com/Book/Info/' # Tsumino is changing their url structue https://www.tsumino.com/entry/
API_URL_TSUMINO = 'https://www.tsumino.com/entry/'

class Tsumino():

    def __init__(self, database):
        self.database = database

    def analyseNumber(self, galleryNumber):
        title = ''
        numberOfPages = 0
        rating = ''
        category = []
        group = []
        artist = []
        parody = []
        tag = []
        collection = []
        isRedacted = False

        response = self.getHTML(galleryNumber)
        if response:
            soup = BeautifulSoup(response, features="html.parser")
            # title finder
            try:
                title = soup.find('div', id="Title").string.replace('\n','')
            except:
                pass

            # pages finder
            try:
                numberOfPages = soup.find('div', id="Pages").string.replace('\n','')
            except:
                pass

            # rating finder
            try:
                rating = soup.find('div', id="Rating").string.replace('\n','')
            except:
                pass

            # category finder
            try:
                category = [a.get('data-define') for a in soup.find('div', id="Category").findAll('a')]
            except:
                pass

            # group finder
            try:
                group = [a.get('data-define') for a in soup.find('div', id="Group").findAll('a')]
            except:
                pass

            # artist finder
            try:
                artist = [a.get('data-define') for a in soup.find('div', id="Artist").findAll('a')]
            except:
                pass

            # collection finder
            try:
                collection = [a.get('data-define') for a in soup.find('div', id="Collection").findAll('a')]
            except:
                pass

            # parody finder
            try:
                parody = [a.get('data-define') for a in soup.find('div', id="Parody").findAll('a')]
            except:
                pass

            # character finder
            try:
                character = [a.get('data-define') for a in soup.find('div', id="Character").findAll('a')]
            except:
                pass

            # tag finder
            try:
                tag = [a.get('data-define') for a in soup.find('div', id="Tag").findAll('a')]
            except:
                pass

            if tag:
                for entry in tag:
                    if 'loli' in entry.lower():
                        isRedacted = True
                    elif 'shota' in entry.lower():
                        isRedacted = True

            return {
                "title": title,
                "numberOfPages": numberOfPages,
                "rating": rating,
                "category": category,
                "group": group,
                "artist": artist,
                "parody": parody,
                "tag": tag,
                "collection": collection,
                "character": character,
                "isRedacted": isRedacted
            }
        else:
            return []

    def generateLinks(self, number):
        tags = self.analyseNumber(number)
        if tags.get('isRedacted'):
            return "This number contains restricted tags and therefore cannot be linked"
        if tags > 1:
            return API_URL_TSUMINO + str(number)

    def generateReplyString(self, processedData, galleryNumber, censorshipLevel=0, useError=False, generateLink=False):
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
        replyString = ""

        if processedData:
            #Censorship engine
            if processedData.get("isRedacted"):
                #Level 2
                if censorshipLevel > 5:
                    return ""
                if censorshipLevel > 1:
                    # processedData[etc] = ["[REDACTED]" for element in processedData[etc]]
                    if processedData.get("title"):
                        processedData['title'] = "[REDACTED]"
                    if processedData.get("artist"):
                        processedData['artist'] = ["[REDACTED]" for element in processedData.get("artist")]
                    if processedData.get("group"):
                        processedData['group'] = ["[REDACTED]" for element in processedData.get("group")]
                #Level 3
                if censorshipLevel > 2:
                    if processedData.get("collection"):
                        processedData['collection'] = ["[REDACTED]" for element in processedData.get("collection")]
                    if processedData.get("parody"):
                        processedData['parody'] = ["[REDACTED]" for element in processedData.get("parody")]
                #Level 4
                if censorshipLevel > 3:
                    if processedData.get("tag"):
                        processedData['tag'] = ["[REDACTED]" if not any(tags in element.lower() for tags in ['loli','shota']) else element for element in processedData.get("tag")]
                #Level 5
                if censorshipLevel > 4:
                    if processedData.get("pages"):
                        processedData['pages'] = "[REDACTED]"  
                    if processedData.get("rating"):
                        processedData['rating'] = "[REDACTED]"
                    if processedData.get("category"):
                        processedData['category'] = ["[REDACTED]" for element in processedData.get("category")]

            if processedData.get("isRedacted"):
                if censorshipLevel > 0:
                    replyString += ">Tsumino: [REDACTED]\n\n"
                else:
                    replyString += f">Tsumino: {str(galleryNumber).zfill(5)}&#32;\n\n"
                if useError:
                    replyString += f"{commentpy.generate450string('Tsumino')}\n\n"
                    return replyString
            elif generateLink:
                replyString += f">Tsumino: [{str(galleryNumber).zfill(5)}]({API_URL_TSUMINO}{galleryNumber})\n\n"
            else:
                replyString += f">Tsumino: {str(galleryNumber).zfill(5)}\n\n"
            if processedData.get("title"):
                replyString += f"**Title**: {processedData.get('title')}\n\n"
            replyString += f"**Number of pages**: {str(processedData.get('pages'))}\n\n"
            if processedData.get("rating"):
                replyString += f"**Rating**: {processedData.get('rating')}\n\n"

            if processedData.get("category"):
                replyString += commentpy.additionalTagsString(processedData.get("category"), "Category", False) + "\n\n"
            if processedData.get("group"):
                replyString += commentpy.additionalTagsString(processedData.get("group"), "Group", False) + "\n\n"
            if processedData.get("collection"):
                replyString += commentpy.additionalTagsString(processedData.get("collection"), "Collection", False) + "\n\n"
            if processedData.get("artist"):
                replyString += commentpy.additionalTagsString(processedData.get("artist"), "Artist", False) + "\n\n"
            if processedData.get("parody"):
                replyString += commentpy.additionalTagsString(processedData.get("parody"), "Parody", False) + "\n\n"
            if processedData.get("tag"):
                replyString += commentpy.additionalTagsString(processedData.get("tag"), "Tag", False) + "\n\n"
        return replyString


    def getHTML(self, galleryNumber):
        self.database.execute("SELECT last_update, html FROM tsumino WHERE (gallery_number = %s)", [galleryNumber])
        cachedEntry = self.database.fetchone()
        if cachedEntry and ((datetime.datetime.now() - cachedEntry[0]) // datetime.timedelta(days=7)) < 1:
            return cachedEntry[1]
        response = requests.get(API_URL_TSUMINO+str(galleryNumber))
        if response.status_code == 200:
            if cachedEntry:
                self.database.execute("UPDATE tsumino SET last_update = %s, html = %s WHERE (gallery_number = %s)", (datetime.datetime.now(), response.text, int(galleryNumber)))
            else:
                self.database.execute("INSERT INTO tsumino (gallery_number, last_update, html) VALUES (%s, %s, %s)", (int(galleryNumber), datetime.datetime.now(), response.text))
            self.database.commit()
            return response.text


    def getNumbers(self, comment):
        numbers = re.findall(r'(?<=\))\d{5}(?=\()', comment)
        try:
            numbers = [int(number) for number in numbers]
        except ValueError:
            numbers = []
        numbers = commentpy.removeDuplicates(numbers)
        return [{'number': number, 'type': 'tsumino'} for number in numbers]


    def remove_and_return_old_results_from_comment(self, comment):
        tsuminoNumbers = re.findall(r'(?<=>Tsumino: )\d{5,6}', comment)
        try:
            tsuminoNumbers = [int(number) for number in tsuminoNumbers]
        except ValueError:
            tsuminoNumbers = []
        comment = re.sub(r'(?<=>Tsumino: )\d{5,6}', '', comment)
        return [{'number': number, 'type': 'tsumino'} for number in tsuminoNumbers], comment


    def scanURL(self, comment):
        tsuminoNumbers = []
        # use lowercase comment because tsumino has an inconsistent url scheme 
        commentLower = comment.lower()
        tsuminoLinks = re.findall(r'https?:\/\/(?:www.)?tsumino.com\/book\/info\/\d{1,5}', commentLower)
        tsuminoLinks += re.findall(r'https?:\/\/(?:www.)?tsumino.com\/read\/view\/\d{1,5}', commentLower)
        tsuminoLinks += re.findall(r'https?:\/\/(?:www.)?tsumino.com\/entry\/\d{1,5}', commentLower)
        try:
            tsuminoNumbers = [re.search(r'\d+', link).group(0) for link in tsuminoLinks]
        except AttributeError:
            pass
        try:
            tsuminoNumbers = [int(number) for number in tsuminoNumbers]
        except ValueError:
            tsuminoNumbers = []
        tsuminoNumbers = commentpy.removeDuplicates(tsuminoNumbers)
        return [{'number': number, 'type': 'tsumino'} for number in tsuminoNumbers]
        