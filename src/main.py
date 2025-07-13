import discord
import asyncio
from discord.ext import commands
from discord import app_commands
from config import TOKEN
from utils.time_parser import load_boss_times, save_boss_times_from_web
from utils.timer_manager import start_timer, cancel_timer, get_status, is_active

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)
tree = bot.tree

# 載入 Boss 時間
boss_times, boss_time_seconds = load_boss_times()

async def update_boss_times_periodically():
    global boss_times, boss_time_seconds
    while True:
        updated = await save_boss_times_from_web()
        if updated:
            boss_times, boss_time_seconds = load_boss_times()
            print("✅ boss_times 已自動同步到記憶體")
        await asyncio.sleep(14400)

# MY_GUILDS = [discord.Object(id=gid) for gid in GUILD_ID]

@bot.event
async def on_ready():
    # 開始背景任務，定時更新 boss_time.json 並同步記憶體
    bot.loop.create_task(update_boss_times_periodically())
    await tree.sync()
    # for g in MY_GUILDS:
    #     await tree.sync(guild=g)
    print(f"機器人已上線: {bot.user}")

@tree.command(name="timer", description="開始設定該王的重生倒數")
@app_commands.describe(boss_name="王名", game_channel="遊戲頻道名稱")
async def timer(interaction: discord.Interaction, boss_name: str, game_channel: str):
    if is_active(interaction.guild.id, boss_name, game_channel):
        await interaction.response.send_message(
            f"「{boss_name}」在遊戲頻道 {game_channel} 已經在倒數中囉！", ephemeral=True)
        return

    if boss_name not in boss_time_seconds:
        await interaction.response.send_message(
            f"找不到「{boss_name}」的重生時間資料", ephemeral=True)
        return

    await interaction.response.defer()

    seconds = boss_time_seconds[boss_name]
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    label = f"{hours} 小時 {minutes} 分鐘" if hours else f"{minutes} 分鐘"

    await start_timer(interaction, boss_name, game_channel, seconds, label, boss_times)

@tree.command(name="cancel", description="取消王的重生倒數")
@app_commands.describe(boss_name="王名", game_channel="遊戲頻道名稱")
async def cancel(interaction: discord.Interaction, boss_name: str, game_channel: str):
    if cancel_timer(interaction.guild.id, boss_name, game_channel):
        await interaction.response.send_message(f"「{boss_name}」在遊戲頻道 {game_channel} 的倒數已取消")
    else:
        await interaction.response.send_message(f"沒有在遊戲頻道 {game_channel} 發現「{boss_name}」的倒數")

@tree.command(name="status", description="查看目前正在倒數的王")
async def status(interaction: discord.Interaction):
    status_list = get_status(interaction.guild.id)
    if not status_list:
        await interaction.response.send_message("📬 目前沒有任何王在倒數中")
        return

    await interaction.response.defer()

    chunks = [status_list[i:i + 25] for i in range(0, len(status_list), 25)]

    for page_num, chunk in enumerate(chunks, start=1):
        embed = discord.Embed(
            title=f"⏳ 正在倒數的王 (第 {page_num}/{len(chunks)} 頁)",
            color=discord.Color.orange()
        )
        for boss, channel, h, m, s in chunk:
            parts = []
            if h > 0: parts.append(f"{h} 小時")
            if m > 0: parts.append(f"{m} 分")
            if s > 0 or not parts: parts.append(f"{s} 秒")
            time_left = " ".join(parts)

            embed.add_field(
                name=f"{boss} (頻道 {channel})",
                value=f"剩餘時間: **{time_left}**",
                inline=False
            )
        await interaction.followup.send(embed=embed)

@tree.command(name="search", description="搜尋包含關鍵字的王名")
@app_commands.describe(keyword="王名關鍵字")
async def search(interaction: discord.Interaction, keyword: str):
    matches = {boss: time for boss, time in boss_times.items() if keyword in boss}
    if not matches:
        await interaction.response.send_message(f"❌ 找不到包含「{keyword}」的王名")
        return

    await interaction.response.defer()

    chunks = list(matches.items())
    pages = [chunks[i:i + 25] for i in range(0, len(chunks), 25)]

    for idx, page in enumerate(pages):
        embed = discord.Embed(
            title=f"🔍 搜尋結果: 包含「{keyword}」的王 (第 {idx + 1}/{len(pages)} 頁)",
            color=discord.Color.green()
        )
        for boss, time_range in page:
            embed.add_field(name=boss, value=time_range, inline=False)
        await interaction.followup.send(embed=embed)

@tree.command(name="boss_list", description="顯示所有已定義的 Boss 重生時間")
async def boss_list(interaction: discord.Interaction):
    await interaction.response.defer()

    boss_list = list(boss_times.items())
    chunks = [boss_list[i:i + 25] for i in range(0, len(boss_list), 25)]

    for index, chunk in enumerate(chunks):
        embed = discord.Embed(
            title=f"📚 所有 Boss 重生時間 (第 {index + 1}/{len(chunks)} 頁)",
            color=discord.Color.teal()
        )
        for boss, time_range in chunk:
            embed.add_field(name=boss, value=time_range, inline=False)
        await interaction.followup.send(embed=embed)

@tree.command(name="help", description="顯示指令列表")
async def help_me(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Boss Timer Bot 指令列表",
        description="以下是此機器人可用指令:",
        color=discord.Color.blue()
    )
    embed.add_field(name="`/timer 王名 頻道`", value="開始重生倒數", inline=False)
    embed.add_field(name="`/cancel 王名 頻道`", value="取消倒數", inline=False)
    embed.add_field(name="`/status`", value="查看目前倒數王", inline=False)
    embed.add_field(name="`/search 關鍵字`", value="搜尋王名", inline=False)
    embed.add_field(name="`/boss_list`", value="顯示所有 Boss", inline=False)
    embed.add_field(name="`/help`", value="顯示此說明", inline=False)
    await interaction.response.send_message(embed=embed)

bot.run(TOKEN)