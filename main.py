# main.py
import os
import re
from flask import Flask
from threading import Thread
import disnake
from disnake.ext import commands
from dotenv import load_dotenv
import joblib
from csv_to_dict import load_commandments

# --- Flask keep-alive ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!", 200

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
    Thread(target=run_flask, daemon=True).start()

# --- Load environment variables and ML model ---
load_dotenv()
token = os.getenv('DISCORD_TOKEN')

try:
    model = joblib.load('Testament_Classifier.pkl')
    vectorizer = joblib.load('TC_Vectorizer.pkl')
    model_loaded = True
except FileNotFoundError:
    print("Warning: Model files not found. Classification feature will be disabled.")
    model_loaded = False

# --- Bot setup ---
intents = disnake.Intents.default()
intents.message_content = True

# Use InteractionBot for slash-command only bots
bot = commands.InteractionBot(
    intents=intents,
    test_guilds=[1388620030358589563]  # Your guild ID
)

# --- Helper functions ---
def chunk_text(text: str, max_len: int = 2000):
    """Split text into Discord-friendly chunks"""
    chunks = []
    while len(text) > max_len:
        split_at = text.rfind("\n", 0, max_len)
        if split_at == -1:
            split_at = text.rfind(" ", 0, max_len)
        if split_at == -1:
            split_at = max_len
        chunks.append(text[:split_at])
        text = text[split_at:].lstrip()
    if text:
        chunks.append(text)
    return chunks

# --- Events ---
@bot.event
async def on_ready():
    print(f"✅ Bot is ready! Logged in as {bot.user}")
    print(f"✅ Serving {len(bot.guilds)} guild(s)")

@bot.event
async def on_message(msg):
    if msg.author == bot.user:
        return

    # Zeus is cool response
    if "zeus is cool" in msg.content.lower():
        await msg.reply("That's right! ⚡", mention_author=True)
        await msg.add_reaction("✅")

    # Bot mention responses
    if bot.user in msg.mentions:
        cleaned_content = re.sub(r'<@!?' + str(bot.user.id) + r'>', '', msg.content).strip().lower()
        
        responses = {
            "how are you": "I am good. How are you?",
            "bye": "Bye! 👋",
            "ayoo": "What's uppp! 🎉",
            "i am good": "Good to hear that you are doing good!",
            "i'm good": "Good to hear that you are doing good!",
            "i am not good": "Oh! Hope you feel better soon. ❤️",
            "i'm not good": "Oh! Hope you feel better soon. ❤️"
        }
        
        response_sent = False
        for phrase, reply in responses.items():
            if phrase in cleaned_content:
                await msg.reply(reply, mention_author=True)
                response_sent = True
                break
        
        if not response_sent:
            greetings = ["hello", "hi", "hey", "yo", "howdy", "greetings"]
            if any(greeting in cleaned_content.split() for greeting in greetings):
                await msg.reply("Hello! 👋", mention_author=True)
            else:
                await msg.reply("I'm not sure how to respond to that.", mention_author=True)

    # REMOVED: await bot.process_commands(msg) - InteractionBot doesn't need this

# --- Slash commands ---
@bot.slash_command(name="greet", description="Greet another user")
async def greet(inter: disnake.ApplicationCommandInteraction, user: disnake.User, message: str = ""):
    """Greet a user with an optional message"""
    if message:
        await inter.response.send_message(f"{inter.author.mention} says to {user.mention}: {message}")
    else:
        await inter.response.send_message(f"{inter.author.mention} says hello {user.mention}! 👋")

@bot.slash_command(name="classify", description="AI evaluation of OT/NT text")
async def classify(inter: disnake.ApplicationCommandInteraction, text: str):
    """Classify text as Old or New Testament"""
    if not model_loaded:
        await inter.response.send_message("❌ Classification feature is currently unavailable.")
        return
        
    try:
        prediction = model.predict(vectorizer.transform([text]))[0]
        response = "📖 New Testament" if prediction else "🕍 Old Testament"
        await inter.response.send_message(f'**Classification:** {response}')
    except Exception as e:
        await inter.response.send_message(f"❌ Error during classification: {str(e)}")

@bot.slash_command(name="commandment", description="Find commandments containing specific words")
async def commandment(inter: disnake.ApplicationCommandInteraction, search_term: str):
    """Search for Bible commandments"""
    try:
        commandments = load_commandments()
        matches = [f'**{ref}**: {verse}' for ref, verse in commandments.items() 
                  if search_term.lower() in verse.lower()]

        if not matches:
            await inter.response.send_message("❌ No matches found")
            return

        response = "\n".join(matches)
        chunks = chunk_text(response)

        if len(chunks) == 1:
            await inter.response.send_message(chunks[0])
        else:
            await inter.response.send_message(chunks[0])
            for chunk in chunks[1:]:
                await inter.followup.send(chunk)
    except Exception as e:
        await inter.response.send_message(f"❌ Error: {str(e)}")

# --- Error handling ---
@bot.event
async def on_slash_command_error(inter: disnake.ApplicationCommandInteraction, error):
    """Handle slash command errors"""
    print(f"Command error: {error}")
    
    # Check if the interaction has already been responded to
    if not inter.response.is_done():
        try:
            await inter.response.send_message("❌ An error occurred while executing this command.", ephemeral=True)
        except:
            pass  # If we can't respond, just log the error

# --- Run bot ---
if __name__ == "__main__":
    if token:
        bot.run(token)
    else:
        print("❌ Error: No token found. Please check your .env file.")
