import requests
import json
import os
import praw
import re
import time
import datetime
import traceback
from bs4 import BeautifulSoup

from DBConn import Database
from nhentai import Nhentai
from ehentai import Ehentai
from tsumino import Tsumino
from hitomila import Hitomila

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
                     'jizzedtothisPLUS',
                     'goodanimemes',
                     'AstolfoHentai'
                     ]
# REDACTED_INFO_SUBS_LV6 = ['Animemes']
REDACTED_INFO_SUBS_ERROR = ['HentaiSource',
                            'Animemes',
                            'hentaimemes',
                            'goodanimemes',
                            'AstolfoHentai'
                            ]
REDACTED_INFO_SUBS_LV1 = ['goodanimemes']
USE_LINKS_SUBS = PARSED_SUBREDDITS.copy()
USE_LINKS_SUBS.remove('anime_irl')

# PARSED_SUBREDDITS = ['loli_tag_bot']
# # REDACTED_INFO_SUBS_LV6 = ['loli_tag_bot']
# # REDACTED_INFO_SUBS_LV1 = ['loli_tag_bot']
# REDACTED_INFO_SUBS_LV1 = []
# # REDACTED_INFO_SUBS_ERROR = ['loli_tag_bot']
# REDACTED_INFO_SUBS_ERROR = []
# USE_LINKS_SUBS = ['loli_tag_bot']

nhentaiKey = 0
tsuminoKey = 1
ehentaiKey = 2
hitomilaKey = 3
redactedKey = 4

messagesRepliedTo = []

def addFooter():
    # Needs to use ASCII code to not break reddit formatting &#32; is space &#40; is ( and &#41; is )
    return "---\n\n^(nHentai), )Tsumino(, }e-hentai/token{, !hitomi.la! | min 5 digits | [FAQ](https://www.reddit.com/r/nHentaiTagBot/wiki/index) | [/r/](https://www.reddit.com/r/nHentaiTagBot/) | [Source](https://github.com/TheVexedGerman/nHentai-Tag-Bot)".replace(' ', '&#32;').replace('(', '&#40;', 2).replace(')', '&#41;', 2)


def authenticate():
    print("Authenticating...")
    reddit = praw.Reddit(
        'nhentaibot'
        # 'thevexedgermanbot'
    )
    print("Authenticated as {}".format(reddit.user.me()))
    return reddit


#TODO change this over to using the DB
def getSavedMessages():
    # return an empty list if empty
    if not os.path.isfile("messagesRepliedTo.txt"):
        messagesRepliedTo = []
    else:
        with open("messagesRepliedTo.txt", "r") as f:
            # updated read file method from https://stackoverflow.com/questions/3925614/how-do-you-read-a-file-into-a-list-in-python
            messagesRepliedTo = f.read().splitlines()

    return messagesRepliedTo

#TODO change this over to using the DB
def getSavedLinkedMessages():
    # return an empty list if empty
    if not os.path.isfile("linksRepliedTo.txt"):
        linksRepliedTo = []
    else:
        with open("linksRepliedTo.txt", "r") as f:
            # updated read file method from https://stackoverflow.com/questions/3925614/how-do-you-read-a-file-into-a-list-in-python
            linksRepliedTo = f.read().splitlines()

    return linksRepliedTo


class NHentaiTagBot():

    def __init__(self, reddit, database):
        self.database = database
        self.reddit = reddit

        self.nhentai = Nhentai(database)
        self.tsumino = Tsumino(database)
        self.ehentai = Ehentai(database)
        self.hitomila = Hitomila(database)
        self.processors = {
            'nhentai': self.nhentai,
            'tsumino': self.tsumino,
            'ehentai': self.ehentai,
            'hitomila': self.hitomila
        }

        self.parsed_subreddit = "+".join(PARSED_SUBREDDITS)


    def runBot(self):
        lastCheckedPMsTime = time.time()
        for comment in self.reddit.subreddit(self.parsed_subreddit).stream.comments():
            if comment:
                if (time.time() - lastCheckedPMsTime) > TIME_BETWEEN_PM_CHECKS:
                    self.processPMs()
                    lastCheckedPMsTime = time.time()
                print(comment.body)
                self.processComment(comment)


    #TODO update the don't reply twice check
    def writeCommentReply(self, replyString, comment):
        print(f"Commenting with: \n{replyString}")
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


    #TODO use dict instead of list
    def getNumbers(self, comment):
        numbersCombi = self.keyWordDetection(comment)
        if not numbersCombi:
            nhentaiNumbers = self.nhentai.getNumbers(comment.body)
            tsuminoNumbers = self.tsumino.getNumbers(comment.body)
            ehentaiNumbers = self.ehentai.getNumbers(comment.body)
            hitomilaNumbers = self.hitomila.getNumbers(comment.body)
            numbersCombi = nhentaiNumbers + tsuminoNumbers + ehentaiNumbers + hitomilaNumbers
        return numbersCombi


    def keyWordDetection(self, comment):
        foundNumbers = []
        if "!tags" in comment.body.lower():
            foundNumbers = self.scanForURL(comment.body)
            if not foundNumbers:
                parent = comment.parent_id
                commentParent = re.findall(r'(?<=t1_).*', parent)
                if commentParent:
                    comment = self.reddit.comment(commentParent[0])
                    foundNumbers = self.scanForURL(comment.body)
        return foundNumbers


    def scanForURL(self, comment):
        nhentaiNumbers = self.nhentai.scanURL(comment)
        tsuminoNumbers = self.tsumino.scanURL(comment)
        ehentaiNumbers = self.ehentai.scanURL(comment)
        hitomilaNumbers = self.hitomila.scanURL(comment)

        return nhentaiNumbers + tsuminoNumbers + ehentaiNumbers + hitomilaNumbers


    def processComment(self, comment, isEdit=False):
        if comment.author.name != self.reddit.user.me():
            replyString = ""
            logString = ""
            useError = False
            useLink = False
            censorshipLevel = 0
            numbersCombi = self.getNumbers(comment)
            # if comment.subreddit in REDACTED_INFO_SUBS_LV6:
            #     censorshipLevel = 6
            if comment.subreddit in REDACTED_INFO_SUBS_LV1:
                censorshipLevel = 1
            if comment.subreddit in REDACTED_INFO_SUBS_ERROR:
                useError = True
            if comment.subreddit in USE_LINKS_SUBS:
                useLink = True
            if numbersCombi:
                if len(numbersCombi) > 5:
                    replyString += "This bot does a maximum of 5 numbers at a time, your list has been shortened:\n\n"
                    logString += "This bot does a maximum of 5 numbers at a time, your list has been shortened:\n\n"
                numbersCombi = numbersCombi[:5]
                for entry in numbersCombi:
                    if replyString:
                        replyString += "&#x200B;\n\n"
                        logString += "&#x200B;\n\n"
                    processedData = self.processors[entry['type']].analyseNumber(entry['number'])
                    replyString += self.processors[entry['type']].generateReplyString(processedData, entry['number'], censorshipLevel, useError, useLink)
                    logString += self.processors[entry['type']].generateReplyString(processedData, entry['number'])
            if replyString:
                replyString += addFooter()
                if comment.id not in messagesRepliedTo and not isEdit:
                    messagesRepliedTo.append(self.writeCommentReply(replyString, comment))
            if logString:
                self.logRequest(logString, comment)
            # required for message reply mark read
            return replyString


    #TODO change this to log into DB
    def logRequest(self, replyString, comment):
        with open("requestHistory.csv", "a", encoding="UTF-8") as f:
            f.write(f""""{comment.id}","https://reddit.com{comment.permalink}?context=1000","{comment.body}","{replyString}","{comment.author}"\n""")

    #TODO possibly update this
    def processPMs(self):
        print("Current time: " + str(datetime.datetime.now().time()))
        #Adapted from Roboragi
        for message in self.reddit.inbox.unread(limit=None):
            usernameMention = message.subject == 'username mention'
            usernameInBody = message.subject == 'comment reply' and "u/nhentaitagbot" in message.body.lower()
            linkMessage = message.subject == "[Link]" or message.subject == "re: [Link]"
            linkRequestInComment = message.subject == 'comment reply' and "!link" in message.body.lower()

            if not (usernameMention or usernameInBody):
                if linkMessage:
                    self.scanPM(message)
                if linkRequestInComment:
                    linkComment = self.reddit.comment(message.id)
                    self.processCommentReply(linkComment)
                    message.mark_read()
                continue

            try:
                mentionedComment = self.reddit.comment(message.id)
                mentionedComment.refresh()

                replies = mentionedComment.replies

                ownComments = []
                commentToEdit = None

                for reply in replies:
                    if (reply.author.name.lower() == 'nhentaitagbot'):
                        ownComments.append(reply)
                for comment in ownComments:
                    nhentaiNumbers, tsuminoNumbers, ehentaiNumbers, hitomilaNumbers, redacted = self.getOldResponses(comment)
                    if nhentaiNumbers or tsuminoNumbers or ehentaiNumbers or hitomilaNumbers or redacted:
                        commentToEdit = comment
                replyString = self.processComment(mentionedComment, isEdit=True)
                try:
                    if replyString:
                        if commentToEdit:
                            commentToEdit.edit(replyString)
                            message.mark_read()
                            continue
                except:
                    break
                print(mentionedComment.body)
                if self.processComment(mentionedComment):
                    message.mark_read()
            except:
                break


    
    def generateLinkString(self, numbersCombi):
        #generate the string that will be replied
        linkString = ""
        if numbersCombi:
            for entry in numbersCombi:
                linkString += self.processors[entry['type']].analyseNumber(entry['number'])
        return linkString


    def scanPM(self, message):
        linkString = ""
        numbersCombi = self.getNumbers(message)
        numberOfInts = len(numbersCombi)
        if (numberOfInts) > 0:
            if numberOfInts == 1:
                linkString += "Here is your link:\n\n"
            else:
                linkString += "Here are your links:\n\n"
        numbersCombi.append(False)
        linkString += self.generateLinkString(numbersCombi)
        message.reply(linkString)
        message.mark_read()


    def processCommentReply(self, comment):
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
            parentComment = self.reddit.comment(foundParent.group(0))
            if parentComment.author.name == self.reddit.user.me() and parentComment.id not in postsLinked:
                nhentaiNumbers, tsuminoNumbers, ehentaiNumbers, hitomilaNumbers, redacted = self.getOldResponses(parentComment)
        if nhentaiNumbers or tsuminoNumbers or ehentaiNumbers or hitomilaNumbers or redacted:
            parent = parentComment
            numberOfInts = len(nhentaiNumbers)+len(tsuminoNumbers)+len(ehentaiNumbers)+len(hitomilaNumbers)
            if numberOfInts > 0:
                if numberOfInts == 1:
                    linkString += "Here is your link:\n\n"
                else:
                    linkString += "Here are your links:\n\n"
            linkString += self.generateLinkString([nhentaiNumbers, tsuminoNumbers, ehentaiNumbers, hitomilaNumbers, redacted])
            if not redacted:
                replyString += "You have been PM'd the links to the numbers above.\n\n"
            else:
                replyString += "Restricted numbers don't get links. If there are unresticted numbers a link has been PM'd to you.\n\n"
            if (redacted and (nhentaiNumbers or tsuminoNumbers or ehentaiNumbers or hitomilaNumbers)) or not redacted:
                replyString += "This is the first and **only** link comment I will respond to for this request to prevent clutter, if you'd also like to receive the link please [click here]("+ self.generateReplyLink([nhentaiNumbers, tsuminoNumbers, ehentaiNumbers, hitomilaNumbers]) +")\n\n"
            if not redacted:
                replyString += "---\n\n"
                subReplyString = ""
                subReplyString += "^Note: It seems like the official reddit app has issues handling pre-formatted PM links: if the above link leads you to a blank message form, you'll have to fill the fields in manually with `[Link]` as the subject and the numbers in brackets " + self.generateManualInfo([nhentaiNumbers, tsuminoNumbers, ehentaiNumbers, hitomilaNumbers]) + ".\n\n"
                replyString += re.sub(r' ', '&#32;', subReplyString)
            print(linkString)
            print(replyString)
        if linkString and replyString:
            print(comment.author)
            postsLinked.append(parent.id)
            with open("linksRepliedTo.txt", "a") as f:
                f.write(parent.id + "\n")
            self.reddit.redditor(comment.author.name).message('[Link]', linkString)
            comment.reply(replyString)
            
            return True
        return False


    def getOldResponses(self, parentComment):
        numbersCombi = []
        nhentaiNumbers = []
        tsuminoNumbers = []
        ehentaiNumbers = []
        hitomilaNumbers = []
        # redacted = []
        if re.search(r'\[click here\]', parentComment.body):
            return False
        parentComment = parentComment.body

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



    def generateReplyLink(self, numbersCombi, manualinfo = False):
        if not manualinfo:
            character_map = {
                'nhentai': {
                    'start': '%28',
                    'end': '%29'
                },
                'tsumino': {
                    'start': '%29',
                    'end': '%28'
                },
                'ehentai': {
                    'start': '}',
                    'end': '{'
                },
                'hitomila': {
                    'start': '!',
                    'end': '!'
                },
                'join_char': '+',
                'replyString': 'https://reddit.com/message/compose/?to=nHentaiTagBot&subject=[Link]&message='
            }
        else:
            character_map = {
                'nhentai': {
                    'start': '`(',
                    'end': ')`'
                },
                'tsumino': {
                    'start': '`)',
                    'end': '(`'
                },
                'ehentai': {
                    'start': '`}',
                    'end': '{`'
                },
                'hitomila': {
                    'start': '`!',
                    'end': '!`'
                },
                'join_char': ' ',
                'replyString' : ''
            }
        #  %28 is ( and %29 is )
        # https://reddit.com/message/compose/?to=nHentai-Tag-Bot&subject=[Link]&message=(123456)+)12345(
        replyString = character_map['replyString']
        for i, item in enumerate(numbersCombi):
            replyString += f"{character_map[item['type']]['start']}{'/'.join(item['number']) if item['type'] == 'ehentai' else item['number']}{character_map[item['type']]['start']}{character_map['join_char'] if i < len(numbersCombi)-1 else ''}"

        return replyString


def main():
    reddit = authenticate()
    global messagesRepliedTo
    messagesRepliedTo = getSavedMessages()
    global postsLinked
    postsLinked = getSavedLinkedMessages()
    while True:
        runBot(reddit)

if __name__ == '__main__':
    while True:
        try:
            main()
        except Exception as e:
            print(traceback.format_exc())

# main()