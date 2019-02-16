import comment
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
    isLoli = False

    requestString = '{"method": "gdata","gidlist": [['+ str(galleryID) + ',' + '"' + galleryToken +'"]],"namespace": 1}'
    ehentaiJSON = requests.post(API_URL_EHENTAI, json=json.loads(requestString)).json()

    if 'gmetadata' in ehentaiJSON:
        title = ehentaiJSON['gmetadata'][0]['title']
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
                isLoli = True
            elif "shotacon" in male:
                isLoli = True

        #TODO actual loli check
    return [title, numberOfPages, category, rating, artist, character, female, group, language, male, parody, misc, isLoli]


def generateReplyString(processedData, galleryNumberAndToken):
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
    isLoli = 12
    replyString = ""

    if processedData:
        if processedData[isLoli]:
            replyString += ">E-Hentai: [REDACTED]\n\n"
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
            replyString += comment.additionalTagsString(processedData[language], "Language", False) + "\n\n"
        if processedData[parody]:
            replyString += comment.additionalTagsString(processedData[parody], "Parody", False) + "\n\n"
        if processedData[character]:
            replyString += comment.additionalTagsString(processedData[character], "Character", False) + "\n\n"
        if processedData[group]:
            replyString += comment.additionalTagsString(processedData[group], "Group", False) + "\n\n"
        if processedData[artist]:
            replyString += comment.additionalTagsString(processedData[artist], "Artist", False) + "\n\n"
        if processedData[male]:
            replyString += comment.additionalTagsString(processedData[male], "Male", False) + "\n\n"
        if processedData[female]:
            replyString += comment.additionalTagsString(processedData[female], "Female", False) + "\n\n"
        if processedData[misc]:
            replyString += comment.additionalTagsString(processedData[misc], "Misc", False) + "\n\n"
    
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