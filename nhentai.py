# from https://stackoverflow.com/questions/16981921/relative-imports-in-python-3 to make the imports work when imported as submodule
import os, sys; sys.path.append(os.path.dirname(os.path.realpath(__file__)))
import commentpy
import requests
import json
import re
import time
import datetime
import uuid

from postgres_credentials import PROXY_URL

# API_URL_NHENTAI = 'https://nhentai.net/api/gallery/'
API_URL_NHENTAI = PROXY_URL
LINK_URL_NHENTAI = "https://nhentai.net/g/"

class Nhentai():
    def __init__(self, database):
        self.database = database

    def analyseNumber(self, galleryNumber):
        title = ''
        numberOfPages = 0
        listOfTags = []
        languages = []
        artists = []
        categories = []
        parodies = []
        characters = []
        groups = []
        isRedacted = False
        error = None
        rawData = self.getJSON(galleryNumber)
        if rawData and rawData.get('error'):
            error = rawData.get('error')
            if len(rawData) == 1:
                return rawData
        if rawData:
            title = rawData['title']['pretty']
            numberOfPages = rawData['num_pages']
            for tags in rawData['tags']:
                if 'tag' in tags['type']:
                    listOfTags.append([tags['name'], tags['count']])
                elif 'language' in tags['type']:
                    languages.append([tags['name'], tags['count']])
                elif 'artist' in tags['type']:
                    artists.append([tags['name'], tags['count']])
                elif 'category' in tags['type']:
                    categories.append([tags['name'], tags['count']])
                elif 'parody' in tags['type']:
                    parodies.append([tags['name'], tags['count']])
                elif 'character' in tags['type']:
                    characters.append([tags['name'], tags['count']])
                elif 'group' in tags['type']:
                    groups.append([tags['name'], tags['count']])
            if listOfTags:
                #TODO use any()
                for entry in listOfTags:
                    if 'lolicon' in entry[0]:
                        isRedacted = True
                    elif 'shotacon' in entry[0]:
                        isRedacted = True

        processedData = {
            "title": title,
            "numberOfPages": numberOfPages,
            "listOfTags": listOfTags,
            "languages": languages, 
            "artists": artists,
            "categories": categories,
            "parodies": parodies,
            "characters": characters,
            "groups": groups,
            "isRedacted": isRedacted,
            "error": error
        }
        
        # Sort the tags by descending popularity to imitate website behavior
        for key in processedData.keys():
            if not key in ["title", "numberOfPages", "isRedacted", "error"]:
                processedData[key] = sorted(processedData[key], key=lambda tags: tags[1], reverse=True)
        return processedData

    def generateLinks(self, number):
        tags = self.analyseNumber(number)
        if tags.get('isRedacted'):
            return "This number contains restricted tags and therefore cannot be linked"
        if len(tags) > 1:
            return LINK_URL_NHENTAI + str(number) + '/'

    def generateReplyString(self, processedData, galleryNumber, censorshipLevel=0, useError=False, generateLink=False):
        # parodies
        # characters
        # tags
        # artists
        # groups
        # languages
        # categories
        replyString = ""
        if processedData.get("isRedacted"):
            if censorshipLevel > 0:
                replyString += ">[REDACTED]\n\n"
            else:
                replyString += f">{str(galleryNumber).zfill(5)}&#32;\n\n"
            if useError:
                replyString += f"{commentpy.generate450string('nHentai')}\n\n"
                return replyString
        elif generateLink:
            replyString += f">[{str(galleryNumber).zfill(5)}]({LINK_URL_NHENTAI}{galleryNumber}/)\n\n"
        else:
            replyString += ">" + str(galleryNumber).zfill(5) + "\n\n"
        if processedData.get('error'):
            replyString += f"nHentai returned {processedData.get('error')}. \n\n"
            if processedData.get('error') == 404 and not processedData.get('title'):
                replyString = replyString[:-2] + "The gallery has either been removed or doesn't exist yet. \n\n"
            if processedData.get("title"):
                replyString = replyString[:-2] + "Using cached gallery info:\n\n"
            elif processedData.get('error') != 404:
                replyString = replyString[:-2] + "Gallery info couldn't be retrieved at the moment.\n\n"
        if processedData.get("title"):
            #Censorship engine
            if processedData.get("isRedacted"):
                if censorshipLevel > 5:
                    return ""
                #Level 2
                if censorshipLevel > 1:
                    processedData["title"] = "[REDACTED]"
                    if processedData.get("artists"):
                        for element in processedData.get("artists"):
                            element[0] = "[REDACTED]"
                    if processedData.get("groups"):
                        for element in processedData.get("groups"):
                            element[0] = "[REDACTED]"
                #Level 3
                if censorshipLevel > 2:
                    if processedData.get("characters"):
                        for element in processedData.get("characters"):
                            element[0] = "[REDACTED]"
                    if processedData.get("parodies"):
                        for element in processedData.get("parodies"):
                            element[0] = "[REDACTED]"
                #Level 4
                if censorshipLevel > 3:
                    if processedData.get("listOfTags"):
                        for element in processedData.get("listOfTags"):
                            if not any(tag in element[0] for tag in ['loli','shota']):
                                element[0] = "[REDACTED]"
                #Level 5
                if censorshipLevel > 4:
                    if processedData.get("languages"):
                        for element in processedData.get("languages"):
                            element[0] = "[REDACTED]"
                    if processedData.get("categories"):
                        for element in processedData.get("categories"):
                            element[0] = "[REDACTED]"
                    processedData["numberOfPages"] = "[REDACTED]"

            replyString += "**Title**: " + processedData.get("title") + "\n\n"
            replyString += "**Number of pages**: " + str(processedData.get("numberOfPages")) + "\n\n"
            
            if processedData.get("characters"):
                replyString += commentpy.additionalTagsString(processedData.get("characters"), "Characters") + "\n\n"
            if processedData.get("parodies"):
                replyString += commentpy.additionalTagsString(processedData.get("parodies"), "Parodies") + "\n\n"
            if processedData.get("listOfTags"):
                replyString += commentpy.additionalTagsString(processedData.get("listOfTags"), "Tags") + "\n\n"
            if processedData.get("artists"):
                replyString += commentpy.additionalTagsString(processedData.get("artists"), "Artists") + "\n\n"
            if processedData.get("groups"):
                replyString += commentpy.additionalTagsString(processedData.get("groups"), "Groups") + "\n\n"
            if processedData.get("languages"):
                replyString += commentpy.additionalTagsString(processedData.get("languages"), "Languages") + "\n\n"
            if processedData.get("categories"):
                replyString += commentpy.additionalTagsString(processedData.get("categories"), "Categories") + "\n\n"
        return replyString


    def getJSON(self, galleryNumber):
        galleryNumber = str(galleryNumber)
        # request = getRequest(galleryNumber) # ['tags'] #
        # Fetch gallery info from cache
        self.database.execute("SELECT last_update, json FROM nhentai WHERE (gallery_number = %s)", [galleryNumber])
        cachedEntry = self.database.fetchone()
        # Use cached entry if new enough (less than 7 days old)
        if cachedEntry and ((datetime.datetime.utcnow() - cachedEntry[0]) // datetime.timedelta(days=7)) < 1:
            return cachedEntry[1]
        try:
            request = requests.get(API_URL_NHENTAI+galleryNumber)
        # TODO make error more specifc to connection refused.
        except Exception as e:
            if cachedEntry:
                return cachedEntry[1]
            else:
                return {'error': 408}
        if request == None:
            if cachedEntry:
                return cachedEntry[1]
            else:
                return []
        if request.status_code != 200:
            if cachedEntry:
                return_json = cachedEntry[1]
                return_json.update({'error': request.status_code})
                return return_json
            else:
                return {'error': request.status_code}
        # nhentaiTags = json.loads(re.search(r'(?<=N.gallery\().*(?=\))', request.text).group(0))
        nhentaiTags = request.json()
        if "error" in nhentaiTags:
            return {'error': 404}
        if cachedEntry:
            self.database.execute("UPDATE nhentai SET last_update = %s, json = %s WHERE (gallery_number = %s)", (datetime.datetime.utcnow(), json.dumps(nhentaiTags), int(galleryNumber)))
        else:
            self.database.execute("INSERT INTO nhentai (gallery_number, last_update, json) VALUES (%s, %s, %s)", (int(galleryNumber), datetime.datetime.utcnow(), json.dumps(nhentaiTags)))
        self.database.commit()
        return nhentaiTags


    def getRequest(self, galleryNumber):
        for i in range(1, 5):
            request = requests.get(LINK_URL_NHENTAI+galleryNumber) # ['tags'] #
            if request.status_code == 200 or request.status_code == 404:
                return request
            time.sleep(i)
        return None

    def getNumbers(self, comment):
        numbers = re.findall(r'(?<=\()\d{5,6}(?=\))', comment)
        try:
            numbers = [int(number) for number in numbers]
        except ValueError:
            numbers = []
        numbers = commentpy.removeDuplicates(numbers)
        return [{'number': number, 'type': 'nhentai'} for number in numbers]


    def remove_and_return_old_results_from_comment(self, comment):
        nhentaiNumbers = re.findall(r'\d{5,6}', comment)
        try:
            nhentaiNumbers = [int(number) for number in nhentaiNumbers]
        except ValueError:
            nhentaiNumbers = []
        return [{'number': number, 'type': 'nhentai'} for number in nhentaiNumbers], comment


    def scanURL(self, comment):
        nhentaiNumbers = []
        nhentaiLinks = re.findall(r'https?:\/\/(?:www.)?nhentai.net\/g\/\d{1,6}', comment.lower())
        try:
            nhentaiNumbers = [re.search(r'\d+', link).group(0) for link in nhentaiLinks]
        except AttributeError:
            pass
        try:
            nhentaiNumbers = [int(number) for number in nhentaiNumbers]
        except ValueError:
            nhentaiNumbers = []
        nhentaiNumbers = commentpy.removeDuplicates(nhentaiNumbers)
        return [{'number': number, 'type': 'nhentai'} for number in nhentaiNumbers]


from DBConn import Database
databae = Database()
nhentai = Nhentai(databae)
r = nhentai.getJSON(481105)
print(r)