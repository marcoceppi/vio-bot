
import os
import sys
import asyncio
import logging

from pathlib import Path
from aioslack.core import Slack
from viobot import config

log = logging.getLogger(__name__)


class VIOBot(object):
    def __init__(self, config):
        self.config = config
        slack_config = self.config.get('slack', {})
        self.slack = Slack(slack_config['access-token'])

    async def run(self):
        async for event in self.slack.rtm():
            await self.handler(event)

    # This exists as the aioslack library does not present the websocket for writing :(
    async def _request(self, method, **kwargs):
        return await self.slack.api(method, **kwargs)

    async def send(self, channel, text):
        return await self._request('chat.postMessage', channel=channel, text=text)

    async def handler(self, event):
        event_type = event.type
        handler_name = '{}_handler'.format(event_type)

        if not hasattr(self, handler_name):
            log.debug('Could not process "{}" event'.format(event_type))
            return

        func = getattr(self, handler_name)
        await func(event)

    async def message_handler(self, event):
        message = SlackMessage(event)
        if message.subtype == 'bot_message':
            return

        log.info('Got a message from {}'.format(message.user))
        await self.send(message.channel, 'Got it boss')

    async def user_typing_handler(self, event):
        pass


class SlackMessage(object):
    def __init__(self, event):
        self.text = event.text
        self.subtype = None
        self.user = None
        self.blocks = None

        if hasattr(event, 'subtype'):
            self.subtype = event.subtype

        if hasattr(event, 'user'):
            self.user = event.user

        if hasattr(event, 'blocks'):
            self.blocks = event.blocks

        self.team = event.team
        self.channel = event.channel

if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    loop = asyncio.get_event_loop()
    bot = VIOBot(config.read(os.environ.get('VIO_BOT_CONFIG', Path(__file__).parent.parent / 'config' / 'config.yaml')))
    loop.run_until_complete(bot.run())
