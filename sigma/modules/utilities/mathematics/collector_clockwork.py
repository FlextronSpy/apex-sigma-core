# Apex Sigma: The Database Giant Discord Bot.
# Copyright (C) 2017  Lucia's Cipher
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import asyncio
import string

import discord

collector_loop_running = False


async def check_queued(db, uid):
    return bool(await db[db.db_cfg.database].CollectorQueue.find_one({'UserID': uid}))


async def add_to_queue(db, collector_item):
    await db[db.db_cfg.database].CollectorQueue.insert_one(collector_item)


async def get_queue_size(db):
    return await db[db.db_cfg.database].CollectorQueue.count()


def check_for_bot_prefixes(prefix, text):
    common_pfx = [prefix, '!', '/', '\\', '~', '.', '>', '<', '-', '_', '?']
    prefixed = False
    for pfx in common_pfx:
        if text.startswith(pfx):
            prefixed = True
            break
    return prefixed


def get_channel(msg):
    if msg.channel_mentions:
        target_chn = msg.channel_mentions[0]
    else:
        target_chn = msg.channel
    return target_chn


def get_target(msg):
    if msg.mentions:
        target_usr = msg.mentions[0]
    else:
        target_usr = msg.author
    return target_usr


def check_for_bad_content(text):
    disalloed = ['```', 'http', '"']
    bad = False
    for cont in disalloed:
        if cont in text:
            bad = True
            break
    return bad


def clean_bad_chars(text):
    unallowed_chars = ['`', '\n', '\\', '\\n']
    for char in unallowed_chars:
        text = text.replace(char, '')
    return text


def replace_mentions(log, text):
    if log.mentions:
        for mention in log.mentions:
            text = text.replace(mention.mention, mention.name)
    if log.channel_mentions:
        for mention in log.channel_mentions:
            text = text.replace(mention.mention, mention.name)
    return text


def punctuate_content(text):
    text = text.strip()
    last_char = text[-1]
    if last_char not in string.punctuation:
        text += '.'
    return text


def cleanse_content(log, text):
    text = replace_mentions(log, text)
    text = clean_bad_chars(text)
    text = punctuate_content(text)
    return text


async def notify_target(ath, tgt_usr, tgt_chn, cltd, cltn):
    req_usr = ('you' if ath.id == tgt_usr.id else ath.name) if ath else 'Unknown User'
    title = f'✅ Added {cltd} entries to your chain, {len(cltn)} entries total.'
    footer = f'Chain requested by {req_usr} in #{tgt_chn.name} on {tgt_chn.guild.name}.'
    ftr_icn = tgt_chn.guild.icon_url or 'https://i.imgur.com/xpDpHqz.png'
    response = discord.Embed(color=0x66CC66, title=title)
    response.set_footer(text=footer, icon_url=ftr_icn)
    try:
        await tgt_usr.send(embed=response)
    except Exception:
        pass


async def collector_clockwork(ev):
    global collector_loop_running
    if not collector_loop_running:
        collector_loop_running = True
        ev.bot.loop.create_task(cycler(ev))


async def cycler(ev):
    while True:
        if ev.bot.is_ready():
            cltr_item = await ev.db[ev.db.db_cfg.database].CollectorQueue.find_one_and_delete({})
            if cltr_item:
                cl_usr = discord.utils.find(lambda x: x.id == cltr_item.get('UserID'), ev.bot.get_all_members())
                cl_chn = discord.utils.find(lambda x: x.id == cltr_item.get('ChannelID'), ev.bot.get_all_channels())
                cl_ath = discord.utils.find(lambda x: x.id == cltr_item.get('AuthorID'), ev.bot.get_all_members())
                if cl_usr and cl_chn:
                    collected = 0
                    collection = await ev.db[ev.db.db_cfg.database].MarkovChains.find_one({'UserID': cl_usr.id})
                    collection = collection.get('Chain') if collection else []
                    pfx = await ev.db.get_guild_settings(cl_chn.guild.id, 'Prefix') or ev.bot.cfg.pref.prefix
                    try:
                        async for log in cl_chn.history(limit=100000):
                            cnt = log.content
                            if log.author.id == cl_usr.id and len(log.content) > 8:
                                if not check_for_bot_prefixes(pfx, cnt) and not check_for_bad_content(cnt):
                                    cnt = cleanse_content(log, cnt)
                                    if cnt not in collection:
                                        collection.append(cnt)
                                        collected += 1
                                        if collected >= 5000:
                                            break
                    except Exception:
                        pass
                    insert_data = {'UserID': cl_usr.id, 'Chain': collection}
                    await ev.db[ev.db.db_cfg.database].MarkovChains.delete_one({'UserID': cl_usr.id})
                    await ev.db[ev.db.db_cfg.database].MarkovChains.insert_one(insert_data)
                    await notify_target(cl_ath, cl_usr, cl_chn, collected, collection)
        await asyncio.sleep(1)
