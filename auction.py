import asyncio

class Auction:
    def __init__(self, seconds, start_bid, item_desc, channel, bot_user):
        self.seconds = seconds
        self.current_bid = 0
        self.min_bid = start_bid
        self.desc = item_desc
        self.channel = channel
        self.user = bot_user
        self.auctioning = True
        self.highest_bidder = "No one"
        self.check = lambda msg: msg.author != self.user and msg.channel is channel and (msg.content.strip().isdigit() and int(msg.content) >= self.min_bid) or msg.content == "."

    async def countdown(self, seconds, countdown_from = 5):
        while seconds > 0:
            if seconds <= countdown_from:
                await self.channel.send(seconds)
            await asyncio.sleep(1)
            seconds -= 1

