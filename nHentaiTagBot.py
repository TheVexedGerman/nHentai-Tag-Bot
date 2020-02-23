import requests
import json
import os
import praw
import re
import time
import datetime
import traceback
from bs4 import BeautifulSoup

import nhentai
import ehentai
import tsumino
import hitomila
import commentpy

API_URL_NHENTAI = 'https://nhentai.net/api/gallery/'
API_URL_TSUMINO = 'https://www.tsumino.com/entry/'
API_URL_EHENTAI = "https://api.e-hentai.org/api.php"
LINK_URL_NHENTAI = "https://nhentai.net/g/"
LINK_URL_EHENTAI = "https://e-hentai.org/g/"

TIME_BETWEEN_PM_CHECKS = 60  # in seconds

PARSED_SUBREDDITS = ['Animemes',
                     'hentai_irl',
                     'anime_irl',
                     'u_Loli-Tag-Bot',
                     'u_nHentaiTagBot',
                     'HentaiSource',
                     'CroppedHentaiMemes',
                     'hentaimemes',
                     'SauceSharingCommunity',
                     'jizzedtothisHENTAI',
                     'nHentaiTagBot',
                     'hentaidankmemes',
                     'jizzedtothisPLUS']
# REDACTED_INFO_SUBS_LV6 = ['Animemes']
REDACTED_INFO_SUBS_ERROR = ['HentaiSource', 'Animemes', 'hentaimemes']
USE_LINKS_SUBS = PARSED_SUBREDDITS.copy()
USE_LINKS_SUBS.remove('anime_irl')

# PARSED_SUBREDDITS = ['loli_tag_bot']
# # REDACTED_INFO_SUBS_LV6 = ['loli_tag_bot']
# # REDACTED_INFO_SUBS_ERROR = ['loli_tag_bot']
# REDACTED_INFO_SUBS_ERROR = []
# USE_LINKS_SUBS = ['loli_tag_bot']

nhentaiKey = 0
tsuminoKey = 1
ehentaiKey = 2
hitomilaKey = 3
redactedKey = 4

messagesRepliedTo = []

def subListToString(lst):
    string = f'{lst[0]}'
    for i in range(len(lst)):
        if i > 0:
            string += f'+{lst[i]}'
    return string

#Moved lower to have method defined
PARSED_SUBREDDIT = subListToString(PARSED_SUBREDDITS)
print(PARSED_SUBREDDIT)

def addFooter():
    # Needs to use ASCII code to not break reddit formatting &#32; is space &#40; is ( and &#41; is )
    # return "---\n\n^&#40;nHentai&#41;,&#32;&#41;Tsumino&#40;,&#32;}e-hentai/token{,&#32;!hitomi.la!&#32;|&#32;min&#32;5&#32;digits&#32;|&#32;[Contact](https://www.reddit.com/message/compose/?to=thevexedgerman&subject=[nHentai-Bot])&#32;|&#32;[Source](https://github.com/TheVexedGerman/nHentai-Tag-Bot)"
    return "---\n\n^(nHentai), )Tsumino(, }e-hentai/token{, !hitomi.la! | min 5 digits | [FAQ](https://www.reddit.com/r/nHentaiTagBot/wiki/index) | [/r/](https://www.reddit.com/r/nHentaiTagBot/) | [Source](https://github.com/TheVexedGerman/nHentai-Tag-Bot)".replace(' ', '&#32;').replace('(', '&#40;', 2).replace(')', '&#41;', 2)


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
    global postsLinked
    postsLinked = getSavedLinkedMessages()
    while True:
        runBot(reddit)


def getNumbers(comment):
    numbersCombi = []
    numbersCombi = keyWordDetection(comment)
    if not numbersCombi:
        nhentaiNumbers = nhentai.getNumbers(comment.body)
        tsuminoNumbers = tsumino.getNumbers(comment.body)
        ehentaiNumbers = ehentai.getNumbers(comment.body)
        hitomilaNumbers = hitomila.getNumbers(comment.body)
        numbersCombi = [nhentaiNumbers, tsuminoNumbers, ehentaiNumbers, hitomilaNumbers]
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
    hitomilaNumbers = []

    nhentaiNumbers = nhentai.scanURL(comment)
    tsuminoNumbers = tsumino.scanURL(comment)
    ehentaiNumbers = ehentai.scanURL(comment)
    hitomilaNumbers = hitomila.scanURL(comment)

    if nhentaiNumbers or tsuminoNumbers or ehentaiNumbers or hitomilaNumbers:
        print("true return")
        return [nhentaiNumbers, tsuminoNumbers, ehentaiNumbers, hitomilaNumbers]
    return []


def getSavedMessages():
    # return an empty list if empty
    if not os.path.isfile("messagesRepliedTo.txt"):
        messagesRepliedTo = []
    else:
        with open("messagesRepliedTo.txt", "r") as f:
            # updated read file method from https://stackoverflow.com/questions/3925614/how-do-you-read-a-file-into-a-list-in-python
            messagesRepliedTo = f.read().splitlines()

    return messagesRepliedTo


def getSavedLinkedMessages():
    # return an empty list if empty
    if not os.path.isfile("linksRepliedTo.txt"):
        linksRepliedTo = []
    else:
        with open("linksRepliedTo.txt", "r") as f:
            # updated read file method from https://stackoverflow.com/questions/3925614/how-do-you-read-a-file-into-a-list-in-python
            linksRepliedTo = f.read().splitlines()

    return linksRepliedTo


def processComment(comment, isEdit=False):
    if comment.author.name != reddit.user.me():
        replyString = ""
        logString = ""
        useError = False
        useLink = False
        censorshipLevel = 0
        numbersCombi = getNumbers(comment)
        # if comment.subreddit in REDACTED_INFO_SUBS_LV6:
        #     censorshipLevel = 6
        if comment.subreddit in REDACTED_INFO_SUBS_ERROR:
            useError = True
        if comment.subreddit in USE_LINKS_SUBS:
            useLink = True
        #TODO make this more efficient
        combination = []
        i = 0
        if numbersCombi:
            for entry in numbersCombi:
                for subentry in entry:
                    combination.append([subentry, i])
                i += 1
        if combination:
            if len(combination) > 5:
                replyString += "This bot does a maximum of 5 numbers at a time, your list has been shortened:\n\n"
                logString += "This bot does a maximum of 5 numbers at a time, your list has been shortened:\n\n"
            combination = combination[:5]
            for entry in combination:
                if replyString:
                    replyString += "&#x200B;\n\n"
                    logString += "&#x200B;\n\n"
                number = entry[0]
                key = entry[1]
                if key == nhentaiKey:
                    processedData = nhentai.analyseNumber(number)
                    replyString += nhentai.generateReplyString(processedData, number, censorshipLevel, useError, useLink)
                    logString += nhentai.generateReplyString(processedData, number)
                elif key == tsuminoKey:
                    processedData = tsumino.analyseNumber(number)
                    replyString += tsumino.generateReplyString(processedData, number, censorshipLevel, useError, useLink)
                    logString += tsumino.generateReplyString(processedData, number)
                elif key == ehentaiKey:
                    processedData = ehentai.analyseNumber(number)
                    replyString += ehentai.generateReplyString(processedData, number, censorshipLevel, useError, useLink)
                    logString += ehentai.generateReplyString(processedData, number)
                elif key == hitomilaKey:
                    processedData = hitomila.analyseNumber(number)
                    replyString += hitomila.generateReplyString(processedData, number, censorshipLevel, useError, useLink)
                    logString += hitomila.generateReplyString(processedData, number)
        if replyString:
            replyString += addFooter()
            if comment.id not in messagesRepliedTo and not isEdit:
                messagesRepliedTo.append(writeCommentReply(replyString, comment))
        # required for message reply mark read
        if logString:
            logRequest(logString, comment)
        return replyString


def logRequest(replyString, comment):
    with open("requestHistory.csv", "a", encoding="UTF-8") as f:
        f.write(f""""{comment.id}","https://reddit.com{comment.permalink}?context=1000","{comment.body}","{replyString}","{comment.author}"\n""")


def processPMs(reddit):
    print("Current time: " + str(datetime.datetime.now().time()))
    #Adapted from Roboragi
    for message in reddit.inbox.unread(limit=None):
        usernameMention = message.subject == 'username mention'
        usernameInBody = message.subject == 'comment reply' and "u/nhentaitagbot" in message.body.lower()
        linkMessage = message.subject == "[Link]" or message.subject == "re: [Link]"
        linkRequestInComment = message.subject == 'comment reply' and "!link" in message.body.lower()

        if not (usernameMention or usernameInBody):
            if linkMessage:
                scanPM(message)
            if linkRequestInComment:
                linkComment = reddit.comment(message.id)
                processCommentReply(linkComment)
                message.mark_read()
            continue

        try:
            mentionedComment = reddit.comment(message.id)
            mentionedComment.refresh()

            replies = mentionedComment.replies

            ownComments = []
            commentToEdit = None

            for reply in replies:
                if (reply.author.name.lower() == 'nhentaitagbot'):
                    ownComments.append(reply)
            for comment in ownComments:
                nhentaiNumbers, tsuminoNumbers, ehentaiNumbers, hitomilaNumbers, redacted = getOldResponses(comment)
                if nhentaiNumbers or tsuminoNumbers or ehentaiNumbers or hitomilaNumbers or redacted:
                    commentToEdit = comment
            replyString = processComment(mentionedComment, isEdit=True)
            try:
                if replyString:
                    if commentToEdit:
                        commentToEdit.edit(replyString)
                        message.mark_read()
                        continue
            except:
                break
            print(mentionedComment.body)
            if processComment(mentionedComment):
                message.mark_read()
        except:
            break


def generateLinkString(numbersCombi):
    #generate the string that will be replied
    linkString = ""
    if numbersCombi:
        if numbersCombi[nhentaiKey]:
            numbers = numbersCombi[nhentaiKey]
            for number in numbers:
                linkString += generateLinks(number, nhentaiKey) + "\n\n"
        if numbersCombi[tsuminoKey]:
            numbers = numbersCombi[tsuminoKey]
            for number in numbers:
                linkString += generateLinks(number, tsuminoKey) + "\n\n"
        if numbersCombi[ehentaiKey]:
            numbers = numbersCombi[ehentaiKey]
            for number in numbers:
                linkString += generateLinks(number, ehentaiKey) + "\n\n"
        if numbersCombi[hitomilaKey]:
            numbers = numbersCombi[hitomilaKey]
            for number in numbers:
                linkString += generateLinks(number, hitomilaKey) +"\n\n"
        if numbersCombi[redactedKey]:
            numbers = numbersCombi[redactedKey]
            for number in numbers:
                linkString += "This number has been redacted and therefore no link can be generated. \n\n"
    return linkString


def generateLinks(number, key):
    # make the link
    linkString = ""
    if key == nhentaiKey:
        tags = nhentai.analyseNumber(number)
        if len(tags) > 1 and not tags[-1]:
            linkString = LINK_URL_NHENTAI + str(number)
    elif key == tsuminoKey:
        tags = tsumino.analyseNumber(number)
        if len(tags) > 1 and not tags[-1]:
            # Since Tsumino is just being HTML parsed the API URL is fine
            linkString = API_URL_TSUMINO + str(number)
    elif key == ehentaiKey:
        tags = ehentai.analyseNumber(number)
        if len(tags) > 1 and not tags[-1]:
            linkString = LINK_URL_EHENTAI + str(number[0]) + "/" + number[1]
    elif key == hitomilaKey:
        tags = hitomila.analyseNumber(number)
        if len(tags) > 1 and not tags[-1]:
            linkString = hitomila.API_URL_HITOMILA + str(number) + ".html"
    if not linkString:
        linkString = "This number contains restricted tags and therefore cannot be linked"
    return linkString


def scanPM(message):
    linkString = ""
    numbersCombi = getNumbers(message)
    numberOfInts = len(numbersCombi[0])+len(numbersCombi[1])+len(numbersCombi[2])+len(numbersCombi[3])
    if (numberOfInts) > 0:
        if numberOfInts == 1:
            linkString += "Here is your link:\n\n"
        else:
            linkString += "Here are your links:\n\n"
    numbersCombi.append(False)
    linkString += generateLinkString(numbersCombi)
    message.reply(linkString)
    message.mark_read()


def processCommentReply(comment):
    tsuminoNumbers = []
    ehentaiNumbers = []
    nhentaiNumbers = []
    hitomilaNumbers = []
    redacted = []
    replyString = ""
    linkString = ""
    try:
        foundParent = re.search(r'(?<=t1_).*', comment.parent_id)
    except:
        print('failure')
    if foundParent:
        parentComment = reddit.comment(foundParent.group(0))
        if parentComment.author.name == reddit.user.me() and parentComment.id not in postsLinked:
            nhentaiNumbers, tsuminoNumbers, ehentaiNumbers, hitomilaNumbers, redacted = getOldResponses(parentComment)
    if nhentaiNumbers or tsuminoNumbers or ehentaiNumbers or hitomilaNumbers or redacted:
        parent = parentComment
        numberOfInts = len(nhentaiNumbers)+len(tsuminoNumbers)+len(ehentaiNumbers)+len(hitomilaNumbers)
        if numberOfInts > 0:
            if numberOfInts == 1:
                linkString += "Here is your link:\n\n"
            else:
                linkString += "Here are your links:\n\n"
        linkString += generateLinkString([nhentaiNumbers, tsuminoNumbers, ehentaiNumbers, hitomilaNumbers, redacted])
        if not redacted:
            replyString += "You have been PM'd the links to the numbers above.\n\n"
        else:
            replyString += "Restricted numbers don't get links. If there are unresticted numbers a link has been PM'd to you.\n\n"
        if (redacted and (nhentaiNumbers or tsuminoNumbers or ehentaiNumbers or hitomilaNumbers)) or not redacted:
            replyString += "This is the first and **only** link comment I will respond to for this request to prevent clutter, if you'd also like to receive the link please [click here]("+ generateReplyLink([nhentaiNumbers, tsuminoNumbers, ehentaiNumbers, hitomilaNumbers]) +")\n\n"
        if not redacted:
            replyString += "---\n\n"
            subReplyString = ""
            subReplyString += "^Note: It seems like the official reddit app has issues handling pre-formatted PM links: if the above link leads you to a blank message form, you'll have to fill the fields in manually with `[Link]` as the subject and the numbers in brackets " + generateManualInfo([nhentaiNumbers, tsuminoNumbers, ehentaiNumbers, hitomilaNumbers]) + ".\n\n"
            replyString += re.sub(r' ', '&#32;', subReplyString)
        print(linkString)
        print(replyString)
    if linkString and replyString:
        print(comment.author)
        postsLinked.append(parent.id)
        with open("linksRepliedTo.txt", "a") as f:
            f.write(parent.id + "\n")
        reddit.redditor(comment.author.name).message('[Link]', linkString)
        comment.reply(replyString)
        
        return True
    return False


def getOldResponses(parentComment):
    tsuminoNumbers = []
    ehentaiNumbers = []
    nhentaiNumbers = []
    hitomilaNumbers = []
    redacted = []
    if re.search(r'\[click here\]', parentComment.body):
        return False
    parentComment = parentComment.body

    # Remove restricted numbers
    # Remove already existing links
    parentComment = re.sub(r'\[.*?\]\(.*?\)', '', parentComment)
    print(parentComment)
    redacted = re.findall(r'&#32;\n\n', parentComment)
    print(redacted)
    parentComment = re.sub(r'(?<=>).*?(?=&#32;\n\n)', '', parentComment)


    # print(parentComment)

    tsuminoNumbers = re.findall(r'(?<=>Tsumino: )\d{5,6}', parentComment)
    try:
        tsuminoNumbers = [int(number) for number in tsuminoNumbers]
    except ValueError:
        tsuminoNumbers = []
    parentComment = re.sub(r'(?<=>Tsumino: )\d{5,6}', '', parentComment)
    print(tsuminoNumbers)
    # print(parentComment)


    ehentaiNumbersCandidates = re.findall(r'(?<=>E-Hentai: )\d{1,8}\/\w*', parentComment)
    print(ehentaiNumbersCandidates)
    try:
        for entry in ehentaiNumbersCandidates:
            galleryID = int(re.search(r'\d+(?=\/)', entry).group(0))
            galleryToken = re.search(r'(?<=\/)\w+', entry).group(0)
            ehentaiNumbers.append([galleryID, galleryToken])
    except AttributeError:
        print("Number Recognition failed Ehentai")

    parentComment = re.sub(r'(?<=>E-Hentai: )\d{1,8}\/\w*', '', parentComment)
    print(ehentaiNumbers)
    # print(parentComment)

    hitomilaNumbers = re.findall(r'(?<=>Hitomi.la: )\d{5,8}', parentComment)
    try:
        hitomilaNumbers = [int(number) for number in hitomilaNumbers]
    except ValueError:
        hitomilaNumbers = []
    print(hitomilaNumbers)

    parentComment = re.sub(r'(?<=>Hitomi.la: )\d{5,8}', '', parentComment)

    nhentaiNumbers = re.findall(r'\d{5,6}', parentComment)
    try:
        nhentaiNumbers = [int(number) for number in nhentaiNumbers]
    except ValueError:
        nhentaiNumbers = []

    redacted += re.findall(r'\[REDACTED\]', parentComment)
    if redacted:
        redacted = [True]
    return nhentaiNumbers, tsuminoNumbers, ehentaiNumbers, hitomilaNumbers, redacted




def generateReplyLink(numbersCombi):
    #  %28 is ( and %29 is )
    # https://reddit.com/message/compose/?to=nHentai-Tag-Bot&subject=[Link]&message=(123456)+)12345(
    replyString = "https://reddit.com/message/compose/?to=nHentaiTagBot&subject=[Link]&message="
    if numbersCombi[nhentaiKey]:
        i = 0
        numbers = numbersCombi[nhentaiKey]
        length = len(numbers) - 1
        for number in numbers:
            replyString += '%28' + str(number).zfill(5) + '%29'
            if length != i or numbersCombi[tsuminoKey] or numbersCombi[ehentaiKey] or numbersCombi[hitomilaKey]:
                replyString += '+'
            i += 1
    if numbersCombi[tsuminoKey]:
        i = 0
        numbers = numbersCombi[tsuminoKey]
        length = len(numbers) - 1
        for number in numbers:
            replyString += '%29' + str(number).zfill(5) + '%28'
            if length != i or numbersCombi[ehentaiKey] or numbersCombi[hitomilaKey]:
                replyString += '+'
            i += 1
    if numbersCombi[ehentaiKey]:
        i = 0
        numbers = numbersCombi[ehentaiKey]
        length = len(numbers) - 1
        for number in numbers:
            replyString += '}' + str(number[0]) + '/' + str(number[1]) + '{'
            if length != i or numbersCombi[hitomilaKey]:
                replyString += '+'
            i += 1
    if numbersCombi[hitomilaKey]:
        i = 0
        numbers = numbersCombi[hitomilaKey]
        length = len(numbers) - 1
        for number in numbers:
            replyString += '!' + str(number).zfill(5) + '!'
            if length != i:
                replyString += '+'
            i += 1
    # if numbersCombi[redactedKey]:
    #     i = 0
    #     numbers = numbersCombi[redactedKey]
    #     length = len(numbers) - 1
    #     for number in numbers:
    #         replyString += "This number has been removed for a reason. No link can be generated"
    return replyString


def generateManualInfo(numbersCombi):
    #TODO, use string replacement to use this function with the link generator
    replyString = ""
    if numbersCombi[nhentaiKey]:
        i = 0
        numbers = numbersCombi[nhentaiKey]
        length = len(numbers) - 1
        for number in numbers:
            replyString += '`(' + str(number).zfill(5) + ')`'
            if length != i or numbersCombi[tsuminoKey] or numbersCombi[ehentaiKey] or numbersCombi[hitomilaKey]:
                replyString += ' '
            i += 1
    if numbersCombi[tsuminoKey]:
        i = 0
        numbers = numbersCombi[tsuminoKey]
        length = len(numbers) - 1
        for number in numbers:
            replyString += '`)' + str(number).zfill(5) + '(`'
            if length != i or numbersCombi[ehentaiKey] or numbersCombi[hitomilaKey]:
                replyString += ' '
            i += 1
    if numbersCombi[ehentaiKey]:
        i = 0
        numbers = numbersCombi[ehentaiKey]
        length = len(numbers) - 1
        for number in numbers:
            replyString += '`}' + str(number[0]) + '/' + str(number[1]) + '{`'
            if length != i or numbersCombi[hitomilaKey]:
                replyString += ' '
            i += 1
    if numbersCombi[hitomilaKey]:
        i = 0
        numbers = numbersCombi[hitomilaKey]
        length = len(numbers) - 1
        for number in numbers:
            replyString += '`!' + str(number).zfill(5) + '!`'
            if length != i:
                replyString += ' '
            i += 1
    return replyString


if __name__ == '__main__':
    while True:
        try:
            main()
        except Exception as e:
            print(traceback.format_exc())

# main()