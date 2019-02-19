# nHentai-Tag-Bot
A Reddit bot that gives information about doujins.

# Features
In the scanned subreddits you can automatically request the tags for a doujin from nHentai, Tsumino, and E-Hentai. In unscanned subreddits you can call the bot by username mention.

# Usage
For nHentai galleries you need to put the gallery number in parentheses, while padding it with leading zeroes to have at least 5 digits. For example: (123456) or (00001)

For Tsumino galleries you need to put the gallery number in inverted parentheses, while padding it with leading zeroes to have at least 5 digits. For example: )12345( or )00002(

For E-Hentai galleries you need to put the gallery number and token in inverted curly brackets separated by a forward slash. For example: }618395/0439fa3666{

For Hitomo.la galleries you need to put the gallery number between exclamation points, while padding with with leading zeroes to have at least 5 digits. For example !1234567! or !04321!

The bot can also scan URLs from any of the aforementioned sites by including the keyword !tags with the URL in a comment. A comment reply with the keyword will also trigger the scanning of the URLs.

---

# Running the Bot

To run the bot yourself you need to create a praw.ini file with the login information in accordance to the praw documentation. The identifier can be changed within the `authenticate()` method. After that the bot is ready to run, but I would ask that you would change the scanned subreddits in the `PARSED_SUBREDDIT` to prevent your instance from replying to all the same comments the bot is already replying to.