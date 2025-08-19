# main.py
import os
from flask import Flask
from threading import Thread
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
bot = discord.Bot(intents=intents)  # Pycord Bot

# --- Events ---
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

    if bot.user in msg.mentions:
        import re
        text = re.sub(r'^\w\s', '', msg.content.lower())
        if "how are you" in text:
            await msg.reply("I am good. How are you?", mention_author=True)
        elif "bye" in text:
            await msg.reply("Bye!", mention_author=True)
        elif "ayoo" in text:
            await msg.reply("What's uppp!", mention_author=True)
        elif "i am good" in text or "i'm good" in text:
            await msg.reply("Good to hear that you are doing good!", mention_author=True)
        elif "i am not good" in text or "i'm not good" in text:
            await msg.reply("Oh! Hope you do good", mention_author=True)
        else:
            greetings = ["hello", "hi", "hey", "yo", "howdy", "greetings"]
            if any(greeting in text.split() for greeting in greetings):
                await msg.reply("Hello!", mention_author=True)
            else:
                await msg.reply("I'm not sure how to respond to that.", mention_author=True)

    await bot.process_commands(msg)

# --- Slash commands ---
@bot.slash_command(name="greet", description='Greet the user', guild_ids=[1388620030358589563])
async def greet(ctx, user: discord.User, msg: str = ""):
    if msg:
        await ctx.respond(f"{ctx.author.mention} says to {user.mention}: {msg}")
    else:
        await ctx.respond(f"{ctx.author.mention} says hello {user.mention}! 👋")

@bot.slash_command(name="classify", description="AI evaluation of OT/NT text", guild_ids=[1388620030358589563])
async def classify(ctx, msg: str):
    response = "New Testament" if model.predict(vectorizer.transform([msg]))[0] else "Old Testament"
    await ctx.respond(f'Classification : {response}')

# --- Helper ---
def chunk_text(text: str, max_len: int = 2000):
    chunks = []
    while len(text) > max_len:
        split_at = text.rfind("\n", 0, max_len)
        if split_at == -1:
            split_at = max_len
        chunks.append(text[:split_at])
        text = text[split_at:]
    if text:
        chunks.append(text)
    return chunks

@bot.slash_command(name="commandment", description="Get a commandment from the Bible based on words", guild_ids=[1388620030358589563])
async def commandment(ctx, msg: str):
    from csv_to_dict import load_commandments
    commandments = load_commandments()
    matches = [f'{ref} : {verse}' for ref, verse in commandments.items() if msg.lower() in verse.lower()]

    if not matches:
        await ctx.respond("No matches found")
        return

    response = "\n".join(matches)
    chunks = chunk_text(response)

    await ctx.respond(chunks[0])
    for chunk in chunks[1:]:
        await ctx.followup.send(chunk)

# --- Run bot ---
bot.run(token)
