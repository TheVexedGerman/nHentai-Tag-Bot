# from https://stackoverflow.com/questions/16981921/relative-imports-in-python-3 to make the imports work when imported as submodule
import os, sys; sys.path.append(os.path.dirname(os.path.realpath(__file__)))
import commentpy
import requests
import json
import re
import time

API_URL_NHENTAI = 'https://nhentai.net/api/gallery/'
API_URL_TSUMINO = 'https://www.tsumino.com/Book/Info/'
API_URL_EHENTAI = "https://api.e-hentai.org/api.php"
LINK_URL_NHENTAI = "https://nhentai.net/g/"
LINK_URL_EHENTAI = "https://e-hentai.org/g/"

def analyseNumber(galleryNumber):
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
    rawData = getJSON(galleryNumber)
    if rawData == [404]:
        return rawData
    if rawData:
        # print(rawData)
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
            for entry in listOfTags:
                if 'lolicon' in entry[0]:
                    isRedacted = True
                elif 'shotacon' in entry[0]:
                    isRedacted = True

    processedData = [title, numberOfPages, listOfTags, languages, artists, categories, parodies, characters, groups, isRedacted]
    # Sort the tags by descending popularity to imitate website behavior
    i = 0
    for tagList in processedData:
        if i > 1 and i < 9:
            processedData[i] = sorted(tagList, key=lambda tags: tags[1], reverse=True)
        i += 1
    # print(processedData)
    return processedData

def generateReplyString(processedData, galleryNumber, censorshipLevel=0, useError=False, generateLink=False):
    # parodies
    # characters
    # tags
    # artists
    # groups
    # languages
    # categories
    title = 0
    numberOfPages = 1
    listOfTags = 2
    languages = 3
    artists = 4
    categories = 5
    parodies = 6
    characters = 7
    groups = 8
    isRedacted = 9
    replyString = ""
    if processedData[0] == 404:
        replyString += ">" + str(galleryNumber).zfill(5) + "\n\n"
        replyString += "nHentai returned 404 for this number. The gallery has either been removed or doesn't exist yet.\n\n"
        return replyString
    if processedData[title]:
        #Censorship engine
        if processedData[isRedacted]:
            if censorshipLevel > 5:
                return ""
            #Level 2
            if censorshipLevel > 1:
                processedData[title] = "[REDACTED]"
                if processedData[artists]:
                    for element in processedData[artists]:
                        element[0] = "[REDACTED]"
                if processedData[groups]:
                    for element in processedData[groups]:
                        element[0] = "[REDACTED]"
            #Level 3
            if censorshipLevel > 2:
                if processedData[characters]:
                    for element in processedData[characters]:
                        element[0] = "[REDACTED]"
                if processedData[parodies]:
                    for element in processedData[parodies]:
                        element[0] = "[REDACTED]"
            #Level 4
            if censorshipLevel > 3:
                if processedData[listOfTags]:
                    for element in processedData[listOfTags]:
                        if not any(tag in element[0] for tag in ['loli','shota']):
                            element[0] = "[REDACTED]"
            #Level 5
            if censorshipLevel > 4:
                if processedData[languages]:
                    for element in processedData[languages]:
                        element[0] = "[REDACTED]"
                if processedData[categories]:
                    for element in processedData[categories]:
                        element[0] = "[REDACTED]"
                processedData[numberOfPages] = "[REDACTED]"
        if processedData[isRedacted]:
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

        replyString += "**Title**: " + processedData[title] + "\n\n"
        replyString += "**Number of pages**: " + str(processedData[numberOfPages]) + "\n\n"
        
        if processedData[characters]:
            replyString += commentpy.additionalTagsString(processedData[characters], "Characters") + "\n\n"
        if processedData[parodies]:
            replyString += commentpy.additionalTagsString(processedData[parodies], "Parodies") + "\n\n"
        if processedData[listOfTags]:
            replyString += commentpy.additionalTagsString(processedData[listOfTags], "Tags") + "\n\n"
        if processedData[artists]:
            replyString += commentpy.additionalTagsString(processedData[artists], "Artists") + "\n\n"
        if processedData[groups]:
            replyString += commentpy.additionalTagsString(processedData[groups], "Groups") + "\n\n"
        if processedData[languages]:
            replyString += commentpy.additionalTagsString(processedData[languages], "Languages") + "\n\n"
        if processedData[categories]:
            replyString += commentpy.additionalTagsString(processedData[categories], "Categories") + "\n\n"
    # print (replyString)
    return replyString


def getJSON(galleryNumber):
    galleryNumber = str(galleryNumber)
    request = getRequest(galleryNumber) # ['tags'] #
    if request == None:
        return []
    if request.status_code == 404:
        return [404]
    nhentaiTags = json.loads(re.search(r'(?<=N.gallery\().*(?=\))', request.text).group(0))
    # nhentaiTags = request.json()
    if "error" in nhentaiTags:
        return []
    else:
        return nhentaiTags


def getRequest(galleryNumber):
    for i in range(1, 5):
        request = requests.get(LINK_URL_NHENTAI+galleryNumber) # ['tags'] #
        if request.status_code == 200 or request.status_code == 404:
            return request
        time.sleep(i)
    return None

def getNumbers(comment):
    numbers = re.findall(r'(?<=\()\d{5,6}(?=\))', comment)
    try:
        numbers = [int(number) for number in numbers]
    except ValueError:
        numbers = []
    numbers = commentpy.removeDuplicates(numbers)
    return numbers


def scanURL(comment):
    nhentaiNumbers = []
    nhentaiLinks = re.findall(r'https?:\/\/(?:www.)?nhentai.net\/g\/\d{1,6}', comment)
    print(nhentaiLinks)
    try:
        nhentaiNumbers = [re.search(r'\d+', link).group(0) for link in nhentaiLinks]
    except AttributeError:
        print("No nHentai links")
    try:
        nhentaiNumbers = [int(number) for number in nhentaiNumbers]
    except ValueError:
        nhentaiNumbers = []
    nhentaiNumbers = commentpy.removeDuplicates(nhentaiNumbers)
    return nhentaiNumbers