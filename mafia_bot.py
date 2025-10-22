# mafia_bot.py
import os
import discord
from discord.ext import commands

TOKEN = os.getenv("DISCORD_TOKEN")
INTENTS = discord.Intents.default()
INTENTS.message_content = True
INTENTS.guilds = True

bot = commands.Bot(command_prefix=".", intents=INTENTS)

# لینک‌های تصویر شب و روز (جایگزین کن با لینک‌های خودت)
NIGHT_IMAGE_URL = "https://example.com/night.png"
DAY_IMAGE_URL = "https://example.com/day.png"

# دستور شب
@bot.command(name="شب")
async def send_night(ctx):
    embed = discord.Embed(
        title="🌙 شب شد...",
        description="**شب میشه و شهر خاموش**",
        color=discord.Color.dark_blue()
    )
    embed.set_image(url=NIGHT_IMAGE_URL)
    embed.set_footer(text="🕯️ آرامش شبانه در شهر مافیا")
    await ctx.send(embed=embed)

# دستور روز
@bot.command(name="روز")
async def send_day(ctx):
    embed = discord.Embed(
        title="☀️ روز شد...",
        description="**روز میشه و شهر روشن**",
        color=discord.Color.gold()
    )
    embed.set_image(url=DAY_IMAGE_URL)
    embed.set_footer(text="🌇 بیداری و هیاهوی شهر")
    await ctx.send(embed=embed)

# نمونه دستور شروع بازی با پیشوند .
@bot.command(name="ng")
async def new_game(ctx):
    await ctx.send("🎮 بازی جدید ساخته شد. با دستور `.j` وارد شوید.")

# دستور ورود به بازی
@bot.command(name="j")
async def join_game(ctx):
    await ctx.send(f"✅ <@{ctx.author.id}> وارد بازی شد.")

# دستور وضعیت
@bot.command(name="st")
async def status(ctx):
    await ctx.send("📊 وضعیت فعلی بازی: در حال آماده‌سازی...")

# راه‌اندازی بات
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user.name}")
    print("📌 دستورات فعال: .شب .روز .ng .j .st")

bot.run(TOKEN)
