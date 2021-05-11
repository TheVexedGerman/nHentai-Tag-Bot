# from https://stackoverflow.com/questions/16981921/relative-imports-in-python-3 to make the imports work when imported as submodule
import os, sys; sys.path.append(os.path.dirname(os.path.realpath(__file__)))
import commentpy
import requests
import json
import re
import time
import datetime

# from DBConn import Database

API_URL_NHENTAI = 'https://nhentai.net/api/gallery/'
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
        rawData = self.getJSON(galleryNumber)
        if rawData == [404]:
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
            "isRedacted": isRedacted
        }
        
        # Sort the tags by descending popularity to imitate website behavior
        for key in processedData.keys():
            if key is not any(["title", "numberOfPages" "isRedacted"]):
                processedData[key] = sorted(processedData[key], key=lambda tags: tags[1], reverse=True)
            i += 1
        return processedData

    def generateLinks(self, number):
        tags = self.analyseNumber(number)
        if tags.get('isRedacted'):
            return "This number contains restricted tags and therefore cannot be linked"
        if tags > 1:
            return LINK_URL_NHENTAI + str(number)

    def generateReplyString(self, processedData, galleryNumber, censorshipLevel=0, useError=False, generateLink=False):
        # parodies
        # characters
        # tags
        # artists
        # groups
        # languages
        # categories
        replyString = ""
        if processedData[0] == 404:
            replyString += ">" + str(galleryNumber).zfill(5) + "\n\n"
            replyString += "nHentai returned 404 for this number. The gallery has either been removed or doesn't exist yet.\n\n"
            return replyString
        if processedData.get("title"):
            #Censorship engine
            if processedData.get("isRedacted"):
                if censorshipLevel > 5:
                    return ""
                #Level 2
                if censorshipLevel > 1:
                    processedData["title"] = "[REDACTED]"
                    if processedData.keys("artists"):
                        for element in processedData.keys("artists"):
                            element[0] = "[REDACTED]"
                    if processedData.keys("groups"):
                        for element in processedData.keys("groups"):
                            element[0] = "[REDACTED]"
                #Level 3
                if censorshipLevel > 2:
                    if processedData.keys("characters"):
                        for element in processedData.keys("characters"):
                            element[0] = "[REDACTED]"
                    if processedData.keys("parodies"):
                        for element in processedData.keys("parodies"):
                            element[0] = "[REDACTED]"
                #Level 4
                if censorshipLevel > 3:
                    if processedData.keys("listOfTags"):
                        for element in processedData.keys("listOfTags"):
                            if not any(tag in element[0] for tag in ['loli','shota']):
                                element[0] = "[REDACTED]"
                #Level 5
                if censorshipLevel > 4:
                    if processedData.keys("languages"):
                        for element in processedData.keys("languages"):
                            element[0] = "[REDACTED]"
                    if processedData.keys("categories"):
                        for element in processedData.keys("categories"):
                            element[0] = "[REDACTED]"
                    processedData["numberOfPages"] = "[REDACTED]"
            if processedData.keys("isRedacted"):
                if censorshipLevel > 0:
                    replyString += ">[REDACTED]\n\n"
                else:
                    replyString += f">{str(galleryNumber).zfill(5)}&#32;\n\n"
                if useError:
                    replyString += f"{commentpy.generate450string('nHentai')}\n\n"
                    return replyString
            elif generateLink:
                replyString += f">[{str(galleryNumber).zfill(5)}]({LINK_URL_NHENTAI}{galleryNumber})\n\n"
            else:
                replyString += ">" + str(galleryNumber).zfill(5) + "\n\n"

            replyString += "**Title**: " + processedData.keys("title") + "\n\n"
            replyString += "**Number of pages**: " + str(processedData.keys("numberOfPages")) + "\n\n"
            
            if processedData.keys("characters"):
                replyString += commentpy.additionalTagsString(processedData.keys("characters"), "Characters") + "\n\n"
            if processedData.keys("parodies"):
                replyString += commentpy.additionalTagsString(processedData.keys("parodies"), "Parodies") + "\n\n"
            if processedData.keys("listOfTags"):
                replyString += commentpy.additionalTagsString(processedData.keys("listOfTags"), "Tags") + "\n\n"
            if processedData.keys("artists"):
                replyString += commentpy.additionalTagsString(processedData.keys("artists"), "Artists") + "\n\n"
            if processedData.keys("groups"):
                replyString += commentpy.additionalTagsString(processedData.keys("groups"), "Groups") + "\n\n"
            if processedData.keys("languages"):
                replyString += commentpy.additionalTagsString(processedData.keys("languages"), "Languages") + "\n\n"
            if processedData.keys("categories"):
                replyString += commentpy.additionalTagsString(processedData.keys("categories"), "Categories") + "\n\n"
        return replyString


    def getJSON(self, galleryNumber):
        galleryNumber = str(galleryNumber)
        # request = getRequest(galleryNumber) # ['tags'] #
        # Fetch gallery info from cache
        self.database.execute("SELECT last_update, json FROM nhentai WHERE (gallery_number = %s)", [galleryNumber])
        cachedEntry = self.database.fetchone()
        # Use cached entry if new enough (less than 7 days old)
        if cachedEntry and ((datetime.datetime.now() - cachedEntry[0]) // datetime.timedelta(days=7)) < 1:
            return cachedEntry[1]
        request = requests.get(API_URL_NHENTAI+galleryNumber)
        if request == None:
            if cachedEntry:
                return cachedEntry[1]
            else:
                return []
        if request.status_code == 404:
            if cachedEntry:
                return cachedEntry[1]
            else:
                return [404]
        # nhentaiTags = json.loads(re.search(r'(?<=N.gallery\().*(?=\))', request.text).group(0))
        nhentaiTags = request.json()
        if "error" in nhentaiTags:
            return [404]
        if cachedEntry:
            self.database.execute("UPDATE nhentai SET last_update = %s, json = %s WHERE (gallery_number = %s)", (datetime.datetime.now(), request.text, int(galleryNumber)))
        else:
            self.database.execute("INSERT INTO nhentai (gallery_number, last_update, json) VALUES (%s, %s, %s)", (int(galleryNumber), datetime.datetime.now(), request.text))
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
