import os
import discord
from discord.ext import commands
import random

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix=".", intents=intents)

# دیتای بازی‌ها
GAMES = {}  # channel_id -> {players: set, god_id: int, scenario: str, roles: dict, message: int}

# سناریوها
SCENARIOS = {
    "تست": {
        "3": ["دکتر", "مافیا", "شهروند ساده"]
    },
    "مذاکره": {
        "10": ["زره‌پوش","دکتر","کارآگاه","اسنایپر","شهروند ساده","شهروند ساده","دن مافیا","مذاکره‌کننده","مافیا ساده","مافیا ساده"],
        "12": ["زره‌پوش","دکتر","کارآگاه","اسنایپر","شهروند ساده","شهروند ساده","شهروند ساده","دن مافیا","مذاکره‌کننده","مافیا ساده","مافیا ساده","مافیا ساده"],
        "13": ["زره‌پوش","دکتر","کارآگاه","اسنایپر","شهروند ساده","شهروند ساده","شهروند ساده","شهروند ساده","دن مافیا","مذاکره‌کننده","مافیا ساده","مافیا ساده","مافیا ساده"]
    },
    "کاپو": {
        "10": ["عطار","وارث","زره‌ساز","کارآگاه","مظنون","شهروند ساده","شهروند ساده","دن مافیا","جادوگر","جلاد"],
        "12": ["عطار","وارث","زره‌ساز","کارآگاه","مظنون","شهروند ساده","شهروند ساده","کدخدا","دن مافیا","جادوگر","جلاد","خبرچین"],
        "13": ["عطار","وارث","زره‌ساز","کارآگاه","مظنون","شهروند ساده","شهروند ساده","کدخدا","شهروند ساده","دن مافیا","جادوگر","جلاد","خبرچین"]
    }
}





async def update_player_list(channel):
    game = GAMES.get(channel.id)
    if not game or not game.get("message"):
        return

    msg = await channel.fetch_message(game["message"])
    players_text = "\n".join(
        [f"- <@{pid}>" if pid > 0 else f"- 👻 FakePlayer{abs(pid)}" for pid in game["players"]]
    )

    embed = discord.Embed(
        title="🎮 بازی در حال آماده‌سازی",
        description=f"👑 گاد: <@{game['god_id']}>\n\nبازیکنان:\n{players_text}",
        color=discord.Color.blue()
    )
    await msg.edit(embed=embed, view=msg.components[0] if msg.components else None)







@bot.command(name="cg")
async def create_game(ctx):
    GAMES[ctx.channel.id] = {
        "players": set([ctx.author.id]),
        "god_id": ctx.author.id,
        "scenario": None,
        "roles": {},
        "message": None
    }

    class JoinAndScenarioView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=None)
            self.add_item(discord.ui.Button(label="ورود به بازی", style=discord.ButtonStyle.success, custom_id="join_game"))
            for name in SCENARIOS.keys():
                self.add_item(discord.ui.Button(label=name, style=discord.ButtonStyle.primary, custom_id=f"scenario_{name}"))

    embed = discord.Embed(
        title="🎮 بازی جدید ساخته شد",
        description=f"👑 گاد: <@{ctx.author.id}>\n\nبازیکنان:\n- <@{ctx.author.id}>",
        color=discord.Color.green()
    )
    msg = await ctx.send(embed=embed, view=JoinAndScenarioView())
    GAMES[ctx.channel.id]["message"] = msg.id







@bot.command(name="a")
async def add_player(ctx, member: discord.Member):
    game = GAMES.get(ctx.channel.id)
    if not game:
        await ctx.send("❌ بازی‌ای فعال نیست.")
        return
    if ctx.author.id != game["god_id"]:
        await ctx.send("🚫 فقط گاد می‌تونه بازیکن اضافه کنه.")
        return
    if member.id in game["players"]:
        await ctx.send(f"⚠️ {member.display_name} قبلاً وارد بازی شده.")
        return

    game["players"].add(member.id)
    await ctx.send(f"✅ {member.mention} توسط گاد به بازی اضافه شد.")
    await update_player_list(ctx.channel)

@bot.command(name="fake")
async def add_fake_players(ctx, count: int):
    game = GAMES.get(ctx.channel.id)
    if not game:
        await ctx.send("❌ بازی‌ای فعال نیست.")
        return
    if ctx.author.id != game["god_id"]:
        await ctx.send("🚫 فقط گاد می‌تونه بازیکن فیک اضافه کنه.")
        return
    if count < 1 or count > 10:
        await ctx.send("⚠️ فقط می‌تونی عددی بین 1 تا 10 وارد کنی.")
        return

    for i in range(count):
        fake_id = -(len(game["players"]) + i + 1)
        game["players"].add(fake_id)

    await ctx.send(f"👻 {count} بازیکن فیک اضافه شد.")
    await update_player_list(ctx.channel)

@bot.event
async def on_interaction(interaction: discord.Interaction):
    cid = interaction.channel.id
    game = GAMES.get(cid)
    if not game:
        return

    custom_id = interaction.data.get("custom_id", "")

    if custom_id == "join_game":
        if interaction.user.id in game["players"]:
            await interaction.response.send_message("⚠️ شما قبلاً وارد بازی شدی.", ephemeral=True)
            return
        game["players"].add(interaction.user.id)
        await interaction.response.send_message(f"✅ <@{interaction.user.id}> وارد بازی شد.")
        await update_player_list(interaction.channel)
        return

    if custom_id.startswith("scenario_"):
        scenario_name = custom_id.split("_", 1)[1]
        if scenario_name not in SCENARIOS:
            await interaction.response.send_message("❌ سناریو یافت نشد.", ephemeral=True)
            return
        game["scenario"] = scenario_name
        await interaction.response.edit_message(
            content=f"📋 سناریو **{scenario_name}** انتخاب شد. وقتی آماده بودید، گاد می‌تواند با `.sg` نقش‌ها را تقسیم کند.",
            view=None
        )











@bot.command(name="sg")
async def start_game(ctx):
    game = GAMES.get(ctx.channel.id)
    if not game or ctx.author.id != game["god_id"]:
        await ctx.send("🚫 فقط گاد می‌تونه نقش‌ها رو تقسیم کنه.")
        return
    if not game["scenario"]:
        await ctx.send("❌ هنوز سناریو انتخاب نشده.")
        return

    scenario_roles = SCENARIOS[game["scenario"]].get(str(len(game["players"])))
    if not scenario_roles:
        await ctx.send("⚠️ تعداد بازیکنان با هیچ نسخه‌ای از این سناریو نمی‌خونه.")
        return

    roles = scenario_roles.copy()
    random.shuffle(roles)
    assignments = {}
    for player_id, role in zip(game["players"], roles):
        assignments[player_id] = role
        if player_id > 0:  # بازیکن واقعی
            member = ctx.guild.get_member(player_id)
            try:
                await member.send(f"🎭 نقش شما: **{role}**")
            except:
                await ctx.send(f"⚠️ نتونستم نقش رو برای <@{player_id}> بفرستم (پی‌وی بسته است).")

    game["roles"] = assignments

    # لیست نقش‌ها برای گاد
    god_member = ctx.guild.get_member(game["god_id"])
    role_list = "\n".join(
        [f"🔹 {(ctx.guild.get_member(pid).display_name if pid > 0 else f'FakePlayer{abs(pid)}')} → {role}"
         for pid, role in assignments.items()]
    )
    try:
        await god_member.send(f"📋 لیست نقش‌ها:\n\n{role_list}")
    except:
        await ctx.send("⚠️ نتونستم لیست نقش‌ها رو برای گاد بفرستم (پی‌وی بسته است).")

    await ctx.send("✅ نقش‌ها تقسیم شدند.")










# اجرای بات
bot.run(TOKEN)


