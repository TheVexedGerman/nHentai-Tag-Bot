import requests
import json
import os
import praw
import re
import time
import datetime
from bs4 import BeautifulSoup

import nhentai
import ehentai
import tsumino
import hitomila
import commentpy

API_URL_NHENTAI = 'https://nhentai.net/api/gallery/'
API_URL_TSUMINO = 'https://www.tsumino.com/Book/Info/'
API_URL_EHENTAI = "https://api.e-hentai.org/api.php"
LINK_URL_NHENTAI = "https://nhentai.net/g/"
LINK_URL_EHENTAI = "https://e-hentai.org/g/"

TIME_BETWEEN_PM_CHECKS = 60  # in seconds

PARSED_SUBREDDIT = 'Animemes+hentai_irl+anime_irl+u_Loli-Tag-Bot+u_nHentai-Tag-Bot+HentaiSource+CroppedHentaiMemes+hentaimemes'
REDACTED_INFO_SUBS = ['Animemes']
# PARSED_SUBREDDIT = 'loli_tag_bot'
# REDACTED_INFO_SUBS = ['loli_tag_bot']

nhentaiKey = 0
tsuminoKey = 1
ehentaiKey = 2
hitomilaKey = 3
redactedKey = 4

messagesRepliedTo = []

def addFooter():
    # Needs to use ASCII code to not break reddit formatting &#32; is space &#40; is ( and &#41; is )
    return "---\n\n^&#40;nHentai&#41;,&#32;&#41;Tsumino&#40;,&#32;}e-hentai/token{&#32;|&#32;!hitomi.la!&#32;|&#32;min&#32;5&#32;digits&#32;|&#32;[Contact](https://www.reddit.com/message/compose/?to=thevexedgerman&subject=[nHentai-Bot])&#32;|&#32;[Source](https://github.com/TheVexedGerman/nHentai-Tag-Bot)"


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


def processComment(comment):
    if comment.id not in messagesRepliedTo and comment.author.name != reddit.user.me():
        replyString = ""
        isRedacted = False
        numbersCombi = getNumbers(comment)
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
            combination = combination[:5]
            for entry in combination:
                if replyString:
                    replyString += "&#x200B;\n\n"
                number = entry[0]
                key = entry[1]
                if key == nhentaiKey:
                    processedData = nhentai.analyseNumber(number)
                    replyString += nhentai.generateReplyString(processedData, number)
                    if processedData[len(processedData)-1]:
                        isRedacted = True
                elif key == tsuminoKey:
                    processedData = tsumino.analyseNumber(number)
                    replyString += tsumino.generateReplyString(processedData, number)
                    if processedData[len(processedData)-1]:
                        isRedacted = True
                elif key == ehentaiKey:
                    processedData = ehentai.analyseNumber(number)
                    replyString += ehentai.generateReplyString(processedData, number)
                    if processedData[len(processedData)-1]:
                        isRedacted = True
                elif key == hitomilaKey:
                    processedData = hitomila.analyseNumber(number)
                    replyString += hitomila.generateReplyString(processedData, number)
                    if processedData[len(processedData)-1]:
                        isRedacted = True
        if replyString:
            if comment.subreddit in REDACTED_INFO_SUBS and isRedacted:
                header = "YOUR QUERY LEADS TO LOLI/SHOTA.\n\nThis violates Animemes rule 7.2. You are advised to edit your comment to remove the number(s) before it gets deleted.\n\n&#x200B;\n\n"
                replyString = header + replyString
            replyString += addFooter()
            messagesRepliedTo.append(writeCommentReply(replyString, comment))
        # required for message reply mark read
        return True



def processPMs(reddit):
    print("Current time: " + str(datetime.datetime.now().time()))
    #Adapted from Roboragi
    for message in reddit.inbox.unread(limit=None):
        usernameMention = message.subject == 'username mention'
        usernameInBody = message.subject == 'comment reply' and "u/nhentaitagbot" in message.body.lower()
        linkMessage = message.subject == "[Link]" or message.subject == "re: [Link]"
        linkRequestInComment = message.subject == 'comment reply' and "!link" in message.body.lower()

        # This PM doesn't meet the response criteria. Skip it.
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
        linkString = LINK_URL_NHENTAI + str(number)
    elif key == tsuminoKey:
        # Since Tsumino is just being HTML parsed the API URL is fine
        linkString = API_URL_TSUMINO + str(number)
    elif key == ehentaiKey:
        linkString = LINK_URL_EHENTAI + str(number[0]) + "/" + number[1]
    elif key == hitomilaKey:
        linkString = hitomila.API_URL_HITOMILA + str(number) + ".html"
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
            if re.search(r'\[click here\]', parentComment.body):
                return False
            parent = parentComment
            parentComment = parentComment.body

            print(parentComment)

            tsuminoNumbers = re.findall(r'(?<=>Tsumino: )\d{5,6}', parentComment)
            try:
                tsuminoNumbers = [int(number) for number in tsuminoNumbers]
            except ValueError:
                tsuminoNumbers = []
            parentComment = re.sub(r'(?<=>Tsumino: )\d{5,6}', '', parentComment)
            print(tsuminoNumbers)
            print(parentComment)


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
            print(parentComment)

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

            redacted = re.findall(r'\[REDACTED\]', parentComment)
            redacted = [True for entry in redacted]
    if nhentaiNumbers or tsuminoNumbers or ehentaiNumbers or hitomilaNumbers or redacted:
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
            replyString += "Redaction prevents link generation. If there are numbers beside the redacted ones a link has been PM'd to you.\n\n"
        if (redacted and (nhentaiNumbers or tsuminoNumbers or ehentaiNumbers)) or not redacted:
            replyString += "If you also want to receive the link [click here]("+ generateReplyLink([nhentaiNumbers, tsuminoNumbers, ehentaiNumbers, hitomilaNumbers]) +")\n\n"
        replyString += "---\n\n"
        replyString += "^(Please be aware that this action will only be performed for the first !links reply to each comment.)\n\n"
        subReplyString = ""
        subReplyString += "^^Subsequent requests have to use the message link.\n\n"
        subReplyString += "^^It appears that the official reddit app has issues handling pre-formatted PM links. Consider using an alternative app or submitting an issue to reddit.\n\n"
        subReplyString += "^^To manually get the link PM with the title **[Link]** and the body containing the number in the appropriate parentheses.\n\n"
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


if __name__ == '__main__':
    while True:
        try:
            main()
        except Exception as e:
            pass

# main()