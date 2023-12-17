import nextcord as discord
from nextcord.ext import commands
import requests
import json

import os
BOT_TOKEN = ""
with open('botsettings.json','r') as file:
    data=json.load(file)
    BOT_TOKEN=data['BOT_TOKEN']

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True

url = "https://api.orhanaydogdu.com.tr/deprem/kandilli/live"

def fetch_earthquake_data():
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        return None

def format_earthquake_message(data, start_index, end_index):
    if data and "result" in data and data["result"]:
        earthquakes = data["result"][start_index:end_index]
        message = "```css\n"  # Başlık için renklendirme için CSS syntax
        for earthquake in earthquakes:
            earthquake_id = earthquake.get("earthquake_id", "Bilgi Yok")
            provider = earthquake.get("provider", "Bilgi Yok")
            title = earthquake.get("title", "Bilgi Yok")
            date = earthquake.get("date", "Bilgi Yok")
            magnitude = earthquake.get("mag", "Bilgi Yok")
            depth = earthquake.get("depth", "Bilgi Yok")
            coordinates = earthquake.get("geojson", {}).get("coordinates", "Bilgi Yok")

            message += f"""
Deprem ID: {earthquake_id}
Sağlayıcı: {provider}
Başlık: {title}
Tarih: {date}
Büyüklük: {magnitude}
Derinlik: {depth}
Koordinatlar: {coordinates}
-------------------------------------------
"""
        message += "```"
        return message
    else:
        return "Deprem bilgileri alınamadı."

client = commands.Bot(command_prefix='!', intents=intents)
current_index = 0

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.command(name='deprem')
async def deprem(ctx):
    global current_index
    user = ctx.author

    earthquake_data = fetch_earthquake_data()

    if earthquake_data and "result" in earthquake_data:
        max_index = len(earthquake_data["result"])

        # 5 Tane deprem göster ve devam etmek istiyor mu sor
        while current_index < max_index:
            end_index = min(current_index + 5, max_index)
            earthquake_message = format_earthquake_message(earthquake_data, current_index, end_index)
    
            embed = discord.Embed(title="Canlı Deprem Bilgisi", color=discord.Color.red(), description=earthquake_message)
            message = await ctx.send(embed=embed)

            # Emojileri ekleyerek tepki al
            await message.add_reaction('✅')  # Devam et
            await message.add_reaction('❌')  # İstemiyorum
            await message.channel.send("Devam etmek istiyor musunuz?\nEğer istiyorsanız :white_check_mark:  Eğer İstemiyorsanız :x: e Basınız.")
            def check(reaction, user):
                return user == ctx.author and str(reaction.emoji) in ["✅", "❌"]

            try:
                reaction, _ = await client.wait_for("reaction_add", timeout=30.0, check=check)
                
                await message.clear_reactions()
                if str(reaction.emoji) == "❌":
                    await message.channel.send("İsteğiniz Üzerine !deprem komutunu Kullanmadığınız Sürece Deprem ile alakalı bir şey gösterilmeyecek.")
                    current_index = max_index  # Döngüyü bitir
                else:
                    await message.channel.send("Devam Ediliyor...")
                    current_index = end_index
            except discord.errors.TimeoutError:
                current_index = max_index  # eğer timeouterror durumundaysa döngüyü bitir
            else:
                await message.clear_reactions()

@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Geçersiz komut. Lütfen `!deprem` komutunu kullanın.")

client.run(BOT_TOKEN)
