# from https://stackoverflow.com/questions/16981921/relative-imports-in-python-3 to make the imports work when imported as submodule
import os, sys; sys.path.append(os.path.dirname(os.path.realpath(__file__)))
import commentpy
import requests
import json
import re

API_URL_NHENTAI = 'https://nhentai.net/api/gallery/'
API_URL_TSUMINO = 'https://www.tsumino.com/Book/Info/'
API_URL_EHENTAI = "https://api.e-hentai.org/api.php"
LINK_URL_NHENTAI = "https://nhentai.net/g/"
LINK_URL_EHENTAI = "https://e-hentai.org/g/"

def analyseNumber(galleryNumberAndToken):
    galleryID = galleryNumberAndToken[0]
    galleryToken = galleryNumberAndToken[1]
    title = ''
    numberOfPages = 0
    category = ''
    rating = ''
    artist = []
    character = []
    female = []
    group = []
    language = []
    male = []
    parody = []
    misc = []
    isRedacted = False

    requestString = '{"method": "gdata","gidlist": [['+ str(galleryID) + ',' + '"' + galleryToken +'"]],"namespace": 1}'
    ehentaiJSON = requests.post(API_URL_EHENTAI, json=json.loads(requestString)).json()

    if 'gmetadata' in ehentaiJSON:
        title = ehentaiJSON['gmetadata'][0]['title']
        # clean up the title
        title = re.sub(r'\(.*?\)', '', title)
        title = re.sub(r'\[.*?\]', '', title)
        category = ehentaiJSON['gmetadata'][0]['category']
        numberOfPages = ehentaiJSON['gmetadata'][0]['filecount']
        rating = ehentaiJSON['gmetadata'][0]['rating']
        tags = ehentaiJSON['gmetadata'][0]['tags']
        for tag in tags:
        # print(tag)
            if 'artist:' in tag:
                artist.append(re.search(r'(?<=artist:).+', tag).group(0))
            elif 'character:' in tag:
                character.append(re.search(r'(?<=character:).+', tag).group(0))
            elif 'female:' in tag:
                female.append(re.search(r'(?<=female:).+', tag).group(0))
            elif 'group:' in tag:
                group.append(re.search(r'(?<=group:).+', tag).group(0))
            elif 'language:' in tag:
                language.append(re.search(r'(?<=language:).+', tag).group(0))
            elif 'male:' in tag:
                male.append(re.search(r'(?<=male:).+', tag).group(0))
            elif 'parody:' in tag:
                parody.append(re.search(r'(?<=parody:).+', tag).group(0))
            else:
                misc.append(re.search(r'.+', tag).group(0))
            if "lolicon" in female:
                isRedacted = True
            elif "shotacon" in male:
                isRedacted = True

        #TODO actual loli check
    return [title, numberOfPages, category, rating, artist, character, female, group, language, male, parody, misc, isRedacted]


def generateReplyString(processedData, galleryNumberAndToken, censorshipLevel=0, useError=False, generateLink=False):
    # Title
    # number of pages
    # rating
    # language
    # parody
    # character
    # group
    # artist
    # male
    # female
    # misc

    # [title, numberOfPages, category, rating, artist, character, female, group, language, male, parody, misc]
    title = 0
    numberOfPages = 1
    category = 2
    rating = 3
    artist = 4
    character = 5
    female = 6
    group = 7
    language = 8
    male = 9
    parody = 10
    misc = 11
    isRedacted = 12
    replyString = ""

    if processedData:
        #Censorship engine
        if processedData[isRedacted]:
            if censorshipLevel > 5:
                return ""
            #Level 2
            if censorshipLevel > 1:
                if processedData[title]:
                    processedData[title] = "[REDACTED]"
                if processedData[artist]:
                    processedData[artist] = ["[REDACTED]" for element in processedData[artist]]
                if processedData[group]:
                    processedData[group] = ["[REDACTED]" for element in processedData[group]]
            #Level 3
            if censorshipLevel > 2:
                if processedData[parody]:
                    processedData[parody] = ["[REDACTED]" for element in processedData[parody]]
                if processedData[character]:
                    processedData[character] = ["[REDACTED]" for element in processedData[character]]
            #Level 4
            if censorshipLevel > 3:
                if processedData[male]:
                    processedData[male] = ["[REDACTED]" if "shota" not in element else element for element in processedData[male]]
                if processedData[female]:
                    processedData[female] = ["[REDACTED]" if "loli" not in element else element for element in processedData[female]]
                if processedData[misc]:
                    processedData[misc] = ["[REDACTED]" for element in processedData[misc]]
            #Level 5
            if censorshipLevel > 4:
                if processedData[numberOfPages]:
                    processedData[numberOfPages] = "[REDACTED]"
                if processedData[rating]:
                    processedData[rating] = "[REDACTED]"
                if processedData[category]:
                    processedData[category] = "[REDACTED]"
                if processedData[language]:
                    processedData[language] = "[REDACTED]"

        if processedData[isRedacted]:
            if censorshipLevel > 0:
                replyString += ">E-Hentai: [REDACTED]\n\n"
            else:
                replyString += f">E-Hentai: {galleryNumberAndToken[0]}/{galleryNumberAndToken[1]}&#32;\n\n"
                if useError:
                    replyString += f"{commentpy.generate450string('E-Hentai')}\n\n"
                    return replyString
        elif generateLink:
            replyString += f">E-Hentai: [{galleryNumberAndToken[0]}/{galleryNumberAndToken[1]}]({LINK_URL_EHENTAI}{galleryNumberAndToken[0]}/{galleryNumberAndToken[1]})\n\n"
        else:
            replyString += ">E-Hentai: " + str(galleryNumberAndToken[0]) + "/" + str(galleryNumberAndToken[1]) + "\n\n"
        if processedData[title]:
            replyString += "**Title**: " + processedData[title] + "\n\n"
        replyString += "**Number of pages**: " + str(processedData[numberOfPages]) + "\n\n"
        if processedData[rating]:
            replyString += "**Rating**: " + str(processedData[rating]) + "\n\n"
        if processedData[category]:
            replyString += "**Category**: " + processedData[category] + "\n\n"

        if processedData[language]:
            replyString += commentpy.additionalTagsString(processedData[language], "Language", False) + "\n\n"
        if processedData[parody]:
            replyString += commentpy.additionalTagsString(processedData[parody], "Parody", False) + "\n\n"
        if processedData[character]:
            replyString += commentpy.additionalTagsString(processedData[character], "Character", False) + "\n\n"
        if processedData[group]:
            replyString += commentpy.additionalTagsString(processedData[group], "Group", False) + "\n\n"
        if processedData[artist]:
            replyString += commentpy.additionalTagsString(processedData[artist], "Artist", False) + "\n\n"
        if processedData[male]:
            replyString += commentpy.additionalTagsString(processedData[male], "Male", False) + "\n\n"
        if processedData[female]:
            replyString += commentpy.additionalTagsString(processedData[female], "Female", False) + "\n\n"
        if processedData[misc]:
            replyString += commentpy.additionalTagsString(processedData[misc], "Misc", False) + "\n\n"
    
    return replyString


def getNumbers(comment):
    numbers = []
    candidates = re.findall(r'(?<=\})\d{1,8}\/\w*?(?=\{)', comment)
    try:
        for entry in candidates:
            galleryID = int(re.search(r'\d+(?=\/)', entry).group(0))
            galleryToken = re.search(r'(?<=\/)\w+', entry).group(0)
            numbers.append([galleryID, galleryToken])
    except AttributeError:
        print("Number Recognition failed Ehentai")
    return numbers

def scanURL(comment):
    ehentaiNumbers = []
    # having two sites makes getting the url more than with the others.
    ehentaiLinks = re.findall(r'https?:\/\/(?:www.)?e-hentai.org\/g\/\d{1,8}\/\w*', comment)
    ehentaiLinks += re.findall(r'https?:\/\/(?:www.)?exhentai.org\/g\/\d{1,8}\/\w*', comment)
    try:
        for link in ehentaiLinks:
            # split the URL into the gallery number and token.
            removeURL = re.search(r'(?<=\/g\/).+', link).group(0)
            galleryID = int(re.search(r'\d+(?=\/)', removeURL).group(0))
            galleryToken = re.search(r'(?<=\/)\w+', removeURL).group(0)
            ehentaiNumbers.append([galleryID,galleryToken])
    except AttributeError:
        print("no ehentaiLinks")
    except ValueError:
        ehentaiNumbers = []
    # again the two sites along with the page url and token
    ehentaiPageLinks = re.findall(r'https?:\/\/(?:www.)?e-hentai.org\/s\/\w*\/\d{1,8}-\d{1,4}', comment)
    ehentaiPageLinks += re.findall(r'https?:\/\/(?:www.)?exhentai.org\/s\/\w*\/\d{1,8}-\d{1,4}', comment)
    # get all the gallery info from the page number and token
    # TODO condense multiple entries into a single request.
    try:
        for link in ehentaiPageLinks:
            removeURL = re.search(r'(?<=\/s\/).+', link).group(0)
            galleryID = re.search(r'(?<=\/)\d+(?=-)', removeURL).group(0)
            pageToken = re.search(r'\w+', removeURL).group(0)
            page = re.search(r'(?<=-)\d+', removeURL).group(0)

            resquestStringPage = '{"method": "gtoken","pagelist": [[' + galleryID +',"' + pageToken + '",' + page + ']]}'
            ehentaiJSONpage = requests.post(API_URL_EHENTAI, json=json.loads(resquestStringPage)).json()
            if 'tokenlist' in ehentaiJSONpage:
                galleryToken = ehentaiJSONpage['tokenlist'][0]['token']
                ehentaiNumbers.append([galleryID, galleryToken])
    except AttributeError:
        print("no ehentai page Links")
    ehentaiNumbers = commentpy.removeDupes2(ehentaiNumbers)
    return ehentaiNumbers