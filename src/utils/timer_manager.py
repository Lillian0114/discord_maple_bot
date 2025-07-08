import asyncio
from datetime import datetime, timedelta
import discord

active_timers = {}  # key: (guild_id, boss_name, game_channel)

def is_active(guild_id, boss_name, game_channel):
    return (guild_id, boss_name, game_channel) in active_timers

def cancel_timer(guild_id, boss_name, game_channel):
    key = (guild_id, boss_name, game_channel)
    if key in active_timers:
        active_timers[key]["task"].cancel()
        del active_timers[key]
        return True
    return False

async def start_timer(interaction: discord.Interaction, boss_name, game_channel, seconds, time_label, boss_times):
    key = (interaction.guild.id, boss_name, game_channel)
    end_time = datetime.now() + timedelta(seconds=seconds)
    channel = interaction.channel

    embed = discord.Embed(
        title=f"⏳ 已開始「{boss_name}」倒數計時",
        description=(
            f"遊戲頻道： {game_channel} \n"
            f"倒數時間： **{time_label}**\n"
            f"重生時間參考：{boss_times[boss_name]}"
        ),
        color=discord.Color.red()
    )
    try:
        await interaction.followup.send(embed=embed)
    except Exception as e:
        print(f"[start_timer] 初始訊息發送失敗：{e}")

    async def countdown():
        try:
            if seconds > 180:
                await asyncio.sleep(seconds - 180)
                try:
                    await channel.send(f"⏰「{boss_name}」在遊戲頻道 {game_channel} 還剩 3 分鐘！")
                except Exception as e:
                    print(f"[countdown] 發送 3 分鐘提醒失敗：{e}")

            await asyncio.sleep(180)
            try:
                await channel.send(f"🔔 {interaction.user.mention} 「{boss_name}」在遊戲頻道 {game_channel} 可能已經重生囉！")
            except Exception as e:
                print(f"[countdown] 發送重生提醒失敗：{e}")
        except asyncio.CancelledError:
            return
        finally:
            if key in active_timers:
                del active_timers[key]

    task = asyncio.create_task(countdown())
    active_timers[key] = {"task": task, "end_time": end_time}

def get_status(guild_id):
    now = datetime.now()
    status_list = []
    for (g_id, boss_name, game_channel), info in active_timers.items():
        if g_id != guild_id:
            continue
        remaining = info["end_time"] - now
        total = max(int(remaining.total_seconds()), 0)
        minutes, seconds = divmod(total, 60)
        hours, minutes = divmod(minutes, 60)
        status_list.append((boss_name, game_channel, hours, minutes, seconds))
    return status_list
