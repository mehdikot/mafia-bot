import os
import discord
from discord.ext import commands
import asyncio

import os
TOKEN = os.getenv("DISCORD_TOKEN")


intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix=".", intents=intents)

NIGHT_IMAGE_URL = "https://s6.uupload.ir/files/night_25.jpg"
DAY_IMAGE_URL = "https://s6.uupload.ir/files/day_ho71.jpg"

GAMES = {}  # channel_id -> {players: set, god_id: int, votes: dict}

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
    GAMES[ctx.channel.id] = {"players": set(), "god_id": ctx.author.id, "votes": {}}
    await ctx.send(f"🎮 بازی جدید ساخته شد.\n👑 گاد: <@{ctx.author.id}>\nبرای ورود از دستور `.اد` استفاده کنید.")

@bot.command(name="اد")
async def join_game(ctx):
    game = GAMES.get(ctx.channel.id)
    if not game:
        await ctx.send("❌ هنوز بازی‌ای ساخته نشده. از `.بازی` استفاده کن.")
        return
    game["players"].add(ctx.author.id)
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
    if not game:
        await ctx.send("❌ بازی‌ای فعال نیست.")
        return
    if ctx.author.id != game["god_id"]:
        await ctx.send("🚫 فقط گاد فعلی می‌تونه گاد جدید تعیین کنه.")
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

        @discord.ui.button(label="لغو", style=discord.ButtonStyle.danger, custom_id="cancel")
        async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.edit_message(content="❌ انتخاب سناریو لغو شد.", view=None)

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

        roles_text = "\n".join([f"• {r}" for r in scenario["roles"]])
        embed = discord.Embed(
            title=f"✅ سناریو انتخاب شد: {scenario_name}",
            description=f"👥 تعداد بازیکنان: {scenario['players']}\n🎭 نقش‌ها:\n{roles_text}",
            color=discord.Color.blue()
        )
        await interaction.response.edit_message(embed=embed, view=None)









@bot.command(name="v")
async def vote_sequence(ctx, mode: str, start: int, direction: str, count: int):
    game = GAMES.get(ctx.channel.id)
    if not game or ctx.author.id != game["god_id"]:
        await ctx.send("🚫 فقط گاد می‌تونه رأی‌گیری نوبتی انجام بده.")
        return

    players = list(game["players"])
    if len(players) == 0:
        await ctx.send("❌ هیچ بازیکنی وارد بازی نشده.")
        return

    if start < 1 or start > len(players):
        await ctx.send(f"⚠️ شماره شروع باید بین 1 تا {len(players)} باشه.")
        return

    if direction not in ["u", "d"]:
        await ctx.send("⚠️ جهت باید `u` (بالا) یا `d` (پایین) باشه.")
        return

    sequence = []
    idx = start - 1
    for _ in range(count):
        if direction == "u":
            idx = (idx + 1) % len(players)
        else:
            idx = (idx - 1 + len(players)) % len(players)
        sequence.append(players[idx])

    votes = {uid: [] for uid in sequence}
    await ctx.send(f"🗳️ رأی‌گیری نوع **{mode}** آغاز شد.\n⏳ هر بازیکن ۵ ثانیه فرصت داره رأی بده.")

    for i, target_id in enumerate(sequence, start=1):
        vote_msg = await ctx.send(f"🔢 شماره {i} → <@{target_id}> | رأی‌ها: 0")

        def check(m):
            return (
                m.channel == ctx.channel and
                m.author.id in game["players"] and
                m.author.id != target_id and
                m.content.strip() != ""
            )

        end_time = asyncio.get_event_loop().time() + 5
        while True:
            timeout = end_time - asyncio.get_event_loop().time()
            if timeout <= 0:
                break
            try:
                msg = await bot.wait_for("message", timeout=timeout, check=check)
                if msg.author.id not in votes[target_id]:
                    votes[target_id].append(msg.author.id)
                    await vote_msg.edit(content=f"🔢 شماره {i} → <@{target_id}> | رأی‌ها: {len(votes[target_id])}")
            except asyncio.TimeoutError:
                break

    game["votes"] = votes
    await ctx.send("✅ رأی‌گیری نوبتی به پایان رسید. برای اعدام از دستور `.اعدام` استفاده کن.")







@bot.command(name="اعدام")
async def execute_vote(ctx):
    game = GAMES.get(ctx.channel.id)
    if not game or ctx.author.id != game["god_id"]:
        await ctx.send("🚫 فقط گاد می‌تونه اعدام رو انجام بده.")
        return

    votes = game.get("votes", {})
    if not votes:
        await ctx.send("❌ هیچ رأیی ثبت نشده.")
        return

    tally = {}
    for target_id, voter_ids in votes.items():
        tally[target_id] = len(voter_ids)

    if not tally:
        await ctx.send("⚠️ هیچ رأی معتبری وجود ندارد.")
        return

    max_votes = max(tally.values())
    candidates = [uid for uid, count in tally.items() if count == max_votes]

    if len(candidates) > 1:
        await ctx.send("⚖️ رأی مساوی شد. کسی اعدام نشد.")
        return

    executed = candidates[0]
    role = "نامشخص"
    if "roles" in game:
        role = game["roles"].get(executed, "نامشخص")

    game["players"].discard(executed)
    await ctx.send(f"☠️ <@{executed}> با نقش **{role}** اعدام شد.")

    # بررسی برد
    mafia_alive = [uid for uid in game["players"] if "مافیا" in game.get("roles", {}).get(uid, "")]
    others_alive = [uid for uid in game["players"] if uid not in mafia_alive]

    if not mafia_alive:
        await ctx.send("🎉 شهروندها برنده شدند!")
    elif len(mafia_alive) >= len(others_alive):
        await ctx.send("😈 مافیاها کنترل شهر رو به دست گرفتن. مافیا برنده شد!")

    # پاک‌سازی رأی‌ها
    game["votes"] = {}














@bot.event
async def on_ready():
    print(f"✅ بات فعال شد: {bot.user.name}")
    print("📌 دستورات فارسی آماده استفاده هستن.")

bot.run(TOKEN)












