# main.py
import os
from flask import Flask
from threading import Thread
from discord.ext import commands
import discord
from dotenv import load_dotenv
import joblib

# --- Flask keep-alive ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!", 200

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

Thread(target=run_flask).start()

# --- Load environment variables and ML model ---
load_dotenv()
token = os.getenv('token')

model = joblib.load('Testament_Classifier.pkl')
vectorizer = joblib.load('TC_Vectorizer.pkl')

# --- Bot setup ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="#", intents=intents)

@bot.event
async def on_ready():
    print("Bot is working :)))")

@bot.event
async def on_message(msg):
    if msg.author == bot.user:
        return
    if "zeus is cool" in msg.content.lower():
        await msg.reply("That's right", mention_author=True)
        await msg.add_reaction("✅")
    await bot.process_commands(msg)

@bot.slash_command(name="greet", description='Greet the user', guild_ids=[1388620030358589563])
async def greet(ctx, user: discord.User, msg: str = None):
    if msg:
        await ctx.respond(f"{ctx.author.mention} says to {user.mention}: {msg}")
    else:
        await ctx.respond(f"{ctx.author.mention} says hello {user.mention}! 👋")

@bot.slash_command(name="classify", description="AI evaluation of OT/NT text", guild_ids=[1388620030358589563])
async def classify(ctx, msg: str):
    response = "New Testament" if model.predict(vectorizer.transform([msg]))[0] else "Old Testament"
    await ctx.respond(f'Classification : {response}')

# --- Run bot ---
bot.run(token)
