# from https://stackoverflow.com/questions/16981921/relative-imports-in-python-3 to make the imports work when imported as submodule
import os, sys; sys.path.append(os.path.dirname(os.path.realpath(__file__)))
import commentpy
import requests
import json
import re
import datetime

# from DBConn import Database

API_URL_EHENTAI = "https://api.e-hentai.org/api.php"
LINK_URL_EHENTAI = "https://e-hentai.org/g/"

class Ehentai():
    def __init__(self, database):
        self.database = database

    def analyseNumber(self, galleryNumberAndToken):
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

        ehentaiJSON = self.getJSON(galleryNumberAndToken)
        # requestString = '{"method": "gdata","gidlist": [['+ str(galleryID) + ',' + '"' + galleryToken +'"]],"namespace": 1}'
        # ehentaiJSON = requests.post(API_URL_EHENTAI, json=json.loads(requestString)).json()

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

        return {
            "title": title, 
            "numberOfPages": numberOfPages, 
            "category": category, 
            "rating": rating, 
            "artist": artist,
            "character": character, 
            "female": female, 
            "group": group, 
            "language": language, 
            "male": male, 
            "parody": parody, 
            "misc": misc,
            "isRedacted": isRedacted

        }

    def generateLinks(self, number):
        tags = self.analyseNumber(number)
        if tags.get('isRedacted'):
            return "This number contains restricted tags and therefore cannot be linked"
        if len(tags) > 1:
            return LINK_URL_EHENTAI + str(number[0]) + "/" + number[1]

    def generateReplyString(self, processedData, galleryNumberAndToken, censorshipLevel=0, useError=False, generateLink=False):
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
        replyString = ""

        if processedData:
            #Censorship engine
            if processedData.get("isRedacted"):
                if censorshipLevel > 5:
                    return ""
                #Level 2
                if censorshipLevel > 1:
                    if processedData.get("title"):
                        processedData["title"] = "[REDACTED]"
                    if processedData.get("artist"):
                        processedData["artist"] = ["[REDACTED]" for element in processedData.get("artist")]
                    if processedData.get("group"):
                        processedData["group"] = ["[REDACTED]" for element in processedData.get("group")]
                #Level 3
                if censorshipLevel > 2:
                    if processedData.get("parody"):
                        processedData["parody"] = ["[REDACTED]" for element in processedData.get("parody")]
                    if processedData.get("character"):
                        processedData["character"] = ["[REDACTED]" for element in processedData.get("character")]
                #Level 4
                if censorshipLevel > 3:
                    if processedData.get("male"):
                        processedData["male"] = ["[REDACTED]" if "shota" not in element else element for element in processedData.get("male")]
                    if processedData.get("female"):
                        processedData["female"] = ["[REDACTED]" if "loli" not in element else element for element in processedData.get("female")]
                    if processedData.get("misc"):
                        processedData["misc"] = ["[REDACTED]" for element in processedData.get("misc")]
                #Level 5
                if censorshipLevel > 4:
                    if processedData.get("numberOfPages"):
                        processedData["numberOfPages"] = "[REDACTED]"
                    if processedData.get("rating"):
                        processedData["rating"] = "[REDACTED]"
                    if processedData.get("category"):
                        processedData["category"] = "[REDACTED]"
                    if processedData.get("language"):
                        processedData["language"] = "[REDACTED]"

            if processedData.get("isRedacted"):
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
                replyString += f">E-Hentai: {galleryNumberAndToken[0]}/{galleryNumberAndToken[1]}\n\n"
            if processedData.get("title"):
                replyString += f"**Title**: {processedData.get('title')}\n\n"
            replyString += f"**Number of pages**: {processedData.get('numberOfPages')}\n\n"
            if processedData.get("rating"):
                replyString += f"**Rating**: {processedData.get('rating')}\n\n"
            if processedData.get("category"):
                replyString += f"**Category**: {processedData.get('category')}\n\n"

            if processedData.get("language"):
                replyString += commentpy.additionalTagsString(processedData.get("language"), "Language", False) + "\n\n"
            if processedData.get("parody"):
                replyString += commentpy.additionalTagsString(processedData.get("parody"), "Parody", False) + "\n\n"
            if processedData.get("character"):
                replyString += commentpy.additionalTagsString(processedData.get("character"), "Character", False) + "\n\n"
            if processedData.get("group"):
                replyString += commentpy.additionalTagsString(processedData.get("group"), "Group", False) + "\n\n"
            if processedData.get("artist"):
                replyString += commentpy.additionalTagsString(processedData.get("artist"), "Artist", False) + "\n\n"
            if processedData.get("male"):
                replyString += commentpy.additionalTagsString(processedData.get("male"), "Male", False) + "\n\n"
            if processedData.get("female"):
                replyString += commentpy.additionalTagsString(processedData.get("female"), "Female", False) + "\n\n"
            if processedData.get("misc"):
                replyString += commentpy.additionalTagsString(processedData.get("misc"), "Misc", False) + "\n\n"
        
        return replyString


    def getJSON(self, galleryNumberAndToken):
        galleryID = galleryNumberAndToken[0]
        galleryToken = galleryNumberAndToken[1]
        self.database.execute("SELECT last_update, json FROM ehentai WHERE (gallery_number = %s AND token = %s)", (galleryID, galleryToken))
        cachedEntry = self.database.fetchone()
        if cachedEntry and ((datetime.datetime.utcnow() - cachedEntry[0]) // datetime.timedelta(days=7)) < 1:
            return cachedEntry[1]
        requestString = f'{{"method": "gdata","gidlist": [[{galleryID},"{galleryToken}"]],"namespace": 1}}'
        ehentaiResponse = requests.post(API_URL_EHENTAI, json=json.loads(requestString))
        if ehentaiResponse.status_code == 200:
            if cachedEntry:
                self.database.execute("UPDATE ehentai SET last_update = %s, json = %s WHERE (gallery_number = %s AND token = %s)", (datetime.datetime.utcnow(), ehentaiResponse.text, galleryID, galleryToken))
            else:
                self.database.execute("INSERT INTO ehentai (gallery_number, token, last_update, json) VALUES (%s, %s, %s, %s)", (galleryID, galleryToken, datetime.datetime.utcnow(), ehentaiResponse.text))
        self.database.commit()
        return ehentaiResponse.json()

    def getNumbers(self, comment):
        numbers = []
        candidates = re.findall(r'(?<=\})\d{1,8}\/\w*?(?=\{)', comment)
        try:
            for entry in candidates:
                galleryID = int(re.search(r'\d+(?=\/)', entry).group(0))
                galleryToken = re.search(r'(?<=\/)\w+', entry).group(0)
                numbers.append([galleryID, galleryToken])
        except AttributeError:
            pass
        return [{'number': number, 'type': 'ehentai'} for number in numbers]


    def remove_and_return_old_results_from_comment(self, comment):
        ehentaiNumbers = []
        ehentaiNumbersCandidates = re.findall(r'(?<=>E-Hentai: )\d{1,8}\/\w*', comment)
        try:
            for entry in ehentaiNumbersCandidates:
                galleryID = int(re.search(r'\d+(?=\/)', entry).group(0))
                galleryToken = re.search(r'(?<=\/)\w+', entry).group(0)
                ehentaiNumbers.append([galleryID, galleryToken])
        except AttributeError:
            print("Number Recognition failed Ehentai")
        comment = re.sub(r'(?<=>E-Hentai: )\d{1,8}\/\w*', '', comment)
        return [{'number': number, 'type': 'ehentai'} for number in ehentaiNumbers], comment


    def scanURL(self, comment):
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
            pass
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
            pass
        ehentaiNumbers = commentpy.removeDupes2(ehentaiNumbers)
        return [{'number': number, 'type': 'ehentai'} for number in ehentaiNumbers]