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

import discord
from humanfriendly.tables import format_pretty_table as boop

from sigma.core.mechanics.command import SigmaCommand
from sigma.core.utilities.data_processing import user_avatar
from .nodes.item_core import ItemCore
from .nodes.properties import rarity_names

item_core = None


async def chances(cmd: SigmaCommand, message: discord.Message, args: list):
    global item_core
    if not item_core:
        item_core = ItemCore(cmd.resource('data'))
    if message.mentions:
        target = message.mentions[0]
    else:
        target = message.author
    upgrade_file = await cmd.db[cmd.db.db_cfg.database].Upgrades.find_one({'UserID': target.id}) or {}
    upgrade_level = upgrade_file.get('luck') or 0
    top_roll, rarities = item_core.create_roll_range(upgrade_level)
    out_lines = []
    table_head = ['Rarity', 'Chance']
    for rarity_key in rarities.keys():
        if rarity_key != 0:
            new_key = rarity_key - 1
            range_top = rarities.get(rarity_key) - rarities.get(new_key)
            chance = round((range_top / top_roll) * 100, 5)
            out_line = [rarity_names.get(new_key).title(), f'{chance}%']
            out_lines.append(out_line)
    range_top = top_roll - rarities.get(9)
    chance = round((range_top / top_roll) * 100, 5)
    out_line = [rarity_names.get(9).title(), f'{chance}%']
    out_lines.append(out_line)
    description = f'Your luck is **Lv{upgrade_level}** with a top roll of **{top_roll}**.'
    out_table = boop(out_lines, table_head)
    response = discord.Embed(color=0x1b6f5f)
    response.set_author(name=f'{target.name}\'s Item Chances', icon_url=user_avatar(target))
    response.add_field(name='General Stats', value=description, inline=False)
    response.add_field(name='Chances Table', value=f'```bat\n{out_table}\n```', inline=False)
    await message.channel.send(embed=response)
