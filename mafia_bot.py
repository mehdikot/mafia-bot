import discord
from discord.ext import commands
import random
import os

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

games = {}

SCENARIOS = {
    "classic": ["Mafia", "Mafia", "Villager", "Villager", "Villager", "Doctor", "Detective"],
    "small": ["Mafia", "Villager", "Villager", "Detective"],
    "big": ["Mafia", "Mafia", "Mafia", "Villager", "Villager", "Villager", "Villager", "Doctor", "Detective", "Serial Killer"]
}

@bot.event
async def on_ready():
    print(f"ربات {bot.user} آنلاین شد!")
    await bot.change_presence(activity=discord.Game(name="!mafia help"))

@bot.group(invoke_without_command=True)
async def mafia(ctx):
    await ctx.send("برای راهنمایی: `!mafia help`")

@mafia.command()
async def help(ctx):
    await ctx.send("""
**دستورات:**
- `!mafia create <scenario>` — شروع بازی
- `!mafia join` — پیوستن
- `!mafia start` — گاد شروع کنه
- `!mafia vote @user` — رأی دادن
- `!mafia next` — عوض کردن فاز (فقط گاد)
""")

@mafia.command()
async def create(ctx, scenario: str = "classic"):
    if ctx.guild.id in games:
        await ctx.send("بازی دیگه‌ای در حال اجراست!")
        return
    if scenario not in SCENARIOS:
        await ctx.send(f"سناریوی نامعتبر! گزینه‌ها: {', '.join(SCENARIOS.keys())}")
        return

    games[ctx.guild.id] = {
        "god": ctx.author,
        "players": [],
        "roles": SCENARIOS[scenario].copy(),
        "alive": {},
        "status": "waiting",
        "votes": {}
    }
    await ctx.send(f"بازی با سناریوی **{scenario}** ساخته شد!\nگاد: {ctx.author.mention}\nبرای پیوستن: `!mafia join`")

@mafia.command()
async def join(ctx):
    game = games.get(ctx.guild.id)
    if not game:
        await ctx.send("بازی فعالی وجود ندارد!")
        return
    if game["status"] != "waiting":
        await ctx.send("بازی در حال اجراست!")
        return
    if ctx.author in game["players"]:
        await ctx.send("قبلاً پیوستی!")
        return
    if len(game["players"]) >= len(game["roles"]):
        await ctx.send("ظرفیت پر شده!")
        return

    game["players"].append(ctx.author)
    await ctx.send(f"{ctx.author.mention} به بازی پیوست!")

@mafia.command()
async def start(ctx):
    game = games.get(ctx.guild.id)
    if not game or ctx.author != game["god"]:
        await ctx.send("فقط گاد می‌تونه بازی رو شروع کنه!")
        return
    if len(game["players"]) < 3:
        await ctx.send("حداقل نیاز به ۳ نفر هست!")
        return

    roles = game["roles"][:len(game["players"])]
    random.shuffle(roles)
    game["alive"] = {p: r for p, r in zip(game["players"], roles)}
    game["status"] = "night"

    for player, role in game["alive"].items():
        try:
            await player.send(f"🎭 نقش تو: **{role}**")
        except:
            await ctx.send(f"⚠️ نتونستم نقش رو به {player.mention} بفرستم.")

    await ctx.send("بازی شروع شد! 🌙 شب آغاز شد...\nگاد با `!mafia next` فاز بعدی رو شروع کنه.")

@mafia.command()
async def next(ctx):
    game = games.get(ctx.guild.id)
    if not game or ctx.author != game["god"]:
        await ctx.send("فقط گاد می‌تونه فاز رو عوض کنه!")
        return

    if game["status"] == "night":
        game["status"] = "day"
        await ctx.send("☀️ روز شد!")
    elif game["status"] == "day":
        game["status"] = "voting"
        game["votes"] = {}
        await ctx.send("زمان رأی‌گیری! `!mafia vote @user`")
    elif game["status"] == "voting":
        votes = game["votes"]
        if not votes:
            await ctx.send("هیچ‌کس رأی نداد!")
        else:
            target = max(votes, key=lambda x: (votes[x], -game["players"].index(x)))
            game["alive"].pop(target, None)
            await ctx.send(f"💀 {target.mention} اعدام شد!")

        mafia_count = sum(1 for r in game["alive"].values() if r in ["Mafia", "Serial Killer"])
        villager_count = len(game["alive"]) - mafia_count

        if mafia_count >= villager_count:
            await ctx.send("🔴 **مافیاها بردند!**")
            del games[ctx.guild.id]
        elif mafia_count == 0:
            await ctx.send("🟢 **شهروندان بردند!**")
            del games[ctx.guild.id]
        else:
            game["status"] = "night"
            await ctx.send("🌙 شب بعدی...")

@mafia.command()
async def vote(ctx, user: discord.Member):
    game = games.get(ctx.guild.id)
    if not game or game["status"] != "voting":
        await ctx.send("الان زمان رأی‌گیری نیست!")
        return
    if ctx.author not in game["alive"]:
        await ctx.send("تو مرده‌ای!")
        return
    if user not in game["alive"]:
        await ctx.send("این نفر زنده نیست!")
        return

    game["votes"][ctx.author] = user
    await ctx.send(f"✅ {ctx.author.display_name} به {user.display_name} رأی داد.")

@mafia.command()
async def end(ctx):
    game = games.get(ctx.guild.id)
    if not game or ctx.author != game["god"]:
        await ctx.send("فقط گاد می‌تونه بازی رو تموم کنه!")
        return
    del games[ctx.guild.id]
    await ctx.send("بازی متوقف شد. 🕊️")

# ⚠️ توکن از طریق Render وارد می‌شه — نه داخل کد!
bot.run(os.getenv("DISCORD_TOKEN"))