import discord
from discord.ext import commands
import tweepy
import os
import requests
import aiohttp
import io
import json
#from keep_alive import keep_alive
import youtube_dl
import re
from urllib3.exceptions import ProtocolError
import asyncio
 
twitter_channel = 869286704933114005 #814638149720211516 #The discord channel to publish tweets
twitter_check_channel = 887667563457306694 #819246013277274143

global minimum_role #Minimum role to use the public_tweet_about
minimum_role = "Nerd Monkeys"

#-----AUTENTICATION-----
#Here we do not use the client, we use commands https://discordpy.readthedocs.io/en/stable/ext/commands/commands.html#commands
bot = commands.Bot(command_prefix='--')

# Authenticate to Twitter
#auth = tweepy.AppAuthHandler(os.environ['USER_KEY'], os.environ['USER_SECRET'])
#Since we use Streaming tweets we need to use this other auth:
auth = tweepy.OAuthHandler(os.environ['USER_KEY'], os.environ['USER_SECRET'])
auth.set_access_token(os.environ['API_KEY'], os.environ['API_SECRET'])
api = tweepy.API(auth)


#-----TWITTER-----
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
      bot.dispatch("lost_tweet", "Protocol error, restarting stream. The latest tweet may be lost. (use --get_last_tweets <number of tweets> to try and catch the lost ones)")
      start_stream()
      
  def on_exception(self, exception):
    print('Exception! \n', exception)
    bot.dispatch("lost_tweet", "Exception! Restarting stream. The latest tweet may be lost. (use --get_last_tweets <number of tweets> to try and catch the lost ones)")
    start_stream()

api = tweepy.API(auth, wait_on_rate_limit=True,
wait_on_rate_limit_notify=True)

tweets_listener = tweetStream(api)
stream = tweepy.Stream(api.auth, tweets_listener)

userid = api.get_user('@Nerd_Monkeys')
#userid = api.get_user('@AndreiaSaria')
#userid = api.get_user('@IGN')

def start_stream():
    stream.filter(follow=[str(userid.id)], is_async = True, stall_warnings=True) #here's where the stream starts
    
start_stream()
    
tweetArray = []
#https://stackoverflow.com/questions/64810905/emit-custom-events-discord-py
@bot.event
async def on_tweet(tweet):
  print(tweet)
  channel = bot.get_channel(twitter_check_channel)

  if 'extended_tweet' in tweet._json: 
    tweet_full_text = tweet._json['extended_tweet']['full_text']
  else:
    tweet_full_text = tweet.text

  #https://stackoverflow.com/questions/63555168/excluding-link-at-the-end-while-pulling-tweets-in-tweepy-streaming
  text_to_send = re.sub(r' https://t.co/\w{10}', '', tweet_full_text)
  tweetArray.append(f"{tweet.user.name}: {text_to_send}\n \nhttps://twitter.com/{tweet.user.screen_name}/status/{tweet.id}")

  await channel.send(tweetArray[0])
  await channel.send(f"Should I send this message to the twitter channel?")

@bot.event
async def on_lost_tweet(text_to_send):
  await bot.get_channel(twitter_check_channel).send(text_to_send)

@bot.command()
@commands.has_role(minimum_role)
async def yes(ctx):
  check_channel = bot.get_channel(twitter_check_channel)

  if(ctx.channel == check_channel):
    if(len(tweetArray) > 0):
      await check_channel.send("Sending tweet to social media feeds channel.")
      await bot.get_channel(twitter_channel).send(tweetArray[0])
      del tweetArray[0]
      if(len(tweetArray) > 0):
        await check_channel.send(tweetArray[0])
        await check_channel.send(f"Should I send this message to the twitter channel?")
    else:
      await check_channel.send("What are you doing? I have no tweets to send.")
  else:
    print("yes command, in the wrong channel")

@bot.command()
@commands.has_role(minimum_role)
async def no(ctx):
  check_channel = bot.get_channel(twitter_check_channel)

  if(ctx.channel == check_channel):
    if(len(tweetArray) > 0):
      await check_channel.send("Ok, I will not send this tweet.")
      del tweetArray[0]
      if(len(tweetArray) > 0):
        await check_channel.send(tweetArray[0])
        await check_channel.send(f"Should I send this message to the twitter channel?")
    else:
      await check_channel.send("What are you doing? I have no tweets to send.")
  else:
    print("no command, in the wrong channel.")

@bot.command()
@commands.has_role(minimum_role)
async def clear(ctx):
  check_channel = bot.get_channel(twitter_check_channel)

  if(ctx.channel == check_channel):
    if(len(tweetArray) > 0):
      del tweetArray[:]
      await check_channel.send("Cleared array of saved tweets.")
    else:
      await check_channel.send("What are you doing? I have no tweets to delete.")

@bot.command()
@commands.has_role(minimum_role)
async def get_latest_tweets(ctx, numberofitems:int, id_to_get):
  channel = bot.get_channel(twitter_check_channel)

  if(ctx.channel == channel):
    for tweet in tweepy.Cursor(api.user_timeline,id=id_to_get, include_rts=False, tweet_mode="extended").items(numberofitems):
      tweet_full_text = tweet._json['full_text']
      text_to_send = re.sub(r' https://t.co/\w{10}', '', tweet_full_text)
      tweetArray.append(f"{tweet.user.name}: {text_to_send}\n \nhttps://twitter.com/{tweet.user.screen_name}/status/{tweet.id}")
    await channel.send(tweetArray[0])
    await channel.send(f"Should I send this message to the twitter channel?")  
  else:
    print("Get latest tweets command in the wrong channel.")
@get_latest_tweets.error
async def get_latest_tweets_error(ctx,error):
  print(error)
  if isinstance(error, commands.MissingRequiredArgument):
    await ctx.channel.send('Missing required argument. \nThis is how you use this function: --get_latest_tweets <number of tweets> <from who>\nAs an example: --get_latest_tweets 5 Nerd_Monkeys')
  elif isinstance(error, commands.BadArgument):
    await ctx.channel.send('I could not understand how many tweets or from whom you want. Please use a number as the first parameter and a string (without spaces) as the second.')
  elif isinstance(error, commands.MissingRole):
    await ctx.channel.send('You do not have permissions to use this function. \nSorry.')

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



#-----BOT EVENTS-----
@bot.event
async def on_ready():
  print('I have just logged in as {0.user}'.format(bot))
  #await bot.get_channel(twitter_channel).send('Hello humans! I am now going to post twitter updates in this channel.')


#-----BOT COMMANDS-----
@bot.command()
async def bot_help(ctx):
  await ctx.channel.send('--hello \n--dog To get a random dog from random.dog api \n --cat To get a random cat from thecatapi.com \n--play <Youtube URL> to play the sound on a voice channel\n--pause to pause audio \n--resume to resume audio \n--leave to leave the voice channel \nOnly available for Nerd Monkeys: \n--public_tweet_about <Do you want RT? true/false> <"Search subject in quotes if contains more than one word"> \n--get_last_tweets <number of tweets> \n--yes To send the tweet \n--no To not send the tweet')

@bot.command()
async def hello(ctx):
  await ctx.channel.send('Hello human.')

@bot.command()
#Dog only possible by random.dog
async def dog(ctx):
  temp = requests.get("https://random.dog/woof?") #woof?filter or woof?include to filter files.
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
  await dog(ctx) #call again when error

@bot.command()
#Cat command only possible by thecatapi.com
async def cat(ctx):
  temp = requests.get("https://api.thecatapi.com/v1/images/search", headers={"x-api-key":os.environ['CAT_API_KEY']})
  json_data = json.loads(temp.text)
  cat = json_data[0]['url']
  catfilename = cat.split("/images/",1)[1]
  print(cat)
  async with aiohttp.ClientSession() as session:
    async with session.get(cat) as resp:
        if resp.status != 200:
          return await ctx.send('Could not get cat...')
        data = io.BytesIO(await resp.read())
        await ctx.channel.send(file=discord.File(data, catfilename))
@cat.error
async def cat_error(ctx,error):
  print(error)
  await cat(ctx) #call again when error


#-----BOT LISTEN-----
#https://stackoverflow.com/questions/53705633/how-to-use-discord-bot-commands-and-event-both
integer_num = 0
@bot.listen()
async def on_message(message):
#The message cannot come from the bot
  lowerCaseMsg = message.content.lower()
  if message.author == bot.user:
    return

  if lowerCaseMsg.startswith('boas') or lowerCaseMsg.startswith('bouas') or lowerCaseMsg.startswith('buenos'):
    global integer_num
    integer_num += 1
    print(integer_num)
    if (integer_num == 3):
      integer_num = 0
      await message.channel.send('BOUAS!')
  
  if lowerCaseMsg.startswith('hello bot'):
    await message.channel.send('Hello human!')




#-----BOT MUSIC PLAY (VERY EARLY VER)-----
#https://stackoverflow.com/questions/64725932/discord-py-send-a-message-if-author-isnt-in-a-voice-channel
#https://stackoverflow.com/questions/61900932/how-can-you-check-voice-channel-id-that-bot-is-connected-to-discord-py
#https://www.youtube.com/watch?v=ml-5tXRmmFk

#do this https://stackoverflow.com/questions/66610012/discord-py-streaming-youtube-live-into-voice
#https://github.com/Rapptz/discord.py/blob/master/examples/basic_voice.py
youtube_dl.utils.bug_reports_message = lambda: ''
ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn'
}
ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


@bot.command()
async def join(ctx):
  """Joins a voice channel"""
  voiceChannel = ctx.author.voice
  if voiceChannel:
    voiceChannel = ctx.author.voice.channel
    await voiceChannel.connect()
    #voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)

@bot.command()
async def play(ctx, *, query):
  """Plays a file from the local filesystem"""

  source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(query))
  ctx.voice_client.play(source, after=lambda e: print(f'Player error: {e}') if e else None)

  await ctx.send(f'Now playing: {query}')

@bot.command()
async def yt(ctx, *, url):
  """Plays from a url (almost anything youtube_dl supports)"""

  async with ctx.typing():
    player = await YTDLSource.from_url(url, loop=bot.loop)
    ctx.voice_client.play(player, after=lambda e: print(f'Player error: {e}') if e else None)

  await ctx.send(f'Now playing: {player.title}')

@bot.command()
async def stream(ctx, *, url):
  """Streams from a url (same as yt, but doesn't predownload)"""

  async with ctx.typing():
    player = await YTDLSource.from_url(url, loop=bot.loop, stream=True)
    ctx.voice_client.play(player, after=lambda e: print(f'Player error: {e}') if e else None)

  await ctx.send(f'Now playing: {player.title}')

''''    @bot.command()
    async def volume(self, ctx, volume: int):
        """Changes the player's volume"""

        if ctx.voice_client is None:
            return await ctx.send("Not connected to a voice channel.")

        ctx.voice_client.source.volume = volume / 100
        await ctx.send(f"Changed volume to {volume}%")

    @bot.command()
    async def stop(self, ctx):
        """Stops and disconnects the bot from voice"""

        await ctx.voice_client.disconnect()

    @play.before_invoke
    @yt.before_invoke
    @stream.before_invoke
    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("You are not connected to a voice channel.")
                raise commands.CommandError("Author not connected to a voice channel.")
        elif ctx.voice_client.is_playing():
            ctx.voice_client.stop()
'''

'''@bot.command()
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
  voice.stop()'''



#-----STARTING WEB SERVER-----
#keep_alive()
bot.run(os.environ['MYSERVERTOKEN'])
#bot.run(os.environ['NMTOKEN'])