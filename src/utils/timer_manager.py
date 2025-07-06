import asyncio
from datetime import datetime, timedelta
import discord

active_timers = {}

def is_active(boss_name, game_channel):
    return (boss_name, game_channel) in active_timers

def cancel_timer(boss_name, game_channel):
    key = (boss_name, game_channel)
    if key in active_timers:
        active_timers[key]["task"].cancel()
        del active_timers[key]
        return True
    return False

async def start_timer(interaction: discord.Interaction, boss_name, game_channel_name: str, seconds, time_label, boss_times):
    key = (boss_name, game_channel_name)
    end_time = datetime.now() + timedelta(seconds=seconds)

    embed = discord.Embed(
        title=f"⏳ 已開始「{boss_name}」倒數計時",
        description=(
            f"遊戲頻道： {game_channel_name} \n"
            f"倒數時間： **{time_label}**\n"
            f"重生時間參考：{boss_times[boss_name]}"
        ),
        color=discord.Color.red()
    )
    await interaction.followup.send(embed=embed)

    bot = interaction.client
    discord_channel = interaction.channel  # Discord 指令執行頻道物件

    async def countdown():
        try:
            if seconds > 180:
                await asyncio.sleep(seconds - 180)
                await discord_channel.send(f"⏰「{boss_name}」在遊戲頻道 {game_channel_name} 還剩 3 分鐘！")

            await asyncio.sleep(180)
            await discord_channel.send(f"🔔 {interaction.user.mention} 「{boss_name}」在遊戲頻道 {game_channel_name} 可能已經重生囉！")
        except asyncio.CancelledError:
            return
        finally:
            if key in active_timers:
                del active_timers[key]

    task = asyncio.create_task(countdown())
    active_timers[key] = {"task": task, "end_time": end_time}

    task = asyncio.create_task(countdown())
    active_timers[key] = {"task": task, "end_time": end_time}

def get_status():
    from datetime import datetime
    now = datetime.now()
    status_list = []
    for (boss_name, game_channel), info in active_timers.items():
        remaining = info["end_time"] - now
        total = int(remaining.total_seconds())
        if total < 0:
            total = 0
        minutes, seconds = divmod(total, 60)
        hours, minutes = divmod(minutes, 60)
        status_list.append((boss_name, game_channel, hours, minutes, seconds))
    return status_list
