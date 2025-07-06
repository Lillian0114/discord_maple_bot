import discord
from discord.ext import commands
from config import TOKEN
from utils.time_parser import load_boss_times
from utils.timer_manager import start_timer, cancel_timer, get_status, is_active
from datetime import datetime

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='/', intents=intents)

# 載入王時間資料
boss_times, boss_time_seconds = load_boss_times()

@bot.event
async def on_ready():
    print(f'機器人已上線：{bot.user}')

@bot.command()
async def timer(ctx, boss_name: str, game_channel: str):
    if is_active(boss_name, game_channel):
        await ctx.send(f"「{boss_name}」在頻道 {game_channel} 已經在倒數中囉！")
        return

    if boss_name not in boss_time_seconds:
        await ctx.send(f"找不到「{boss_name}」的重生時間資料")
        return

    seconds = boss_time_seconds[boss_name]
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    label = f"{hours} 小時 {minutes} 分鐘" if hours else f"{minutes} 分鐘"

    await start_timer(ctx, boss_name, game_channel, seconds, label, boss_times)

@bot.command()
async def cancel(ctx, boss_name: str, game_channel: str):
    if cancel_timer(boss_name, game_channel):
        await ctx.send(f"「{boss_name}」在頻道 {game_channel} 的倒數已取消")
    else:
        await ctx.send(f"沒有在頻道 {game_channel} 發現「{boss_name}」的倒數")

@bot.command()
async def status(ctx):
    status_list = get_status()
    if not status_list:
        await ctx.send("📭 目前沒有任何王在倒數中。")
        return

    # 每 25 個分一頁
    chunks = [status_list[i:i+25] for i in range(0, len(status_list), 25)]

    for page_num, chunk in enumerate(chunks, start=1):
        embed = discord.Embed(
            title=f"⏳ 正在倒數的王（第 {page_num}/{len(chunks)} 頁）",
            color=discord.Color.orange()
        )

        for boss, channel, h, m, s in chunk:
            parts = []
            if h > 0: parts.append(f"{h} 小時")
            if m > 0: parts.append(f"{m} 分")
            if s > 0 or not parts: parts.append(f"{s} 秒")
            time_left = " ".join(parts)

            embed.add_field(
                name=f"{boss}（頻道 {channel}）",
                value=f"剩餘時間：**{time_left}**",
                inline=False
            )

        await ctx.send(embed=embed)

@bot.command()
async def search(ctx, keyword: str):
    keyword = keyword.strip()
    matches = {boss: time for boss, time in boss_times.items() if keyword in boss}

    if not matches:
        await ctx.send(f"❌ 找不到包含「{keyword}」的王名")
        return

    chunks = list(matches.items())
    pages = [chunks[i:i+25] for i in range(0, len(chunks), 25)]

    for idx, page in enumerate(pages):
        embed = discord.Embed(
            title=f"🔍 搜尋結果：包含「{keyword}」的王（第 {idx+1}/{len(pages)} 頁）",
            color=discord.Color.green()
        )
        for boss, time_range in page:
            embed.add_field(name=boss, value=time_range, inline=False)
        await ctx.send(embed=embed)

@bot.command()
async def boss_list(ctx):
    boss_list = list(boss_times.items())
    chunks = [boss_list[i:i+25] for i in range(0, len(boss_list), 25)]

    for index, chunk in enumerate(chunks):
        embed = discord.Embed(
            title=f"📚 所有 Boss 重生時間（第 {index+1}/{len(chunks)} 頁）",
            color=discord.Color.teal()
        )
        for boss, time_range in chunk:
            embed.add_field(name=boss, value=time_range, inline=False)
        await ctx.send(embed=embed)


bot.run(TOKEN)
