import discord
from discord.ext import commands
import tweepy
import os
import requests
import aiohttp
import io
#from keep_alive import keep_alive
import youtube_dl
import re
from urllib3.exceptions import ProtocolError

global twitter_channel #The discord channel to publish tweets
twitter_channel = 869286704933114005 #814638149720211516 

global minimum_role #Minimum role to use the public_tweet_about
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
    try:
      if (not tweet.retweeted) and ('RT @' not in tweet.text) and (userid.id == tweet.user.id):
        print(tweet.user.name + ": " + tweet.text)
        bot.dispatch("tweet",tweet)
      
        #In case we need the RT check this https://docs.tweepy.org/en/stable/extended_tweets.html#examples
    except ProtocolError:
      print("PrototcolError")

  def on_error(self, status):
    print("Error detected " + str(status))

api = tweepy.API(auth, wait_on_rate_limit=True,
wait_on_rate_limit_notify=True)

tweets_listener = tweetStream(api)
stream = tweepy.Stream(api.auth, tweets_listener)

#userid = api.get_user('@Nerd_Monkeys')
userid = api.get_user('@AndreiaSaria')
stream.filter(follow=[str(userid.id)], is_async = True)


#-----BOT EVENTS-----
#https://stackoverflow.com/questions/64810905/emit-custom-events-discord-py
@bot.event
async def on_tweet(tweet):
  channel = bot.get_channel(twitter_channel)
  #https://stackoverflow.com/questions/52431763/how-to-get-full-text-of-tweets-using-tweepy-in-python
  if 'extended_tweet' in tweet._json: 
    tweet_full_text = tweet._json['extended_tweet']['full_text']
  else:
    tweet_full_text = tweet.text

  #https://stackoverflow.com/questions/63555168/excluding-link-at-the-end-while-pulling-tweets-in-tweepy-streaming
  text_to_send = re.sub(r' https://t.co/\w{10}', '', tweet_full_text)

  #https://github.com/tweepy/tweepy/issues/1192
  await channel.send(f"{tweet.user.name}: {text_to_send}\n \nhttps://twitter.com/{tweet.user.screen_name}/status/{tweet.id}")

@bot.event
async def on_ready():
  print('I have just logged in as {0.user}'.format(bot))
  #await bot.get_channel(twitter_channel).send('Hello humans! I am now going to post twitter updates in this channel.')

@bot.command()
async def bot_help(ctx):
  await ctx.channel.send('--hello \n--dog To get a random dog from random.dog api \n--play <Youtube URL> to play the sound on a voice channel\n--pause to pause audio \n--resume to resume audio \n--leave to leave the voice channel \n--public_tweet_about <Do you want RT? true/false> <"Search subject in quotes if contains more than one word"> This is only available for Nerd Monkeys')

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
  print(error)
  await ctx.channel.send('OOps, we had an error, no dogs for you :(')

#https://stackoverflow.com/questions/64725932/discord-py-send-a-message-if-author-isnt-in-a-voice-channel
#https://stackoverflow.com/questions/61900932/how-can-you-check-voice-channel-id-that-bot-is-connected-to-discord-py
#https://www.youtube.com/watch?v=ml-5tXRmmFk

#do this https://stackoverflow.com/questions/66610012/discord-py-streaming-youtube-live-into-voice
@bot.command()
async def play(ctx, url : str):
  song_there = os.path.isfile("song.mp3")
  try:
    if song_there:
      os.remove("song.mp3")
  except PermissionError:
    await ctx.send("Wait for current music to end or use the --stop command")
    return

  voiceChannel = ctx.author.voice
  if voiceChannel:
    voiceChannel = ctx.author.voice.channel
    await voiceChannel.connect()
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)

    ydl_opts = {
      'format': 'bestaudio/best',
      'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
      }],
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
      ydl.download([url])
    for file in os.listdir("./"):
      if file.endswith(".mp3"):
        os.rename(file,"song.mp3")
    voice.play(discord.FFmpegPCMAudio("song.mp3"))
  else:
    print('No voice channel')

@bot.command()
async def leave(ctx):
  voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
  if voice.is_connected:
    await voice.disconnect()
  else:
    await ctx.send('Bot is not on a voice channel')

@bot.command()
async def pause(ctx):
  voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
  if voice.is_playing():
    voice.pause()
  else:
    await ctx.send('No audio playing.')

@bot.command()
async def resume(ctx):
  voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
  if voice.is_paused():
    voice.resume()
  else:
    await ctx.send('The audio is not paused.')

@bot.command()
async def stop(ctx):
  voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
  voice.stop()

#Starting the webserver
#keep_alive()
bot.run(os.environ['MYSERVERTOKEN'])
#bot.run(os.environ['NMTOKEN'])