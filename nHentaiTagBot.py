import requests
import json
import os
import praw
import re
import time
import datetime
from bs4 import BeautifulSoup

API_URL_NHENTAI = 'https://nhentai.net/api/gallery/'
API_URL_TSUMINO = 'https://www.tsumino.com/Book/Info/'
API_URL_EHENTAI = "https://api.e-hentai.org/api.php"
LINK_URL_NHENTAI = "https://nhentai.net/g/"

TIME_BETWEEN_PM_CHECKS = 60  # in seconds

PARSED_SUBREDDIT = 'Animemes+hentai_irl+anime_irl+u_Loli-Tag-Bot+u_nHentai-Tag-Bot+HentaiSource'
# PARSED_SUBREDDIT = 'loli_tag_bot'

messagesRepliedTo = []

def addFooter():
    # Needs to use ASCII code to not break reddit formatting &#32; is space &#40; is ( and &#41; is )
    return "---\n\n^&#40;nHentai&#41;,&#32;&#41;Tsumino&#40;&#32;|&#32;min&#32;5&#32;digits&#32;|&#32;[Q&A](https://www.reddit.com/user/nHentai-Tag-Bot/comments/9r2swv/how_to_use_the_bot/)&#32;|&#32;[Contact](https://www.reddit.com/message/compose/?to=thevexedgerman&subject=[nHentai-Bot])&#32;|&#32;[Source](https://github.com/TheVexedGerman/nHentai-Tag-Bot)"


def additionalTagsString(entries, initialText, isNhentai=True):
    first = True
    replyString = ""
    if isNhentai:
        for entry in entries:
            if first:
                replyString += "**" + initialText + "**: " + entry[0] + " (" + format(entry[1], ',d') + ")"
                first = False
            else:
                replyString += ", " + entry[0] + " (" + format(entry[1], ',d') + ")"
    else:
        for entry in entries:
            if first:
                replyString += "**" + initialText + "**: " + entry
                first = False
            else:
                replyString += ", " + entry
    return replyString


def analyseNumberNhentai(galleryNumber):
    title = ''
    numberOfPages = 0
    listOfTags = []
    languages = []
    artists = []
    categories = []
    parodies = []
    characters = []
    groups = []
    rawData = getJSON(galleryNumber)
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

    processedData = [title, numberOfPages, listOfTags, languages, artists, categories, parodies, characters, groups]
    # Sort the tags by descending popularity to imitate website behavior
    i = 0
    for tagList in processedData:
        if i > 1:
            processedData[i] = sorted(tagList, key=lambda tags: tags[1], reverse=True)
        i += 1
    # print(processedData)
    return processedData


def analyseNumberTsumino(galleryNumber):
    title = ''
    numberOfPages = 0
    rating = ''
    category = []
    group = []
    artist = []
    parody = []
    tag = []
    collection = []

    response = requests.get(API_URL_TSUMINO+str(galleryNumber))
    print(response)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, features="html.parser")
        # title finder
        try:
            title = soup.find('div', id="Title").string.replace('\n','')
            print(title)
        except:
            print("No Title")

        # pages finder
        try:
            numberOfPages = soup.find('div', id="Pages").string.replace('\n','')
            print(numberOfPages)
        except:
            print("No Pages")

        # rating finder
        try:
            rating = soup.find('div', id="Rating").string.replace('\n','')
            print(rating)
        except:
            print("No Rating")

        # category finder
        try:
            category = [a.get('data-define') for a in soup.find('div', id="Category").findAll('a')]
            print(category)
        except:
            print("No Category")

        # group finder
        try:
            group = [a.get('data-define') for a in soup.find('div', id="Group").findAll('a')]
            print(group)
        except:
            print("No Group")

        # artist finder
        try:
            artist = [a.get('data-define') for a in soup.find('div', id="Artist").findAll('a')]
            print(artist)
        except:
            print("No Artist")

        # collection finder
        try:
            collection = [a.get('data-define') for a in soup.find('div', id="Collection").findAll('a')]
            print(collection)
        except:
            print("No Collection")

        # parody finder
        try:
            parody = [a.get('data-define') for a in soup.find('div', id="Parody").findAll('a')]
            print(parody)
        except:
            print("No Parody")

        # character finder
        try:
            character = [a.get('data-define') for a in soup.find('div', id="Character").findAll('a')]
            print(character)
        except:
            print("No Character")

        # tag finder
        try:
            tag = [a.get('data-define') for a in soup.find('div', id="Tag").findAll('a')]
            print(tag)
        except:
            print("No Tags")

        return [title, numberOfPages, rating, category, group, artist, parody, tag, collection]
    else:
        return []


def analyseNumberEhentai(galleryNumberAndToken):
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
    return [title, numberOfPages, category, rating, artist, character, female, group, language, male, parody, misc]


def authenticate():
    print("Authenticating...")
    reddit = praw.Reddit(
        'nhentaibot'
        # 'thevexedgermanbot'
    )
    print("Authenticated as {}".format(reddit.user.me()))
    return reddit


def runBot(reddit):
    lastCheckedPMsTime = time.time()
    for comment in reddit.subreddit(PARSED_SUBREDDIT).stream.comments():
        if comment:
            if (time.time() - lastCheckedPMsTime) > TIME_BETWEEN_PM_CHECKS:
                processPMs(reddit)
                lastCheckedPMsTime = time.time()
            print(comment.body)
            processComment(comment)


def writeCommentReply(replyString, comment):
    print("Commenting with: \n")
    print(replyString)
    # post the replyString to reddit as a reply
    for attempt in range(2):
        try:
            print("Attempt: " + str(attempt))
            comment.reply(replyString)
            print("Post successful")
            # also write it to file to enable reloading after shutdown
            with open("messagesRepliedTo.txt", "a") as f:
                f.write(comment.id + "\n")
        # from Roboragi, but praw doesn't seem to be found
        except praw.errors.Forbidden:
                print('Request from banned subreddit: {0}\n'.format(comment.subreddit))
        # extrapolated from errors, maybe better?
        except prawcore.exceptions.Forbidden:
            print("unable to post")
        except:
            print("Post unsuccessful")
        else:
            break
    # save the replied to comment to not analyse and reply again
    return comment.id


def main():
    global reddit
    reddit = authenticate()
    global messagesRepliedTo
    messagesRepliedTo = getSavedMessages()
    while True:
        runBot(reddit)


def generateReplyStringNhentai(processedData, galleryNumber):
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
    replyString = ""

    if processedData[title]:
        if galleryNumber >= 10000:
            replyString += ">" + str(galleryNumber) + "\n\n"
        else:
            replyString += ">" + str(galleryNumber).zfill(5) + "\n\n"
        replyString += "**Title**: " + processedData[title] + "\n\n"
        replyString += "**Number of pages**: " + str(processedData[numberOfPages]) + "\n\n"
        
        if processedData[characters]:
            replyString += additionalTagsString(processedData[characters], "Characters") + "\n\n"
        if processedData[parodies]:
            replyString += additionalTagsString(processedData[parodies], "Parodies") + "\n\n"
        if processedData[listOfTags]:
            replyString += additionalTagsString(processedData[listOfTags], "Tags") + "\n\n"
        if processedData[artists]:
            replyString += additionalTagsString(processedData[artists], "Artists") + "\n\n"
        if processedData[groups]:
            replyString += additionalTagsString(processedData[groups], "Groups") + "\n\n"
        if processedData[languages]:
            replyString += additionalTagsString(processedData[languages], "Languages") + "\n\n"
        if processedData[categories]:
            replyString += additionalTagsString(processedData[categories], "Categories") + "\n\n"
    # print (replyString)
    return replyString


def generateReplyStringTsumino(processedData, galleryNumber):
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
    # [title, numberOfPages, rating, category, group, artist, parody, tag, collection]
    title = 0
    pages = 1
    rating = 2
    category = 3
    group = 4
    artist = 5
    parody = 6
    tag = 7
    collection = 8
    replyString = ""
    print("Tsumino replyStringGenerator Start")

    if processedData:
        replyString += ">Tsumino: " + str(galleryNumber).zfill(5) + "\n\n"
        if processedData[title]:
            replyString += "**Title**: " + processedData[title] + "\n\n"
        replyString += "**Number of pages**: " + str(processedData[pages]) + "\n\n"
        if processedData[rating]:
            replyString += "**Rating**: " + processedData[rating] + "\n\n"

        if processedData[category]:
            replyString += additionalTagsString(processedData[category], "Category", False) + "\n\n"
        if processedData[group]:
            replyString += additionalTagsString(processedData[group], "Group", False) + "\n\n"
        if processedData[collection]:
            replyString += additionalTagsString(processedData[collection], "Collection", False) + "\n\n"
        if processedData[artist]:
            replyString += additionalTagsString(processedData[artist], "Artist", False) + "\n\n"
        if processedData[parody]:
            replyString += additionalTagsString(processedData[parody], "Parody", False) + "\n\n"
        if processedData[tag]:
            replyString += additionalTagsString(processedData[tag], "Tag", False) + "\n\n"
    print("Tsumino replyStringGenerator End")
    return replyString


def generateReplyStringEhentai(processedData, galleryNumberAndToken):
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
    replyString = ""

    if processedData:
        replyString += "E-Hentai: " + str(galleryNumberAndToken[0]) + "/" + str(galleryNumberAndToken[1]) + "\n\n"
        if processedData[title]:
            replyString += "**Title**: " + processedData[title] + "\n\n"
        replyString += "**Number of pages**: " + str(processedData[numberOfPages]) + "\n\n"
        if processedData[rating]:
            replyString += "**Rating**: " + str(processedData[rating]) + "\n\n"
        
        if processedData[language]:
            replyString += additionalTagsString(processedData[language], "Language", False) + "\n\n"
        if processedData[parody]:
            replyString += additionalTagsString(processedData[parody], "Parody", False) + "\n\n"
        if processedData[character]:
            replyString += additionalTagsString(processedData[character], "Character", False) + "\n\n"
        if processedData[group]:
            replyString += additionalTagsString(processedData[group], "Group", False) + "\n\n"
        if processedData[artist]:
            replyString += additionalTagsString(processedData[artist], "Artist", False) + "\n\n"
        if processedData[male]:
            replyString += additionalTagsString(processedData[male], "Male", False) + "\n\n"
        if processedData[female]:
            replyString += additionalTagsString(processedData[female], "Female", False) + "\n\n"
        if processedData[misc]:
            replyString += additionalTagsString(processedData[misc], "Misc", False) + "\n\n"
    
    return replyString


def getJSON(galleryNumber):
    if galleryNumber < 300000:
        galleryNumber = str(galleryNumber)
        nhentaiTags = requests.get(API_URL_NHENTAI+galleryNumber).json() # ['tags'] #
        if "error" in nhentaiTags:
            return []
        else:
            return nhentaiTags
    else:
        return []


def getNhentaiNumber(comment):
    numbers = re.findall(r'(?<=\()\d{5,6}(?=\))', comment)
    try:
        numbers = [int(number) for number in numbers]
    except ValueError:
        numbers = []
    numbers = removeDuplicates(numbers)
    return numbers


def getNumbers(comment):
    numbersCombi = []
    numbersCombi = keyWordDetection(comment)
    if not numbersCombi:
        nhentaiNumbers = getNhentaiNumber(comment.body)
        tsuminoNumbers = getTsuminoNumbers(comment.body)
        #TODO regular, parentheses based search
        ehentaiNumbers = []
        numbersCombi = [nhentaiNumbers, tsuminoNumbers, ehentaiNumbers]
    return numbersCombi


def keyWordDetection(comment):
    foundNumbers = []
    if "!tags" in comment.body.lower():
        foundNumbers = scanForURL(comment.body)
        if not foundNumbers:
            parent = comment.parent_id
            commentParent = re.findall(r'(?<=t1_).*', parent)
            if commentParent:
                comment = reddit.comment(commentParent[0])
                foundNumbers = scanForURL(comment.body)
    return foundNumbers


def scanForURL(comment):
    nhentaiNumbers = []
    tsuminoNumbers = []
    ehentaiNumbers = []

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
    nhentaiNumbers = removeDuplicates(nhentaiNumbers)

    commentLower = comment.lower()
    tsuminoLinks = re.findall(r'https?:\/\/(?:www.)?tsumino.com\/book\/info\/\d{1,5}', commentLower)
    tsuminoLinks += re.findall(r'https?:\/\/(?:www.)?tsumino.com\/read\/view\/\d{1,5}', commentLower)
    try:
        tsuminoNumbers = [re.search(r'\d+', link).group(0) for link in tsuminoLinks]
    except AttributeError:
        print("No Tsumino links")
    try:
        tsuminoNumbers = [int(number) for number in tsuminoNumbers]
    except ValueError:
        tsuminoNumbers = []
    tsuminoNumbers = removeDuplicates(tsuminoNumbers)

    ehentaiLinks = re.findall(r'https?:\/\/(?:www.)?e-hentai.org\/g\/\d{1,8}\/\w*', comment)
    ehentaiLinks = re.findall(r'https?:\/\/(?:www.)?exhentai.org\/g\/\d{1,8}\/\w*', comment)
    try:
        for link in ehentaiLinks:
            removeURL = re.search(r'(?<=\/g\/).+', link).group(0)
            galleryID = int(re.search(r'\d+(?=\/)', removeURL).group(0))
            galleryToken = re.search(r'(?<=\/)\w+', removeURL).group(0)
            ehentaiNumbers.append([galleryID,galleryToken])
    except AttributeError:
        print("no ehentaiLinks")
    except ValueError:
        ehentaiNumbers = []
    ehentaiPageLinks = re.findall(r'https?:\/\/(?:www.)?e-hentai.org\/s\/\w*\/\d{1,8}-\d{1,4}', comment)
    ehentaiPageLinks += re.findall(r'https?:\/\/(?:www.)?exhentai.org\/s\/\w*\/\d{1,8}-\d{1,4}', comment)
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
    ehentaiNumbers = removeDupes2(ehentaiNumbers)

    if nhentaiNumbers or tsuminoNumbers or ehentaiNumbers:
        print("true return")
        return [nhentaiNumbers, tsuminoNumbers, ehentaiNumbers]
    return []


def getTsuminoNumbers(comment):
    numbers = re.findall(r'(?<=\))\d{5}(?=\()', comment)
    try:
        numbers = [int(number) for number in numbers]
    except ValueError:
        numbers = []
    numbers = removeDuplicates(numbers)
    return numbers


def getSavedMessages():
    # return an empty list if empty
    if not os.path.isfile("messagesRepliedTo.txt"):
        messagesRepliedTo = []
    else:
        with open("messagesRepliedTo.txt", "r") as f:
            # updated read file method from https://stackoverflow.com/questions/3925614/how-do-you-read-a-file-into-a-list-in-python
            messagesRepliedTo = f.read().splitlines()

    return messagesRepliedTo


def processComment(comment):
    if comment.id not in messagesRepliedTo:
        replyString = ""
        nhentai = 0
        tsumino = 1
        ehentai = 2
        numbersCombi = getNumbers(comment)
        if numbersCombi:
            #TODO combine and condense this, since most is redundant
            if numbersCombi[nhentai]:
                numbers = numbersCombi[nhentai]
                if len(numbers) > 5:
                    replyString += "This bot does a maximum of 5 numbers at a time, your list has been shortened:\n\n"
                numbers = numbers[:5]
                for number in numbers:
                    if replyString:
                        replyString += "&#x200B;\n\n"
                    processedData = analyseNumberNhentai(number)
                    replyString += generateReplyStringNhentai(processedData, number)
            if numbersCombi[tsumino]:
                numbers = numbersCombi[tsumino]
                if len(numbers) > 5:
                    replyString += "This bot does a maximum of 5 numbers at a time, your list has been shortened:\n\n"
                numbers = numbers[:5]
                for number in numbers:
                    if replyString:
                        replyString += "&#x200B;\n\n"
                    processedData = analyseNumberTsumino(number)
                    replyString += generateReplyStringTsumino(processedData, number)
            if numbersCombi[ehentai]:
                numbers = numbersCombi[ehentai]
                if len(numbers) > 5:
                    replyString += "This bot does a maximum of 5 numbers at a time, your list has been shortened:\n\n"
                numbers = numbers[:5]
                for number in numbers:
                    if replyString:
                        replyString += "&#x200B;\n\n"
                    processedData = analyseNumberEhentai(number)
                    replyString += generateReplyStringEhentai(processedData, number)
        if replyString:
            replyString += addFooter()
            messagesRepliedTo.append(writeCommentReply(replyString, comment))
        # required for message reply mark read
        return True


def processPMs(reddit):
    print("Current time: " + str(datetime.datetime.now().time()))
    #Adapted from Roboragi
    for message in reddit.inbox.unread(limit=None):
        usernameMention = message.subject == 'username mention'
        usernameInBody = message.subject == 'comment reply' and "u/nhentai-tag-bot" in message.body.lower()
        linkMessage = message.subject == "[Link]" or message.subject == "re: [Link]"

        # This PM doesn't meet the response criteria. Skip it.
        if not (usernameMention or usernameInBody):
            if linkMessage:
                scanPM(message)
            continue

        try:
            mentionedComment = reddit.comment(message.id)
            mentionedComment.refresh()
            print(mentionedComment.body)
            if processComment(mentionedComment):
                message.mark_read()
        except:
            break


# taken from https://stackoverflow.com/questions/480214/how-do-you-remove-duplicates-from-a-list-whilst-preserving-order
def removeDuplicates(seq):
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]

# taken from https://stackoverflow.com/questions/6764909/python-how-to-remove-all-duplicate-items-from-a-list since the other one can't do nested lists
def removeDupes2(X):
    unique_X = []
    for i, row in enumerate(X):
        if row not in X[i + 1:]:
            unique_X.append(row)
    return unique_X


def generateLinkString(numbersCombi):
    #generate the string that will be replied
    nhentai = 0
    tsumino = 1
    linkString = ""
    if numbersCombi:
        if numbersCombi[nhentai]:
            numbers = numbersCombi[nhentai]
            for number in numbers:
                linkString += generateLinks(number) + "\n\n"
        if numbersCombi[tsumino]:
            numbers = numbersCombi[tsumino]
            for number in numbers:
                linkString += generateLinks(number, False) + "\n\n"
    return linkString


def generateLinks(number, isNhentai=True):
    # make the link
    linkString = ""
    if isNhentai:
        linkString = LINK_URL_NHENTAI + str(number)
    else:
        # Since Tsumino is just being HTML parsed the API URL is fine
        linkString = API_URL_TSUMINO + str(number)
    return linkString


def scanPM(message):
    linkString = ""
    numbersCombi = getNumbers(message)
    numberOfInts = len(numbersCombi[0])+len(numbersCombi[1])
    if (numberOfInts) > 0:
        if numberOfInts == 1:
            linkString += "Here is your link:\n\n"
        else:
            linkString += "Here are your links:\n\n"
    linkString += generateLinkString(numbersCombi)
    message.reply(linkString)
    message.mark_read()

#TODO Generate PM based on key word reply
def processCommentReply(comment, reddit):
    tsuminoNumbers = []
    nhentaiNumbers = []
    try:
        foundParent = re.findall(r'(?<=t1_).*', comment.parent_id)
    except:
        print('failure')
    if foundParent:
        parentComment = reddit.comment(foundParent[0])
        if parentComment.author.name == reddit.user.me():
            parentComment = foundParent
            tsuminoNumbers = re.findall(r'(?<=>Tsumino: )\d{5,6}', parentComment)
            # try:
            #     tsuminoNumbers = [int(number) for number in tsuminoNumbers]
            # except ValueError:
            #     numbers = []
            parentComment = re.sub(r'(?<=>Tsumino: )\d{5,6}', '', parentComment)
            nhentaiNumbers = re.findall(r'\d{5,6}', parentComment)
            # try:
            #     nhnumbers = [int(number) for number in numbers]
            # except ValueError:
            #     numbers = []


if __name__ == '__main__':
    while True:
        try:
            main()
        except Exception as e:
            pass

# main()