import discord
from discord.ext import commands
import os

# بررسی وجود توکن
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise RuntimeError("❌ متغیر DISCORD_TOKEN پیدا نشد!")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ ربات {bot.user} آنلاین شد!")
    await bot.change_presence(activity=discord.Game(name="!test"))

@bot.command()
async def test(ctx):
    await ctx.send("🎉 ربات کار می‌کنه! دستورات رو می‌بینه.")

@bot.command()
async def help(ctx):
    await ctx.send("""
**دستورات تستی:**
- `!test` — تست کارکرد
- `!help` — راهنمایی
""")

bot.run(TOKEN)
