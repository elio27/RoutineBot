import discord
import re, os, requests, json
from keep_alive import keep_alive
import difflib
import html
from PIL import Image
from io import BytesIO

client = discord.Client()

def footer(message):
	footer = f"*Automatic reply from @RoutineBot to {message.author.name} (message_id={message.id})*"
	return footer


def is_valid(rhid):
	response = requests.get(
	    f"https://routinehub.co/api/v1/shortcuts/{rhid}/versions/latest")
	json_data = json.loads(response.text)
	return json_data['result'] == "success"


def get_name(rhid):
	response = requests.get(f"https://routinehub.co/shortcut/{rhid}")
	ex = '(?<=<h3 class="title is-3">).*(?=</h3>)'
	return re.findall(ex, response.text)[0]

def search(name, mode=0):
  name = name.replace(" ", "+")
  response = requests.get(f'https://routinehub.co/search/?q={name}')

  ex = '(?<=href="/shortcut/).*(?=/">)'
  matches = re.findall(ex, response.text)

  ex = "(?<=<strong>).*(?=</strong>)"
  names = re.findall(ex, response.text)

  stop_at_ten = 0
  id = ""
  if mode == 0:
    for i in range(len(matches)):
      id = matches[i]
      i_name = html.unescape(names[i])
      if difflib.SequenceMatcher(None, i_name, name).ratio() > 0.7:
        break
    return id
    
  else:
    message = ""
    if len(matches) == 0:
      message = f"RoutineBot cannot find any result for {name}"

    for i in range(len(matches)):
      stop_at_ten += 1
      if stop_at_ten == 6:
        break
      else:
        id = matches[i]
        name = html.unescape(names[i])
        message += f"[{name}](https://routinehub.co/shortcut/{id}): {id}\n"
    return message


@client.event
async def on_ready():
  print("Present in:\n")
  for guild in client.guilds:
    print(f"{guild.name}")
  print("-----------------")
  await client.change_presence(activity=discord.Game(name=f"!rh help in {len(client.guilds)} servers"))


@client.event
async def on_member_join(member):
	channel = client.get_channel(503976650996842507)
	await channel.send(
	    f"Welcome <@{member.id}> and thank you for joining us! We are now {member.guild.member_count} in this server !"
	)


@client.event
async def on_raw_reaction_add(payload):
	channel = client.get_channel(payload.channel_id)
	msg = await channel.fetch_message(payload.message_id)

	try:
		id = re.findall("(?<=message_id=).*(?=\))", msg.content)[0].replace(
		    ").", "")
		id = id.replace(id[-1], "")

	except IndexError:
		id = re.findall("(?<=message_id=).*(?=\)\*)",
		                msg.embeds[0].footer.text)[0]

	msbis = await channel.fetch_message(id)

	if payload.user_id == msbis.author.id:
		await msg.delete()
		await msbis.delete()

@client.event
async def on_message(message):
  if message.author == client.user:
    if message.content and message.content.endswith(")"):
      await message.add_reaction("🗑")
    else:
      if len(message.embeds) > 0  and not message.content == "https://bit.ly/rh-bot":
        await message.add_reaction("🗑")
  if message.content == "!rh help":
    embed = discord.Embed(
    colour = discord.Colour(0x299d68),
    description="Hello and welcome to the RoutineBot help page !")
    embed.set_footer(
      text=f"{footer(message)}",
      icon_url=
      "https://cdn.discordapp.com/avatars/792855846240518174/946eb210985c413d6b1429d49f9168fc.png?size=512")
    embed.add_field(name="**Main Commands :**",value= "**!rh shortcut {RH ID / Name}**\n*Returns the author, amount of downloads and heart of a shortcut, the last version, the release date and a direct link to download it*\n\n**!rh search {shortcut's name}**\n*Returns a list of 5 results and their id for a or several keywords*\n\n**!rh user {username}**\n*Return the number of shortcuts, downloads and hearts of a shortcut creator.*\n\n")

    embed.add_field(
        name="\n\n**Other commands :**",
        value=
        "\n\n**!rh invite**\n*Returns the [link](https://bit.ly/rh-bot) to invite me on your server !*\n\n**!rh help**\n*Returns the help page you are reading*\n\n\n"
    )
    embed.add_field(name="**Credits :**", value="Here is a little message to thank those who contributed to RoutineBot, one way or another, by reporting bugs or suggested improvements.\nI am talking about <@360097325730889730>, <@575317218955493376>, <@618082876730376202>, <@714777087801819237>, <@642358695652753418> and <@293502958950154240>.")
    await message.channel.send(embed=embed)

  elif message.content.startswith("!rh invite"):
    await message.channel.send("https://bit.ly/rh-bot\n")

  elif message.content.startswith("!rh search"):
    name = message.content.replace("!rh search ", "")
    loading = await message.channel.send("Routinebot is loading your request")
    async with message.channel.typing():
      mess = search(name, mode=1)
      await loading.delete()
      embed = discord.Embed(colour=discord.Colour(0x299d68))
      embed.set_footer(
            text=f"{footer(message)}",
            icon_url=
            "https://cdn.discordapp.com/avatars/792855846240518174/946eb210985c413d6b1429d49f9168fc.png?size=512")
      if not f"RoutineBot cannot find any result for {name}" in mess:
        embed.add_field(name=f"Results for {name} :",value=mess)
      else:
        embed.add_field(name="<:error:805061336185831434> Error <:error:805061336185831434>",value=mess)
      
    await message.channel.send(embed=embed)
 

  elif message.content.startswith("!rh shortcut"):
    rhid = message.content.replace("!rh shortcut ", "")
    loading = await message.channel.send("Routinebot is loading your request")
    async with message.channel.typing():
      try:
        int(rhid)
      except ValueError:
        rhid = search(rhid)
      if rhid and is_valid(rhid):
        response = requests.get(f"https://routinehub.co/shortcut/{rhid}")
        ex = "(?<=<p>Downloads: ).*(?=</p>)"
        downloads = re.findall(ex, response.text)[0]
        name = html.unescape(get_name(rhid))
        ex = '(?<=<span class="heart-count">).*(?=</span>)'
        hearts = re.findall(ex, response.text)[0]

        ex = '(?<=<a href="\/user\/).*(?=">)'
        author = re.findall(ex, response.text)[0]

        response = requests.get(
            f"https://routinehub.co/api/v1/shortcuts/{rhid}/versions/latest"
        )
        json_data = json.loads(response.text)
        last_version = json_data["Version"]
        release_date = json_data["Release"]
        url = json_data["URL"]
        embed = discord.Embed(
            colour=discord.Colour(0x299d68))
        icon_url = url.replace("/shortcuts/", "/shortcuts/api/records/")

        try:
          icon_url = json.loads(requests.get(icon_url).text)["fields"]["icon"]["value"]["downloadURL"]
        except:
          icon_url = "https://media.discordapp.net/attachments/752322547877675058/805136237844234290/Sa6a0Ia.png"

        riri = requests.get(icon_url)
        i = Image.open(BytesIO(riri.content))
        i.save("img.png", format=None)
        file = discord.File("img.png", filename="img.png")
        embed.set_thumbnail(url="attachment://img.png")

        embed.set_footer(
            text=f"{footer(message)}",
            icon_url=
            "https://cdn.discordapp.com/avatars/792855846240518174/946eb210985c413d6b1429d49f9168fc.png?size=512"
        )

        embed.add_field(
            name=f"{name}",
            value=
            f"Author: [{author}](https://routinehub.co/user/{author})\nHearts: {hearts}\nDownloads: {downloads}\nLast version: {last_version}\nPublished on : {release_date}\n\n[Download {name}]({url})"
        )

        await message.channel.send(file=file, embed=embed)
        await loading.delete()

      else:
        await loading.delete()
        embed = discord.Embed(colour=discord.Colour(0x690a6))

        embed.set_footer(text=footer(message), icon_url="https://cdn.discordapp.com/avatars/792855846240518174/946eb210985c413d6b1429d49f9168fc.png?size=512")

        embed.add_field(name="<:error:805061336185831434> Error <:error:805061336185831434>", value="This shortcut does not exist.\n\n")

        await message.channel.send(embed=embed)

  elif message.content.startswith("!rh user"):
    user = message.content.replace("!rh user ", "")
    if user:
      user_url = f"https://routinehub.co/user/{user}"
      response = requests.get(user_url)
      if not "Error: Profile not found" in response.text:

        loading = await message.channel.send("Routinebot is loading your request")

        async with message.channel.typing():

          ex = "(?<=<p>Shortcuts: ).*(?=</p>)"
          sc = re.findall(ex, response.text)[0]

          ex = "(?<=<strong>).*(?=</strong>)"
          username = re.findall(ex, response.text)[0]

          ex = "(?<=p>Downloads: ).*(?=</p>)"
          dls = re.findall(ex, response.text)[0]

          ex = '(?<=<img class="is-rounded" src=").*(?=" alt="Profile picture for)'
          
          pp_url = re.findall(ex, response.text)
          

        #  Hearts

          ex = '(?<=<i class="fas fa-heart"></i></span>\n).*(?=\n</small>)'
          hearts_list = re.findall(ex, response.text)

          hearts = 0

          for num in hearts_list:
            num = int(num)
            hearts += num
          
          ex = '(?<=<a class="pagination-link" href="\?page=).*(?=">)'
          pages = re.findall(ex, response.text)

          for page in pages:
            response = requests.get(f"{user_url}?page={page}")
            ex = '(?<=<i class="fas fa-heart"></i></span>\n).*(?=\n</small>)'
            hearts_list = re.findall(ex, response.text)
            for num in hearts_list:
              num = int(num)
              hearts += num


          embed = discord.Embed(title=f"**{username}**", colour=discord.Colour(0x299d68), url=user_url)

          if len(pp_url) > 0:
            embed.set_thumbnail(url=pp_url[0])

          embed.set_footer(
            text=f"{footer(message)}",
            icon_url=
            "https://cdn.discordapp.com/avatars/792855846240518174/946eb210985c413d6b1429d49f9168fc.png?size=512")

          embed.add_field(name="Information", value=f"Shortcuts: {sc}\nDownloads: {dls}\nHearts: {hearts}")
        
        await loading.delete()
        await message.channel.send(embed=embed)

      else:
        embed = discord.Embed(colour=discord.Colour(0x690a6))

        embed.set_footer(text=footer(message), icon_url="https://cdn.discordapp.com/avatars/792855846240518174/946eb210985c413d6b1429d49f9168fc.png?size=512")

        embed.add_field(name="<:error:805061336185831434> Error <:error:805061336185831434>", value="User not found.\n\n")

        await message.channel.send(embed=embed)

  elif message.content.startswith("!rh"):
    embed = discord.Embed(colour=discord.Colour(0x690a6))

    embed.set_footer(
      text=footer(message), icon_url="https://cdn.discordapp.com/avatars/792855846240518174/946eb210985c413d6b1429d49f9168fc.png?size=512")

    embed.add_field(
      name="<:error:805061336185831434> Error <:error:805061336185831434>", value="Invalid command, take a look to the help page with the '!rh help' command.\n\n"
      )

    await message.channel.send(embed=embed)

keep_alive()
client.run(os.getenv("TOKEN"), bot=True)