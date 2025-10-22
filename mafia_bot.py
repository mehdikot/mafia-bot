// src/index.js
import { Client, GatewayIntentBits, Partials, Collection, REST, Routes } from 'discord.js';
import { v4 as uuidv4 } from 'uuid';

const TOKEN = process.env.DISCORD_TOKEN;

const client = new Client({
  intents: [
    GatewayIntentBits.Guilds,
    GatewayIntentBits.GuildMessages,
    GatewayIntentBits.DirectMessages,
    GatewayIntentBits.MessageContent,
    GatewayIntentBits.GuildMembers
  ],
  partials: [Partials.Channel]
});

// In-memory store (برای تولید، دیتابیس بگذارید)
const games = new Map(); // channelId -> game

// Register slash commands
const commands = [
  { name: 'newgame', description: 'ایجاد بازی جدید' },
  { name: 'join', description: 'پیوستن به لابی' },
  { name: 'lock', description: 'قفل‌کردن لابی' },
  { name: 'roles', description: 'مشاهده نقش‌ها' },
  { name: 'start', description: 'شروع بازی' },
  { name: 'vote', description: 'رأی به حذف', options: [{ name: 'user', type: 6, description: 'هدف', required: true }] },
  { name: 'unvote', description: 'حذف رأی' },
  { name: 'shoot', description: 'شلیک اسنایپر', options: [{ name: 'user', type: 6, description: 'هدف', required: true }] },
  { name: 'extend', description: 'تمدید بحث (ثانیه)', options: [{ name: 'seconds', type: 4, description: 'زمان', required: true }] },
  { name: 'status', description: 'وضعیت بازی' },
  { name: 'end', description: 'پایان اضطراری' },
];

async function registerCommands(guildId) {
  const rest = new REST({ version: '10' }).setToken(TOKEN);
  await rest.put(Routes.applicationGuildCommands(client.user.id, guildId), { body: commands });
}

client.once('ready', async () => {
  console.log(`Logged in as ${client.user.tag}`);
  // ثبت دستورات برای همه گیلدها
  client.guilds.cache.forEach(g => registerCommands(g.id));
});

// Helpers
function initGame(channelId, hostId) {
  games.set(channelId, {
    id: uuidv4(),
    channelId,
    hostId,
    state: 'Lobby',
    players: new Map(), // userId -> { userId, displayName, role: null, alive: true }
    votes: new Map(),   // voterId -> targetId
    timers: { night: 90, day: 180, vote: 60 },
    settings: { revealOnLynch: false },
    log: []
  });
}

function getGame(channelId) {
  return games.get(channelId);
}

function endGame(channelId, reason = 'پایان بازی') {
  const game = games.get(channelId);
  if (!game) return;
  game.state = 'EndGame';
  const report = generateReport(game);
  games.delete(channelId);
  return report;
}

function generateReport(game) {
  const roles = [...game.players.values()].map(p => `• ${p.displayName}: ${p.role} (${p.alive ? 'زنده' : 'حذف'})`).join('\n');
  const lines = [
    `گزارش نهایی بازی #${game.id}`,
    `نقش‌ها و وضعیت:`,
    roles,
    `رخدادها:`,
    game.log.map(l => `• ${l}`).join('\n') || '—'
  ];
  return lines.join('\n');
}

// Role assignment (ساده و امن)
function assignRoles(game) {
  const count = game.players.size;
  const base = [];
  if (count >= 6 && count <= 8) base.push('Godfather','Mafia','Doctor','Detective');
  else if (count <= 12) base.push('Godfather','Mafia','MafiaSupport','Doctor','Detective','Sniper');
  else base.push('Godfather','Mafia','Mafia','MafiaSupport','Doctor','Detective','Sniper');

  while (base.length < count) base.push('Villager');

  const shuffled = base.sort(() => Math.random() - 0.5);
  let i = 0;
  for (const p of game.players.values()) {
    p.role = shuffled[i++];
  }
}

async function dmRoles(game) {
  for (const p of game.players.values()) {
    const user = await client.users.fetch(p.userId);
    try {
      await user.send(`نقش شما: ${p.role}\nاکشن شب را با پاسخ همین پیام اعلام کنید (اگر دارید).`);
    } catch {
      const channel = await client.channels.fetch(game.channelId);
      await channel.send(`<@${p.userId}> لطفاً DM خود را فعال کنید تا نقش برای شما ارسال شود.`);
    }
  }
}

// Slash command handling
client.on('interactionCreate', async (interaction) => {
  if (!interaction.isChatInputCommand()) return;

  const { commandName, channelId, user } = interaction;

  if (commandName === 'newgame') {
    if (getGame(channelId)) return interaction.reply({ content: 'در این کانال بازی فعال است.', ephemeral: true });
    initGame(channelId, user.id);
    return interaction.reply('اتاق مافیا ساخته شد. با /join وارد شوید. مدیر با /lock لابی را می‌بندد.');
  }

  if (commandName === 'join') {
    const game = getGame(channelId);
    if (!game || game.state !== 'Lobby') return interaction.reply({ content: 'لابی فعال نیست.', ephemeral: true });
    if (game.players.has(user.id)) return interaction.reply({ content: 'قبلاً joined شدی.', ephemeral: true });
    const member = await interaction.guild.members.fetch(user.id);
    game.players.set(user.id, { userId: user.id, displayName: member.displayName, role: null, alive: true });
    return interaction.reply(`<@${user.id}> وارد لابی شد. تعداد: ${game.players.size}`);
  }

  if (commandName === 'lock') {
    const game = getGame(channelId);
    if (!game || game.state !== 'Lobby') return interaction.reply({ content: 'لابی فعال نیست.', ephemeral: true });
    if (game.players.size < 6) return interaction.reply({ content: 'حداقل 6 نفر لازم است.', ephemeral: true });
    game.state = 'AssignRoles';
    assignRoles(game);
    await interaction.reply('لابی قفل شد. نقش‌ها در حال ارسال هستند…');
    await dmRoles(game);
    game.state = 'Night';
    game.log.push('شب اول آغاز شد.');
    return interaction.followUp('شب است. نقش‌ها اکشن‌های خود را تا 90 ثانیه آینده ثبت کنند.');
  }

  if (commandName === 'start') {
    const game = getGame(channelId);
    if (!game) return interaction.reply({ content: 'بازی‌ای وجود ندارد.', ephemeral: true });
    if (game.state !== 'Night') return interaction.reply({ content: 'الان زمان شروع شب نیست.', ephemeral: true });
    return interaction.reply('شب در حال اجراست. پس از اتمام، گزارش سحرگاه اعلام می‌شود.');
  }

  if (commandName === 'vote') {
    const game = getGame(channelId);
    if (!game || game.state !== 'Voting') return interaction.reply({ content: 'الان فاز رأی‌گیری نیست.', ephemeral: true });
    const target = interaction.options.getUser('user');
    if (!game.players.has(user.id) || !game.players.get(user.id).alive) return interaction.reply({ content: 'شما در بازی نیستید یا حذف شده‌اید.', ephemeral: true });
    if (!game.players.has(target.id) || !game.players.get(target.id).alive) return interaction.reply({ content: 'هدف معتبر نیست.', ephemeral: true });
    game.votes.set(user.id, target.id);
    const tally = tallyVotes(game);
    return interaction.reply(`رأی ثبت شد. شمارش فعلی:\n${formatTally(tally)}`);
  }

  if (commandName === 'unvote') {
    const game = getGame(channelId);
    if (!game || game.state !== 'Voting') return interaction.reply({ content: 'الان فاز رأی‌گیری نیست.', ephemeral: true });
    game.votes.delete(user.id);
    const tally = tallyVotes(game);
    return interaction.reply(`رأی شما حذف شد. شمارش فعلی:\n${formatTally(tally)}`);
  }

  if (commandName === 'status') {
    const game = getGame(channelId);
    if (!game) return interaction.reply({ content: 'بازی‌ای فعال نیست.', ephemeral: true });
    const alive = [...game.players.values()].filter(p => p.alive).map(p => p.displayName).join(', ');
    return interaction.reply(`فاز: ${game.state}\nزنده‌ها: ${alive || '—'}`);
  }

  if (commandName === 'end') {
    const game = getGame(channelId);
    if (!game) return interaction.reply({ content: 'بازی‌ای فعال نیست.', ephemeral: true });
    if (game.hostId !== user.id) return interaction.reply({ content: 'فقط میزبان می‌تواند پایان دهد.', ephemeral: true });
    const report = endGame(channelId, 'پایان اضطراری');
    return interaction.reply(`بازی پایان یافت.\n${report}`);
  }

  if (commandName === 'roles') {
    return interaction.reply('مود کلاسیک: Godfather, Mafia, MafiaSupport, Doctor, Detective, Sniper, Villager');
  }
});

// Voting helpers
function tallyVotes(game) {
  const counts = {};
  for (const targetId of game.votes.values()) {
    counts[targetId] = (counts[targetId] || 0) + 1;
  }
  return counts;
}
function formatTally(counts) {
  const entries = Object.entries(counts);
  if (!entries.length) return 'بدون رأی';
  return entries.map(([tid, c]) => `<@${tid}>: ${c}`).join('\n');
}

client.login(TOKEN);
