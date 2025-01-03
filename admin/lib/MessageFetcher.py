from telethon.client.telegramclient import TelegramClient # type: ignore
from telethon.tl.types import ( # type: ignore
    Channel,
)
from .config import StrategyConfig
from .DatabaseService import DatabaseService
from . import messageStrategies as strat
from .types import MessageGenerator, MessageIter


class MessageFetcher:
    def __init__(self, client: TelegramClient, db: DatabaseService, cfg: StrategyConfig):
        self.client = client
        self.db = db
        self.config = cfg

    async def get_channel_messages(self, channel: Channel) -> MessageGenerator:
        strategy = await self._get_strategy(channel, self.config.strategy, self.config.limit)
        async for message in strategy:
            yield message


    async def _get_strategy(self, channel: Channel, strategy: str, limit: int | None) -> MessageIter:
        match strategy:
            case "all":
                return strat.get_all_messages(self.client, channel, limit)
            case "db":
                last_seen_post = self.db.get_last_seen_post(channel.id)
                return strat.get_messages_since_db_update(self.client, channel, last_seen_post, limit)
            case "oldest":
                return strat.get_oldest_messages(self.client, channel, limit)
            case "before":
                before_id = self.db.get_last_seen_post(channel.id)
                return strat.get_earlier_unseen_messages(self.client, channel, before_id, limit)
            case "urls":
                return strat.get_urls(self.client, channel, limit)
            case "videos":
                return strat.get_all_videos(self.client, channel, limit)
            case "unread":
                return await strat.get_unread_messages(self.client, channel)
            case _:
                raise ValueError(f"unknown message strategy: {strategy}")
