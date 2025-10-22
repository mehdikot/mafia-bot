import discord
from discord.ext import commands
import random

TOKEN = "توکن_بات_شخصی_شما"

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix=".", intents=intents)

NIGHT_IMAGE_URL = "https://s6.uupload.ir/files/night_25.jpg"
DAY_IMAGE_URL = "https://s6.uupload.ir/files/day_ho71.jpg"

GAMES = {}  # channel_id -> {players: set, god_id: int, roles: dict, votes: dict, alive: set}

SCENARIOS = {
    "بازپرس": {
        "players": 10,
        "roles": [
            "مافیا", "گادفادر", "دکتر", "کارآگاه", "شهروند",
            "شهروند", "روان‌پزشک", "ساپورتر", "نماینده", "شهروند"
        ]
    },
    "کاپو": {
        "players": 12,
        "roles": [
            "کاپو", "مافیا", "مافیا", "دکتر", "کارآگاه",
            "شهروند", "شهروند", "روان‌پزشک", "قمارباز", "نماینده", "شهروند", "شهروند"
        ]
    },
    "مذاکره": {
        "players": 13,
        "roles": [
            "مافیا", "مافیا", "گادفادر", "دکتر", "کارآگاه",
            "نماینده", "شهروند", "شهروند", "روان‌پزشک", "ساپورتر", "قمارباز", "دهکده‌دار", "شهروند"
        ]
    },
    "نماینده": {
        "players": 10,
        "roles": [
            "نماینده", "مافیا", "گادفادر", "دکتر", "کارآگاه",
            "شهروند", "شهروند", "روان‌پزشک", "ساپورتر", "شهروند"
        ]
    }
}




@bot.command(name="بازی")
async def create_game(ctx):
    GAMES[ctx.channel.id] = {
        "players": set(),
        "god_id": ctx.author.id,
        "roles": {},
        "votes": {},
        "alive": set()
    }
    await ctx.send(f"🎮 بازی جدید ساخته شد.\n👑 گاد: <@{ctx.author.id}>\nبرای ورود از دستور `.اد` استفاده کنید.")

@bot.command(name="اد")
async def join_game(ctx):
    game = GAMES.get(ctx.channel.id)
    if not game:
        await ctx.send("❌ هنوز بازی‌ای ساخته نشده.")
        return
    game["players"].add(ctx.author.id)
    game["alive"].add(ctx.author.id)
    await ctx.send(f"✅ <@{ctx.author.id}> وارد بازی شد. تعداد بازیکنان: {len(game['players'])}")

@bot.command(name="گاد")
async def set_god(ctx):
    game = GAMES.get(ctx.channel.id)
    if not game:
        await ctx.send("❌ بازی‌ای فعال نیست.")
        return
    game["god_id"] = ctx.author.id
    await ctx.send(f"👑 <@{ctx.author.id}> حالا گاد بازیه.")

@bot.command(name="گاد_تعیین")
async def assign_god(ctx, member: discord.Member):
    game = GAMES.get(ctx.channel.id)
    if not game or ctx.author.id != game["god_id"]:
        await ctx.send("🚫 فقط گاد می‌تونه گاد جدید تعیین کنه.")
        return
    game["god_id"] = member.id
    await ctx.send(f"👑 <@{member.id}> حالا گاد بازیه.")

@bot.command(name="وضعیت")
async def game_status(ctx):
    game = GAMES.get(ctx.channel.id)
    if not game:
        await ctx.send("❌ بازی‌ای فعال نیست.")
        return
    players = ", ".join([f"<@{uid}>" for uid in game["players"]]) or "—"
    await ctx.send(f"📊 وضعیت بازی:\n👑 گاد: <@{game['god_id']}>\n🧑‍🤝‍🧑 بازیکنان: {players}")

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

@bot.command(name="sg")
async def start_game(ctx):
    game = GAMES.get(ctx.channel.id)
    if not game or ctx.author.id != game["god_id"]:
        await ctx.send("🚫 فقط گاد می‌تونه بازی رو ران کنه.")
        return

    class ScenarioView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=None)
            for name in SCENARIOS.keys():
                self.add_item(discord.ui.Button(label=name, style=discord.ButtonStyle.primary, custom_id=f"scenario_{name}"))

    embed = discord.Embed(
        title="📢 شروع رسمی بازی",
        description=f"🎮 بازی قراره ران بشه!\n👑 گاد: <@{ctx.author.id}>\n\nلطفاً یکی از سناریوهای زیر رو انتخاب کن:",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed, view=ScenarioView())

@bot.event
async def on_interaction(interaction: discord.Interaction):
    cid = interaction.channel.id
    game = GAMES.get(cid)
    if not game or interaction.user.id != game["god_id"]:
        await interaction.response.send_message("🚫 فقط گاد می‌تونه سناریو انتخاب کنه.", ephemeral=True)
        return

    if interaction.data["custom_id"].startswith("scenario_"):
        scenario_name = interaction.data["custom_id"].split("_")[1]
        scenario = SCENARIOS.get(scenario_name)
        if not scenario:
            await interaction.response.send_message("❌ سناریو یافت نشد.", ephemeral=True)
            return

        players = list(game["players"])
        if len(players) != scenario["players"]:
            await interaction.response.send_message(f"⚠️ این سناریو نیاز به {scenario['players']} بازیکن داره.", ephemeral=True)
            return

        random.shuffle(players)
        roles = scenario["roles"]
        game["roles"] = dict(zip(players, roles))

        for uid, role in game["roles"].items():
            member = interaction.guild.get_member(uid)
            try:
                await member.send(f"🎭 نقش شما در بازی: **{role}**")
            except:
                pass

        roles_text = "\n".join([f"• {r}" for r in roles])
        embed = discord.Embed(
            title=f"✅ سناریو انتخاب شد: {scenario_name}",
            description=f"👥 تعداد بازیکنان: {scenario['players']}\n🎭 نقش‌ها:\n{roles_text}",
            color=discord.Color.blue()
        )
        await interaction.response.edit_message(embed=embed, view=None)






@bot.command(name="رای")
async def vote(ctx, member: discord.Member):
    game = GAMES.get(ctx.channel.id)
    if not game or ctx.author.id not in game["alive"] or member.id not in game["alive"]:
        await ctx.send("❌ رأی‌گیری معتبر نیست.")
        return
    game["votes"][ctx.author.id] = member.id
    await ctx.send(f"🗳️ <@{ctx.author.id}> به <@{member.id}> رأی داد.")

@bot.command(name="حذف_رای")
async def remove_vote(ctx):
    game = GAMES.get(ctx.channel.id)
    if not game or ctx.author.id not in game["votes"]:
        await ctx.send("❌ رأی‌ای برای حذف وجود ندارد.")
        return
    del game["votes"][ctx.author.id]
    await ctx.send(f"❌ رأی <@{ctx.author.id}> حذف شد.")

@bot.command(name="اعدام")
async def execute(ctx):
    game = GAMES.get(ctx.channel.id)
    if not game:
        await ctx.send("❌ بازی‌ای فعال نیست.")
        return

    tally = {}
    for voter, target in game["votes"].items():
        if target in game["alive"]:
            tally[target] = tally.get(target, 0) + 1

    if not tally:
        await ctx.send("⚠️ هیچ رأی معتبری ثبت نشده.")
        return

    max_votes = max(tally.values())
    candidates = [uid for uid, count in tally.items() if count == max_votes]

    if len(candidates) > 1:
        await ctx.send("⚖️ رأی مساوی شد. کسی اعدام نشد.")
        return

    executed = candidates[0]
    game["alive"].remove(executed)
    role = game["roles"].get(executed, "نامشخص")
    await ctx.send(f"☠️ <@{executed}> با نقش **{role}** اعدام شد.")

    # بررسی برد
    mafia_alive = [uid for uid in game["alive"] if "مافیا" in game["roles"].get(uid, "")]
    others_alive = [uid for uid in game["alive"] if uid not in mafia_alive]

    if not mafia_alive:
        await ctx.send("🎉 شهروندها برنده شدند!")
    elif len(mafia_alive) >= len(others_alive):
        await ctx.send("😈 مافیاها کنترل شهر رو به دست گرفتن. مافیا برنده شد!")

@bot.command(name="پایان")
async def end_game(ctx):
    game = GAMES.pop(ctx.channel.id, None)
    if not game:
        await ctx.send("❌ بازی‌ای فعال نیست.")
        return

    report = []
    for uid, role in game["roles"].items():
        status = "زنده ✅" if uid in game["alive"] else "مرده ☠️"
        report.append(f"<@{uid}> → {role} ({status})")

    embed = discord.Embed(
        title="📜 گزارش نهایی بازی",
        description="\n".join(report),
        color=discord.Color.purple()
    )
    await ctx.send(embed=embed)

@bot.event
async def on_ready():
    print(f"✅ بات فعال شد: {bot.user.name}")
    print("📌 دستورات فارسی آماده استفاده هستن.")

bot.run(TOKEN)
