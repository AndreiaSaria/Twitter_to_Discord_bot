# Twitter_to_Discord_bot
Work in progress!

A Discord bot made in Python that gets information from twitter and transfers it to a Discord server.
It also gets random dogs/cats for you and plays youtube audio!
You can use Replit and UptimeBot to keep it alive, the code is commented, currently I'm using a virtual machine.

Add a twitter user to follow in streaming and every post will be sent to a chosen discord channel.

There are also some functions:

For general commands
--bot_help

Get dogs from random.dog
--dog

Get cats from thecatapi.com
--cat

Play youtube audio 
--play <URL>
  
Pause audio
--pause
  
Resume
--resume
  
Leave voice channel
--leave

Only available for the users with the minimum role:
Search twitter for a specific subject/user/hashtag.
--public_tweet_about <Consider RT's? True/False> <"subject you want to seach">

Get the latest tweets from the specified used in the twitter stream.
--get_last_tweets <number of tweets>

Allow latest tweet to be published in the discord.
--yes

Do not allow latest tweet to be published in the discord.
--no

