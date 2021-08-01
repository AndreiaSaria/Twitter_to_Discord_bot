import discord
from discord.ext import commands
import os
import aiohttp
import io
import requests
from keep_alive import keep_alive
import tweepy

global twitter_channel
twitter_channel = 869286704933114005
global minimum_role
minimum_role = "Nerd Monkeys"

#-----Autentication-----
#Here we do not use the client, we use commands https://discordpy.readthedocs.io/en/stable/ext/commands/commands.html#commands
bot = commands.Bot(command_prefix='--')

# Authenticate to Twitter
#auth = tweepy.AppAuthHandler(os.environ['USER_KEY'], os.environ['USER_SECRET'])
#Since we use Streaming tweets we need to use this other auth:
auth = tweepy.OAuthHandler(os.environ['USER_KEY'], os.environ['USER_SECRET'])
auth.set_access_token(os.environ['API_KEY'], os.environ['API_SECRET'])
api = tweepy.API(auth)


#-----Tweet stream-----
#https://developer.twitter.com/en/docs/twitter-api/v1/tweets/filter-realtime/overview
class tweetStream(tweepy.StreamListener):
  def on_status(self, tweet):
    if (not tweet.retweeted) and ('RT @' not in tweet.text):
      print(tweet.user.name + ": " + tweet.extended_tweet["full_text"])

      bot.dispatch("tweet",tweet)
      #In case we need the RT check this https://docs.tweepy.org/en/stable/extended_tweets.html#examples

  def on_error(self, status):
    print("Error detected " + str(status))

api = tweepy.API(auth, wait_on_rate_limit=True,
wait_on_rate_limit_notify=True)

tweets_listener = tweetStream(api)
stream = tweepy.Stream(api.auth, tweets_listener)
#Following myself for the sake of testing
#userid = api.get_user('@AndreiaSaria')
#stream.filter(follow=[str(userid.id)], is_async = True)
stream.filter(follow=os.environ['NM_USER'], is_async = True)


#-----BOT EVENTS-----
#https://stackoverflow.com/questions/64810905/emit-custom-events-discord-py
@bot.event
async def on_tweet(tweet):
  channel = bot.get_channel(twitter_channel)
  #https://github.com/tweepy/tweepy/issues/1192
  text_to_send = tweet.extended_tweet["full_text"]
  await channel.send(f"{tweet.user.name}: {text_to_send}\n \nhttps://twitter.com/{tweet.user.screen_name}/status/{tweet.id}")

@bot.event
async def on_ready():
  print('I have just logged in as {0.user}'.format(bot))
  await bot.get_channel(twitter_channel).send('Hello humans! I am now going to post twitter updates in this channel.')

@bot.command()
async def bot_help(ctx):
  await ctx.channel.send('--hello \n--dog To get a random dog from random.dog api\n--public_tweet_about <Do you want RT? true/false> <"Search subject in quotes if contains more than one word"> This is only available for Nerd Monkeys')

@bot.command()
async def hello(ctx):
  await ctx.channel.send('Hello human.')

@bot.command()
@commands.has_role(minimum_role)
async def public_tweet_about(ctx,rt:bool,about):
  if(rt == False):
    for tweet in tweepy.Cursor(api.search, q = about + "-filter:retweets", tweet_mode="extended").items(5):
      print(f"{tweet.user.name}: {tweet.full_text}\n \nhttps://twitter.com/{tweet.user.screen_name}/status/{tweet.id}")
      await ctx.channel.send(f"{tweet.user.name}: {tweet.full_text}\n \nhttps://twitter.com/{tweet.user.screen_name}/status/{tweet.id}")

  else:
    for tweet in tweepy.Cursor(api.search, q = about, tweet_mode="extended").items(5):
      print(f"{tweet.user.name}: {tweet.full_text}\n \nhttps://twitter.com/{tweet.user.screen_name}/status/{tweet.id}")
      await ctx.channel.send(f"{tweet.user.name}: {tweet.full_text}\n \nhttps://twitter.com/{tweet.user.screen_name}/status/{tweet.id}")
#https://discordpy.readthedocs.io/en/stable/ext/commands/commands.html#error-handling
@public_tweet_about.error
async def public_tweet_about_error(ctx,error):
  print(error)
  if isinstance(error, commands.MissingRequiredArgument):
    await ctx.channel.send('Missing required argument. \nThis is how you use this function: --public_tweet_about <Do you want RT? true/false> <"Search subject in quotes if contains more than one word">. \nAs an example: --public_tweet_about false "How handsome am I?"')
  elif isinstance(error, commands.BadBoolArgument):
    await ctx.channel.send('I could not understand if you want RTs or not. If you want them type true after the function call, otherwise, type false.')
  elif isinstance(error, commands.MissingRole):
    await ctx.channel.send('You do not have permissions to use this function. \nSorry.')

@bot.command()
#Dog only possible by random.dog, maybe add a webm, png, jpeg filter in the parameters
async def dog(ctx):
  temp = requests.get("https://random.dog/woof?filter=mp4")
  dogfilename = temp.text
  print("https://random.dog/"+dogfilename)
  async with aiohttp.ClientSession() as session:
    async with session.get("https://random.dog/"+dogfilename) as resp:
        if resp.status != 200:
          return await ctx.send('Could not get dog...')
        data = io.BytesIO(await resp.read())
        await ctx.channel.send(file=discord.File(data, dogfilename))
@dog.error
async def dog_error(ctx,error):
  await ctx.channel.send('OOps, no dogs for you, error:' +error)

#https://stackoverflow.com/questions/64725932/discord-py-send-a-message-if-author-isnt-in-a-voice-channel
#https://stackoverflow.com/questions/61900932/how-can-you-check-voice-channel-id-that-bot-is-connected-to-discord-py
#https://www.youtube.com/watch?v=ml-5tXRmmFk
@bot.command()
async def play(ctx):#, url : str):
  voiceChannel = ctx.author.voice
  if voiceChannel:
    voiceChannel = ctx.author.voice.channel
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    await voiceChannel.connect()

  else:
    print('No voice channel')


#Starting the webserver
#keep_alive()
bot.run(os.environ['TOKEN'])