import asyncio

from sigma.modules.games.warframe.commons.cycles.generic import send_to_channels
from sigma.modules.games.warframe.commons.parsers.fissure_parser import get_fissure_data, generate_fissure_embed


async def fissure_clockwork(ev):
    try:
        ev.bot.loop.create_task(cycler(ev))
    except Exception as err:
        ev.log.error(f'Couldn\'t complete a cycle. | Error: {err.with_traceback}')


async def cycler(ev):
    while True:
        fissures = await get_fissure_data(ev.db)
        if fissures:
            response = generate_fissure_embed(fissures)
            await send_to_channels(ev, response, 'WarframeFissureChannel')
        await asyncio.sleep(2)