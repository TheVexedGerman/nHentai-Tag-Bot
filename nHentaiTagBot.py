import requests
import json
import os
import praw
import prawcore
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
                     'AstolfoHentai',
                     'AquaLewds'
                     ]
# REDACTED_INFO_SUBS_LV6 = ['Animemes']
REDACTED_INFO_SUBS_ERROR = ['HentaiSource',
                            'Animemes',
                            # 'hentaimemes',
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
# REDACTED_INFO_SUBS_ERROR = ['loli_tag_bot']
# # REDACTED_INFO_SUBS_ERROR = []
# USE_LINKS_SUBS = ['loli_tag_bot']


def authenticate():
    print("Authenticating...")
    reddit = praw.Reddit(
        'nhentaibot'
        # 'thevexedgermanbot'
    )
    print("Authenticated as {}".format(reddit.user.me()))
    return reddit


#TODO change this over to using the DB eventually, though it's low volume
def getSavedLinkedMessages():
    # return an empty list if no file
    if not os.path.isfile("linksRepliedTo.txt"):
        linksRepliedTo = []
    else:
        with open("linksRepliedTo.txt", "r") as f:
            linksRepliedTo = f.read().splitlines()

    return linksRepliedTo


class NHentaiTagBot():

    def __init__(self, reddit, database):
        self.database = database
        self.reddit = reddit

        self.nhentai = Nhentai(database)
        self.tsumino = Tsumino(database)
        self.ehentai = Ehentai(database)
        # self.hitomila = Hitomila(database)
        self.processors = {
            'nhentai': self.nhentai,
            'tsumino': self.tsumino,
            'ehentai': self.ehentai
            # 'hitomila': self.hitomila
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
                self.scan_comment_and_reply(comment)

    def scan_comment_and_reply(self, comment):
        if comment.author.name == self.reddit.user.me():
            return False
        self.database.execute("SELECT comment_id FROM tag_bot WHERE comment_id = %s", (comment.id,))
        already_replied = self.database.fetchone()
        if already_replied:
            return False
        reply_sting, log_string, numbersCombi = self.scan_comment_and_generate_reply(comment)
        if reply_sting and log_string:
            reply = self.writeCommentReply(reply_sting, comment)
            if reply:
                self.logRequest(log_string, comment, reply, numbersCombi)
            return True
        return False


    def logRequest(self, replyString, comment, reply, numbersCombi):
        query = """INSERT INTO tag_bot
        (comment_id, body, reply, reply_id, comment_author, created_utc, post_id, subreddit)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (comment_id)
        DO UPDATE SET body_edited = EXCLUDED.body, reply_edited = EXCLUDED.reply"""
        self.database.execute(query, (comment.id, comment.body, replyString, reply.id, comment.author.name, datetime.datetime.utcnow(), comment.link_id, comment.subreddit.name))
        for number in numbersCombi:
            if number['type'] == 'ehentai':
                self.database.execute("INSERT INTO stat_tracking (gallery_number, token, site, comment_id) VALUES (%s, %s, %s, %s)", (number['number'][0], number['number'][1], number['type'], comment.id))
            else:
                self.database.execute("INSERT INTO stat_tracking (gallery_number, site, comment_id) VALUES (%s, %s, %s)", (number['number'], number['type'], comment.id))
        self.database.commit()
        

    def writeCommentReply(self, replyString, comment):
        reply = None
        print(f"Commenting with: \n{replyString}")
        for attempt in range(2):
            try:
                print("Attempt: " + str(attempt))
                reply = comment.reply(replyString)
                print("Post successful")
                return reply
            except prawcore.exceptions.Forbidden:
                print("unable to post")
                break
            except:
                print("Post unsuccessful")
                time.sleep(2)


    def getNumbers(self, comment):
        # use a list here because every entry is marked and it makes iterating easier
        # Try the key work detection parser, ele run the normal one.
        numbersCombi = self.keyWordDetection(comment)
        if not numbersCombi:
            numbersCombi = []
            for processor in self.processors.values():
                numbersCombi += processor.getNumbers(comment.body)
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
        numbersCombi = []
        for processor in self.processors.values():
            numbersCombi += processor.scanURL(comment)
        return numbersCombi


    def scan_comment_and_generate_reply(self, comment):
        useError = comment.subreddit in REDACTED_INFO_SUBS_ERROR
        useLink = comment.subreddit in USE_LINKS_SUBS
        censorshipLevel = 0
        # if comment.subreddit in REDACTED_INFO_SUBS_LV6:
        #     censorshipLevel = 6
        # if comment.subreddit in REDACTED_INFO_SUBS_LV1:
        #     censorshipLevel = 1
        numbersCombi = self.getNumbers(comment)
        replyString, logString = self.generateReplyString(numbersCombi, censorshipLevel, useError, useLink)
        return replyString, logString, numbersCombi

    def generateReplyString(self, numbersCombi, censorshipLevel, useError, useLink):
        replyString = ""
        logString = ""
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
            # Needs to use ASCII code to not break reddit formatting &#32; is space &#40; is ( and &#41; is )
            replyString += "---\n\n^(nHentai), )Tsumino(, }e-hentai/token{ | min 5 digits | [FAQ](https://www.reddit.com/r/nHentaiTagBot/wiki/index) | [/r/](https://www.reddit.com/r/nHentaiTagBot/) | [Source](https://github.com/TheVexedGerman/nHentai-Tag-Bot)".replace(' ', '&#32;').replace('(', '&#40;', 2).replace(')', '&#41;', 2)
        return replyString, logString


    def processPMs(self):
        print("Current time: " + str(datetime.datetime.now().time()))
        #Adapted from Roboragi
        for message in self.reddit.inbox.unread(limit=None):
            usernameMention = message.subject == 'username mention'
            usernameInBody = message.subject == 'comment reply' and f"u/{self.reddit.user.me().name.lower()}" in message.body.lower()
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
                    if (reply.author.name.lower() == self.reddit.user.me().name.lower()):
                        ownComments.append(reply)
                for comment in ownComments:
                    numbers_combi = self.getOldResponses(comment)
                    if numbers_combi:
                        commentToEdit = comment
                try:
                    if commentToEdit:
                        replyString, logstring, numbers_combi = self.scan_comment_and_generate_reply(mentionedComment)
                        if replyString:
                                commentToEdit.edit(replyString)
                                message.mark_read()
                                self.logRequest(logstring, mentionedComment, commentToEdit, numbers_combi)
                                continue
                except:
                    break
                comment_handled = self.scan_comment_and_reply(mentionedComment)
                if comment_handled:
                    message.mark_read()
                # if self.scan_comment_and_generate_reply(mentionedComment):
                #     message.mark_read()
            except:
                break

    
    def generateLinkString(self, numbersCombi):
        #generate the string that will be replied
        linkString = ""
        if numbersCombi:
            for entry in numbersCombi:
                if entry['type'] == 'redacted':
                    linkString += "This number has been redacted and therefore no link can be generated. \n\n"
                    continue
                linkString += self.processors[entry['type']].generateLinks(entry['number'])
        return linkString


    def scanPM(self, message):
        linkString = ""
        numbersCombi = self.getNumbers(message)
        numberOfInts = len(numbersCombi)
        if (numberOfInts) > 0:
            linkString += f"Here {'are' if numberOfInts > 1 else 'is'} your link{'s' if numberOfInts > 1 else ''}:\n\n"
        linkString += self.generateLinkString(numbersCombi)
        message.reply(linkString)
        message.mark_read()


    def processCommentReply(self, comment):
        numbersCombi = []
        replyString = ""
        linkString = ""
        try:
            foundParent = re.search(r'(?<=t1_).*', comment.parent_id)
        except:
            print('failure')
        if foundParent:
            parent = self.reddit.comment(foundParent.group(0))
            if parent.author.name == self.reddit.user.me() and parent.id not in postsLinked:
                numbersCombi = self.getOldResponses(parent)
        if numbersCombi:
            redacted = numbersCombi[0].get('type') == 'redacted'
            numberOfInts = len(numbersCombi) - 1 if redacted else 0
            #check if there are unrestricted numbers
            if numberOfInts > 0:
                linkString += f"Here is your link{'s' if numberOfInts > 1 else ''}:\n\n"
            linkString += self.generateLinkString(numbersCombi)
            if not redacted:
                replyString += "You have been PM'd the links to the numbers above.\n\n"
            else:
                replyString += "Restricted numbers don't get links. If there are unresticted numbers a link has been PM'd to you.\n\n"
            if (redacted and numberOfInts > 0) or not redacted:
                replyString += f"This is the first and **only** link comment I will respond to for this request to prevent clutter, if you'd also like to receive the link please [click here]({self.generateReplyLink(numbersCombi)})\n\n"
            if not redacted:
                replyString += "---\n\n"
                subReplyString = ""
                subReplyString += f"^Note: It seems like the official reddit app has issues handling pre-formatted PM links: if the above link leads you to a blank message form, you'll have to fill the fields in manually with `[Link]` as the subject and the numbers in brackets {self.generateReplyLink(numbersCombi, manualinfo=True)}.\n\n"
                replyString += re.sub(r' ', '&#32;', subReplyString)
        if linkString and replyString:
            postsLinked.append(parent.id)
            with open("linksRepliedTo.txt", "a") as f:
                f.write(parent.id + "\n")
            self.reddit.redditor(comment.author.name).message('[Link]', linkString)
            comment.reply(replyString)
            
            return True
        return False


    def getOldResponses(self, parentComment):
        numbersCombi = []
        redacted = []
        if re.search(r'\[click here\]', parentComment.body):
            return False
        parentComment = parentComment.body

        # Find and remove entries which require redaction
        parentComment = re.sub(r'\[.*?\]\(.*?\)', '', parentComment)
        print(parentComment)
        redacted = re.findall(r'&#32;\n\n', parentComment)
        parentComment = re.sub(r'(?<=>).*?(?=&#32;\n\n)', '', parentComment)
        redacted += re.findall(r'\[REDACTED\]', parentComment)
        if redacted:
            numbersCombi.append({'type': 'redacted'})

        for key, processor in self.processors.items():
            #needs to be last so that all other numbers that could match have been removed first.
            if key == 'nhentai':
                continue
            numbers, parentComment = processor.remove_and_return_old_results_from_comment(parentComment)
            numbersCombi += numbers
        numbers, parentComment = self.processors['nhentai'].remove_and_return_old_results_from_comment(parentComment)
        numbersCombi += numbers

        return numbersCombi


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
    database = Database()
    global postsLinked
    postsLinked = getSavedLinkedMessages()
    tag_bot = NHentaiTagBot(reddit, database)
    while True:
        tag_bot.runBot()

if __name__ == '__main__':
    while True:
        try:
            main()
        except Exception as e:
            print(traceback.format_exc())

# main()