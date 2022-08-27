import discord
from discord.ext import commands
import tweepy
import os
import requests
import aiohttp
import io
import json
from keep_alive import keep_alive
from random import randrange
import re
from urllib3.exceptions import ProtocolError
from discord.ext.commands import CommandNotFound

twitter_channel = 814638149720211516 #869286704933114005 #The discord channel to publish tweets
twitter_check_channel = 819246013277274143 #887667563457306694

global minimum_role #Minimum role to use the public_tweet_about
minimum_role = "Nerd Monkeys"

#-----AUTENTICATION-----
#Here we do not use the client, we use commands https://discordpy.readthedocs.io/en/stable/ext/commands/commands.html#commands
bot = commands.Bot(command_prefix='--', help_command=None)

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
      start_stream()
      
  def on_exception(self, exception):
    print('Exception! \n', exception)
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

#-----TWITTER BOT EVENTS-----
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

#-----TWITTER BOT COMMANDS-----
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
async def getLatestTweets(ctx, numberofitems:int, id_to_get):
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
@getLatestTweets.error
async def getLatestTweetsError(ctx,error):
  print(error)
  if isinstance(error, commands.MissingRequiredArgument):
    await ctx.channel.send('Missing required argument. \nThis is how you use this function: --getLatestTweets <number of tweets> <from who>\nAs an example: --getLatestTweets 5 Nerd_Monkeys')
  elif isinstance(error, commands.BadArgument):
    await ctx.channel.send('I could not understand how many tweets or from whom you want. Please use a number as the first parameter and a string (without spaces) as the second.')
  elif isinstance(error, commands.MissingRole):
    await ctx.channel.send('You do not have permissions to use this function. :cry:')

@bot.command()
@commands.has_role(minimum_role)
async def publicTweetAbout(ctx,rt:bool,about):
  if(rt == False):
    for tweet in tweepy.Cursor(api.search, q = about + "-filter:retweets", tweet_mode="extended").items(5):
      print(f"{tweet.user.name}: {tweet.full_text}\n \nhttps://twitter.com/{tweet.user.screen_name}/status/{tweet.id}")
      await ctx.channel.send(f"{tweet.user.name}: {tweet.full_text}\n \nhttps://twitter.com/{tweet.user.screen_name}/status/{tweet.id}")

  else:
    for tweet in tweepy.Cursor(api.search, q = about, tweet_mode="extended").items(5):
      print(f"{tweet.user.name}: {tweet.full_text}\n \nhttps://twitter.com/{tweet.user.screen_name}/status/{tweet.id}")
      await ctx.channel.send(f"{tweet.user.name}: {tweet.full_text}\n \nhttps://twitter.com/{tweet.user.screen_name}/status/{tweet.id}")
#https://discordpy.readthedocs.io/en/stable/ext/commands/commands.html#error-handling
@publicTweetAbout.error
async def publicTweetAboutError(ctx,error):
  print(error)
  if isinstance(error, commands.MissingRequiredArgument):
    await ctx.channel.send('Missing required argument. \nThis is how you use this function: --publicTweetAbout <Do you want RT? true/false> <"Search subject in quotes if contains more than one word">. \nAs an example: --publicTweetAbout false "How handsome am I?"')
  elif isinstance(error, commands.BadBoolArgument):
    await ctx.channel.send('I could not understand if you want RTs or not. If you want them type true before the subject, otherwise, type false.')
  elif isinstance(error, commands.MissingRole):
    await ctx.channel.send('You do not have permissions to use this function. :cry:')


#-----BOT EVENTS-----
@bot.event
async def on_ready():
  print('I have just logged in as {0.user}'.format(bot))
  #await bot.get_channel(twitter_channel).send('Hello humans! I am now going to post twitter updates in this channel.')


#-----BOT COMMANDS-----
@bot.command()
async def help(ctx):
  await ctx.channel.send('Commands: \n--hello \n--dog To get a random dog from random.dog api \n--cat To get a random cat from thecatapi.com \n--search "subject you want" Get any image from pixabay.com \n--search2 "subject you want" Get any image from unsplash.com \n--searchRandom <optional subject> Random image from unsplash.com \n--deleteMessage "message id" Deletes a bot message with id\n--listAllBouas \nOnly available for Nerd Monkeys: \n--publicTweetAbout <Do you want RT? true/false> <"Search subject in quotes if contains more than one word"> \n--get_latest_tweets <number of tweets> <from who>\n--yes To send the tweet \n--no To not send the tweet\n--clear Clear array of saved tweets\n--newBouas "Your new Bouas call!"\n--readBouasFile\n--rewriteBouasFile "All of the bouas here, separated by ¨"')

@bot.command()
async def hello(ctx):
  await ctx.channel.send('Hello human.')

@bot.command()
async def deleteMessage(ctx, msgID: int):
  msg = await ctx.fetch_message(msgID)
  if msg.author == bot.user:
    await msg.delete()
    print(f'Deleted message {msgID}')
  else:
    await ctx.channel.send("I was not the author of this message!")  

@bot.command()
#Dog only possible by random.dog
async def dog(ctx):
  temp = requests.get("https://random.dog/woof?") #woof?filter or woof?include to filter files.
  dogFileName = temp.text
  dogUrl = "https://random.dog/" + dogFileName
  print(dogUrl)
  await SendImage(ctx, dogUrl, dogFileName)
@dog.error
async def dog_error(ctx,error):
  print(error)
  await ctx.channel.send("Something went wrong... :cry: For curious devs here's the error " + error)

@bot.command()
#Cat command only possible by thecatapi.com
async def cat(ctx):
  temp = requests.get("https://api.thecatapi.com/v1/images/search", headers={"x-api-key":os.environ['CAT_API_KEY']})
  jsonData = json.loads(temp.text)
  catUrl = jsonData[0]['url']
  print(catUrl)
  catFileName = catUrl.split("/images/",1)[1]
  await SendImage(ctx, catUrl, catFileName)
@cat.error
async def cat_error(ctx, error):
  print(error)
  await ctx.channel.send("Something went wrong... :cry: For curious devs here's the error " + error)

@bot.command()
async def search(ctx, name):
  temp = requests.get("https://pixabay.com/api/", params={"key":os.environ['PIXABAY_KEY'],"q":name})
  jsonData = json.loads(temp.text)
  imageList = [i['largeImageURL'] for i in jsonData['hits']]

  if len(imageList) == 0:
    await ctx.channel.send('No image found matching this term on pixabay, now using unsplash...')
    await search2(ctx, name)
    return
  
  imageUrl = imageList[randrange(len(imageList))]
  print(imageUrl)
  imageFileName = imageUrl.split("/get/",1)[1]
  await SendImage(ctx, imageUrl, imageFileName)
@search.error
async def search_error(ctx,error):
  print(error)
  await ctx.channel.send("Something went wrong... :cry: For curious devs here's the error " + error)
  if isinstance(error, commands.MissingRequiredArgument):
    await ctx.channel.send('Missing required argument. \nThis is how you use this function: --search <"Search subject in quotes if contains more than one word">. \nAs an example: --search "Blue flower"')

@bot.command()
async def search2(ctx, name):
  temp = requests.get("https://api.unsplash.com/search/photos", params={"client_id":os.environ['UNSPLASH_KEY'],"query":name,"per_page":30})
  jsonData = json.loads(temp.text)
  
  urlsList = [i['urls'] for i in jsonData['results']]
  imageList = [i['full'] for i in urlsList]

  if len(imageList) == 0:
    await ctx.channel.send('No image found matching this term. :cry:')
    return
    
  imageUrl = imageList[randrange(len(imageList))]
  print(imageUrl)
  imageFileName = "SeemsLikeThisAPIOnlyGivesMeJpg.jpg"
  await SendImage(ctx, imageUrl, imageFileName)
@search2.error
async def search2_error(ctx, error):
  print(error)
  await ctx.channel.send("Something went wrong... :cry: For curious devs here's the error " + error)
  if isinstance(error, commands.MissingRequiredArgument):
    await ctx.channel.send('Missing required argument. \nThis is how you use this function: --search2 <"Search subject in quotes if contains more than one word">. \nAs an example: --search2 "Blue flower"')

@bot.command()
async def searchRandom(ctx, name = ""):
  temp = requests.get("https://api.unsplash.com/photos/random", params={"client_id":os.environ['UNSPLASH_KEY'],"query":name})
  jsonData = json.loads(temp.text)
  if('errors' in jsonData):
    await ctx.channel.send('No image found matching this term. :cry:')
    return
    
  imageUrl = jsonData['urls']['full']
  print(imageUrl)
  imageFileName = "SeemsLikeThisAPIOnlyGivesMeJpg.jpg"
  await SendImage(ctx, imageUrl, imageFileName)

@bot.command()
@commands.has_role(minimum_role)
async def newBouas(ctx, newBouas):
  SetNewBouas(newBouas)
  await ctx.channel.send('New Bouas is set')
@newBouas.error
async def newBouasError(ctx, error):
  print(error)
  if isinstance(error, commands.MissingRole):
    await ctx.channel.send('You do not have permissions to use this function. :cry:')
  
@bot.command()
async def listAllBouas(ctx):
  await ctx.channel.send(ListAllBouas())

@bot.command()
@commands.has_role(minimum_role)
async def readBouasFile(ctx):
  await ctx.channel.send(ReadBouasFile())
@readBouasFile.error
async def readBouasFileError(ctx, error):
  print(error)
  if isinstance(error, commands.MissingRole):
    await ctx.channel.send('You do not have permissions to use this function. :cry:')

@bot.command()
@commands.has_role(minimum_role)
async def rewriteBouasFile(ctx, newText):
  RewriteBouasFile(newText)
@rewriteBouasFile.error
async def rewriteBouasFileError(ctx, error):
  print(error)
  if isinstance(error, commands.MissingRole):
    await ctx.channel.send('You do not have permissions to use this function. :cry:')

  
#-----BOT LISTEN-----
#https://stackoverflow.com/questions/53705633/how-to-use-discord-bot-commands-and-event-both
integer_num = 0
@bot.listen()
async def on_message(message):
#The message cannot come from the bot
  lowerCaseMsg = message.content.lower()
  if message.author == bot.user:
    return
  
  if lowerCaseMsg.startswith('hello bot'):
    await message.channel.send('Hello human!')

  if 'estágio' in lowerCaseMsg or 'estagiar' in lowerCaseMsg or 'internship' in lowerCaseMsg or 'estagio' in lowerCaseMsg:
    await message.channel.send('internship@nerdmonkeys.pt')
  
  if lowerCaseMsg.startswith('boas') or lowerCaseMsg.startswith('bouas') or lowerCaseMsg.startswith('buenos'):
    global integer_num
    integer_num += 1
    print(integer_num)
    if (integer_num == 3):
      integer_num = 0
      await message.channel.send(BouasOfTheDay())

      
#-----General purpose methods-----
def ReadBouasFile():
  bouasFile = open("bouasFile.txt","r")
  content = bouasFile.read()
  bouasFile.close()
  return content

def ListAllBouas():
  bouasPhrases = ReadBouasFile().split("¨")
  return bouasPhrases
  
def BouasOfTheDay():
  bouasList = ListAllBouas()
  return bouasList[randrange(len(bouasList))]

def SetNewBouas(newBouas):
  bouasFile = open("bouasFile.txt","a")
  bouasFile.write("¨"+newBouas)
  bouasFile.close()

def RewriteBouasFile(textFile):
  bouasFile = open("bouasFile.txt","w")
  bouasFile.write(textFile)
  bouasFile.close()

async def SendImage(ctx, imageUrl, imageFileName):
  async with aiohttp.ClientSession() as session:
    async with session.get(imageUrl) as resp:
      if resp.status != 200:
        return await ctx.send('Could not get your image...')
      data = io.BytesIO(await resp.read())
      await ctx.channel.send(file=discord.File(data, imageFileName))
  
#-----STARTING WEB SERVER-----
keep_alive()
#bot.run(os.environ['MYSERVERTOKEN'])
bot.run(os.environ['NMTOKEN'])