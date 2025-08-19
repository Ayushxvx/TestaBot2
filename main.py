# main.py
import os
import re
from flask import Flask
from threading import Thread
import discord
from dotenv import load_dotenv
import joblib
from csv_to_dict import load_commandments  # Import at top level

# --- Flask keep-alive ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!", 200

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# Only start Flask thread if we're not in a subprocess (like when running on a WSGI server)
if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
    Thread(target=run_flask, daemon=True).start()

# --- Load environment variables and ML model ---
load_dotenv()
token = os.getenv('token')

# Add error handling for model loading
try:
    model = joblib.load('Testament_Classifier.pkl')
    vectorizer = joblib.load('TC_Vectorizer.pkl')
    model_loaded = True
except FileNotFoundError:
    print("Warning: Model files not found. Classification feature will be disabled.")
    model_loaded = False

# --- Bot setup ---
intents = discord.Intents.default()
intents.message_content = True
bot = discord.Bot(intents=intents)  # Pycord Bot

# Guild IDs (preserved from original code)
GUILD_IDS = [1388620030358589563]

# --- Helper functions ---
def chunk_text(text: str, max_len: int = 2000):
    """Split text into chunks that don't exceed Discord's message limit"""
    chunks = []
    while len(text) > max_len:
        # Try to split at a newline first, otherwise split at space
        split_at = text.rfind("\n", 0, max_len)
        if split_at == -1:
            split_at = text.rfind(" ", 0, max_len)
        if split_at == -1:  # No spaces or newlines found, force split
            split_at = max_len
        chunks.append(text[:split_at])
        text = text[split_at:].lstrip()  # Remove leading whitespace from next chunk
    if text:
        chunks.append(text)
    return chunks

# --- Events ---
@bot.event
async def on_ready():
    print(f"Bot is ready! Logged in as {bot.user}")

@bot.event
async def on_message(msg):
    if msg.author == bot.user:
        return

    # Case-insensitive check for "zeus is cool"
    if "zeus is cool" in msg.content.lower():
        await msg.reply("That's right", mention_author=True)
        await msg.add_reaction("✅")

    # Check if bot was mentioned
    if bot.user in msg.mentions:
        # Remove the mention from the message content
        cleaned_content = re.sub(r'<@!?' + str(bot.user.id) + r'>', '', msg.content).strip().lower()
        
        if "how are you" in cleaned_content:
            await msg.reply("I am good. How are you?", mention_author=True)
        elif "bye" in cleaned_content:
            await msg.reply("Bye!", mention_author=True)
        elif "ayoo" in cleaned_content:
            await msg.reply("What's uppp!", mention_author=True)
        elif "i am good" in cleaned_content or "i'm good" in cleaned_content:
            await msg.reply("Good to hear that you are doing good!", mention_author=True)
        elif "i am not good" in cleaned_content or "i'm not good" in cleaned_content:
            await msg.reply("Oh! Hope you feel better soon.", mention_author=True)
        else:
            greetings = ["hello", "hi", "hey", "yo", "howdy", "greetings"]
            if any(greeting in cleaned_content.split() for greeting in greetings):
                await msg.reply("Hello!", mention_author=True)
            else:
                await msg.reply("I'm not sure how to respond to that.", mention_author=True)

    # Process commands (important for slash commands to work alongside on_message)
    await bot.process_commands(msg)

# --- Slash commands ---
@bot.slash_command(name="greet", description='Greet another user', guild_ids=GUILD_IDS)
async def greet(ctx, user: discord.User, message: str = ""):
    """Greet another user with an optional message"""
    if message:
        await ctx.respond(f"{ctx.author.mention} says to {user.mention}: {message}")
    else:
        await ctx.respond(f"{ctx.author.mention} says hello {user.mention}! 👋")

@bot.slash_command(name="classify", description="AI evaluation of OT/NT text", guild_ids=GUILD_IDS)
async def classify(ctx, text: str):
    """Classify text as Old or New Testament"""
    if not model_loaded:
        await ctx.respond("Classification feature is currently unavailable.")
        return
        
    prediction = model.predict(vectorizer.transform([text]))[0]
    response = "New Testament" if prediction else "Old Testament"
    await ctx.respond(f'Classification: {response}')

@bot.slash_command(name="commandment", description="Get a commandment from the Bible based on words", guild_ids=GUILD_IDS)
async def commandment(ctx, search_term: str):
    """Search for commandments containing specific words"""
    try:
        commandments = load_commandments()
        matches = [f'{ref} : {verse}' for ref, verse in commandments.items() 
                  if search_term.lower() in verse.lower()]

        if not matches:
            await ctx.respond("No matches found")
            return

        response = "\n".join(matches)
        chunks = chunk_text(response)

        await ctx.respond(chunks[0])
        for chunk in chunks[1:]:
            await ctx.followup.send(chunk)
    except Exception as e:
        await ctx.respond(f"An error occurred: {str(e)}")

# --- Error handling ---
@bot.event
async def on_application_command_error(ctx, error):
    if isinstance(error, discord.ApplicationCommandInvokeError):
        await ctx.respond("An error occurred while executing this command.")
        print(f"Command error: {error.original}")
    else:
        print(f"Other error: {error}")

# --- Run bot ---
if __name__ == "__main__":
    if token:
        bot.run(token)
    else:
        print("Error: No token found. Please check your .env file.")
