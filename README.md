# Twitter_to_Discord_bot
Work in progress!

A Discord bot made in Python that gets information from twitter and transfers it to a Discord server.

It also gets random dogs/cats for you and can search for any other image on pixabay.

You can use Replit and UptimeBot to keep it alive.

Add a twitter user to follow in streaming and every post will be sent to a chosen discord channel.

## Commands:

For general commands
--bot_help

Get dogs from random.dog
--dog

Get cats from thecatapi.com
--cat

Get any image from pixabay.com
--search '"subject you want"'

Deletes a bot message with id
--delete_message '"message id"'

Only available for the users with the minimum role:


Search twitter for a specific subject/user/hashtag. 
--public_tweet_about 'Consider RT's? True/False' '"subject you want to seach"'

Get the x latest tweets from user y. 
--get_latest_tweets 'number of tweets' 'from who'

Allow latest tweet to be published in the discord.
--yes

Do not allow latest tweet to be published in the discord.
--no

Clear the array of saved tweets.
--clear

