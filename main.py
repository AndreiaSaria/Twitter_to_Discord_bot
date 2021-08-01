import discord
from discord.ext import commands
from discord.ext.commands import Bot
import os
import json
import requests
from keep_alive import keep_alive
import tweepy
import time
import threading

global mySentMessages
mySentMessages = []

#Here we do not use the client, we use commands https://discordpy.readthedocs.io/en/stable/ext/commands/commands.html#commands
bot = commands.Bot(command_prefix='--')

# Authenticate to Twitter
#auth = tweepy.AppAuthHandler(os.environ['USER_KEY'], os.environ['USER_SECRET'])
auth = tweepy.OAuthHandler(os.environ['USER_KEY'], os.environ['USER_SECRET'])
auth.set_access_token(os.environ['API_KEY'], os.environ['API_SECRET'])
api = tweepy.API(auth)

#https://developer.twitter.com/en/docs/twitter-api/v1/tweets/filter-realtime/overview
class tweetStream(tweepy.StreamListener):
  def on_status(self, tweet):
    if (not tweet.retweeted) and ('RT @' not in tweet.text):
      print(tweet.user.name + ": " + tweet.extended_tweet["full_text"])

      bot.dispatch("tweet",tweet)
      #In case we need the RT check this https://docs.tweepy.org/en/stable/extended_tweets.html#examples

  def on_error(self, status):
    print("Error detected " + str(status))

# Create API object
api = tweepy.API(auth, wait_on_rate_limit=True,
wait_on_rate_limit_notify=True)

tweets_listener = tweetStream(api)
stream = tweepy.Stream(api.auth, tweets_listener)
userid = api.get_user('@AndreiaSaria')
stream.filter(follow=[str(userid.id)], is_async = True)
#stream.filter(user=os.environ['NM_USER'], is_async = true)

def timer_thread(stop):
  print('before while')
  i = 0
  while True:
    if stop():
      break
    i=i+1
    print(f"Iteration number {i}")
    time.sleep(3)
    

threads = []
def set_stop(value):
  global stop_threads
  stop_threads = value

#https://stackoverflow.com/questions/64810905/emit-custom-events-discord-py
@bot.event
async def on_tweet(tweet):
  channel = bot.get_channel(869286704933114005)
  #https://github.com/tweepy/tweepy/issues/1192
  text_to_send = tweet.extended_tweet["full_text"]
  await channel.send(f"{tweet.user.name}: {text_to_send}\n \nhttps://twitter.com/{tweet.user.screen_name}/status/{tweet.id}")

@bot.event
async def on_ready():
  print('I have just logged in as {0.user}'.format(bot))
  await bot.get_channel(869286704933114005).send('Hello humans! I am the new bot in the area. --hello!')

@bot.command()
async def hello(ctx):
  print('hello recieved')
  await ctx.channel.send('Hello human.')

@bot.command()
#Send the about in quotes if it contains more than 1 word
async def public_tweet_about(ctx,rt:bool,about):
  if(rt == False):
    for tweet in tweepy.Cursor(api.search, q = about + "-filter:retweets", tweet_mode="extended").items(5):
      print(f"{tweet.user.name}: {tweet.full_text}\n \nhttps://twitter.com/{tweet.user.screen_name}/status/{tweet.id}")
      await ctx.channel.send(f"{tweet.user.name}: {tweet.full_text}\n \nhttps://twitter.com/{tweet.user.screen_name}/status/{tweet.id}")

  else:
    for tweet in tweepy.Cursor(api.search, q = about, tweet_mode="extended").items(5):
      print(f"{tweet.user.name}: {tweet.full_text}\n \nhttps://twitter.com/{tweet.user.screen_name}/status/{tweet.id}")
      await ctx.channel.send(f"{tweet.user.name}: {tweet.full_text}\n \nhttps://twitter.com/{tweet.user.screen_name}/status/{tweet.id}")


'''@bot.event
async def on_message(message):
#The command cannot come from the bot
#Just saving his messages
  if message.author == bot.user:
    if (len(mySentMessages) > 10):
      mySentMessages.pop[0]

    mySentMessages.append(message)
    return

  msg = message.content.lower()

  if(msg.startswith('hello!')):
    await message.channel.send('Hello human.')

#Method to delete a bot message
  if msg.startswith('/delete_bot_message'):
    index = int(msg.split("/delete_bot_message ",1)[1])
    #null check
    if(index is not None) and (index != ""):
      if (index > len(mySentMessages)):
        await message.channel.send('Index is higher than my saved messages or 10')
      elif (index < 0):
        await message.channel.send('No list starts with a negative number. Try 0.')
      else:
        await mySentMessages[index].delete()
    else:
      await message.channel.send('Null message detected, you must intert a number to delete the message being 10 the last.')
   


#Method to start a thread
  if msg.startswith('/start_thread'):
    channel = bot.get_channel(869286704933114005)
    await channel.send('Starting thread')

    set_stop(False)
    if (len(threads) == 0):
      p = threading.Thread(target=timer_thread, args =(lambda : stop_threads, ))
      threads.append(p)
      p.start()
    else: print('I already have a thread running')

#Method to end a thread
  if msg.startswith('/end_thread'):
    if (len(threads) != 0):
      set_stop(True)
      threads[0].join()
      threads.clear()
      print('thread killed')
    else: print('I have no thread to kill')


#Send last 5 public_tweets about input
  if msg.startswith('/public_tweet_about'):
   public_search = msg

   if(public_search is not None) and (public_search != ""):
     #Without retweets
      if('-RT' in public_search):
        public_search = public_search.split('-RT ',1)[1]
        i = 0
        for tweet in tweepy.Cursor(api.search, q = public_search).items(50):
          if (i >= 5):
            return
            if (not tweet.retweeted):
              i = i + 1
              print(f"{tweet.user.name}: {tweet.text}\n \nhttps://twitter.com/{tweet.user.screen_name}/status/{tweet.id}")
              await message.channel.send(f"{tweet.user.name}: {tweet.text}\n \nhttps://twitter.com/{tweet.user.screen_name}/status/{tweet.id}")

     #With retweets
      else:
        public_search = public_search.split("/public_tweet_about ",1)[1]
        for tweet in tweepy.Cursor(api.search, q = public_search).items(5):
          print(f"{tweet.user.name}: {tweet.text}\n \nhttps://twitter.com/{tweet.user.screen_name}/status/{tweet.id}")
          await message.channel.send(f"{tweet.user.name}: {tweet.text}\n \nhttps://twitter.com/{tweet.user.screen_name}/status/{tweet.id}")

#Starting the webserver
#keep_alive()
'''
bot.run(os.environ['TOKEN'])