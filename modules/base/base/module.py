import datetime
from math import ceil

import discord
from discord.ext import commands

from core import TranslationContext
from core import check, text, logging, utils

from .database import AutoPin, AutoThread, Bookmark

tr = text.Translator(__file__).translate
bot_log = logging.Bot.logger()
guild_log = logging.Guild.logger()


class Base(commands.Cog):
    """Basic bot functions."""

    def __init__(self, bot):
        self.bot = bot

        self.boot = datetime.datetime.now().replace(microsecond=0)

    #

    @commands.command()
    async def ping(self, ctx):
        """Return latency information."""
        await ctx.send(tr("ping", "reply", ctx, time="{:.2f}".format(self.bot.latency)))

    @commands.command()
    async def uptime(self, ctx):
        """Return uptime information."""
        now = datetime.datetime.now().replace(microsecond=0)
        delta = now - self.boot

        embed = utils.Discord.create_embed(
            author=ctx.author,
            title=tr("uptime", "title", ctx),
        )
        embed.add_field(
            name=tr("uptime", "time_since", ctx),
            value=utils.Time.datetime(self.boot),
            inline=False,
        )
        embed.add_field(
            name=tr("uptime", "time_delta", ctx),
            value=str(delta),
            inline=False,
        )

        await ctx.send(embed=embed)

    @commands.guild_only()
    @commands.check(check.acl)
    @commands.group(name="autopin")
    async def autopin(self, ctx):
        await utils.Discord.send_help(ctx)

    @commands.check(check.acl)
    @autopin.command(name="get")
    async def autopin_get(self, ctx, channel: discord.TextChannel = None):
        embed = utils.Discord.create_embed(
            author=ctx.author, title=tr("autopin get", "title", ctx)
        )
        limit: int = getattr(AutoPin.get(ctx.guild.id, None), "limit", 0)
        value: str = f"{limit}" if limit > 0 else tr("autopin get", "disabled", ctx)
        embed.add_field(
            name=tr("autopin get", "limit", ctx),
            value=value,
        )

        if channel is None:
            channel = ctx.channel

        channel_pref = AutoPin.get(ctx.guild.id, channel.id)
        if channel_pref is not None:
            embed.add_field(
                name=tr("autopin get", "channel", ctx, channel=channel.name),
                value=f"{channel_pref.limit}"
                if channel_pref.limit > 0
                else tr("autopin get", "disabled", ctx),
            )

        await ctx.send(embed=embed)

    @commands.check(check.acl)
    @autopin.command(name="set")
    async def autopin_set(self, ctx, limit: int, channel: discord.TextChannel = None):
        """Set autopin limit."""
        if limit < 1:
            raise commands.ArgumentError("Limit has to be at least one.")

        if channel is None:
            AutoPin.add(ctx.guild.id, None, limit)
            await guild_log.info(
                ctx.author,
                ctx.channel,
                f"Global autopin limit set to {limit}.",
            )
        else:
            AutoPin.add(ctx.guild.id, channel.id, limit)
            await guild_log.info(
                ctx.author,
                ctx.channel,
                f"#{channel.name} autopin limit set to {limit}.",
            )

        if limit == 0:
            await ctx.reply(tr("autopin set", "disabled", ctx))
        else:
            await ctx.reply(tr("autopin set", "reply", ctx))

    @commands.check(check.acl)
    @autopin.command(name="unset")
    async def autopin_unset(self, ctx, channel: discord.TextChannel = None):
        if channel is None:
            AutoPin.remove(ctx.guild.id, None)
            await guild_log.info(ctx.author, ctx.channel, "Autopin unset globally.")
        else:
            AutoPin.remove(ctx.guild.id, channel.id)
            await guild_log.info(
                ctx.author, ctx.channel, f"Autopin unset in #{channel.name}."
            )
        await ctx.reply(tr("autopin unset", "reply"))

    @commands.guild_only()
    @commands.check(check.acl)
    @commands.group(name="bookmarks")
    async def bookmarks(self, ctx):
        await utils.Discord.send_help(ctx)

    @commands.check(check.acl)
    @bookmarks.command(name="get")
    async def bookmarks_get(self, ctx, channel: discord.TextChannel = None):
        embed = utils.Discord.create_embed(
            author=ctx.author, title=tr("bookmarks get", "title", ctx)
        )
        enabled: int = getattr(Bookmark.get(ctx.guild.id, None), "enabled", False)
        embed.add_field(
            name=tr("bookmarks get", "settings", ctx),
            value=tr("bookmarks get", str(enabled), ctx),
        )

        if channel is None:
            channel = ctx.channel

        channel_pref = Bookmark.get(ctx.guild.id, channel.id)
        if channel_pref is not None:
            embed.add_field(
                name=tr("bookmarks get", "channel", ctx, channel=channel.name),
                value=tr("bookmarks get", str(channel_pref.enabled), ctx),
            )

        await ctx.send(embed=embed)

    @commands.check(check.acl)
    @bookmarks.command(name="set")
    async def bookmarks_set(
        self, ctx, enabled: bool, channel: discord.TextChannel = None
    ):
        """Enable or disable bookmarking."""
        if channel is None:
            Bookmark.add(ctx.guild.id, None, enabled)
            await guild_log.info(
                ctx.author, ctx.channel, f"Global bookmarks set to {enabled}."
            )
        else:
            Bookmark.add(ctx.guild.id, channel.id, enabled)
            await guild_log.info(
                ctx.author, ctx.channel, f"#{channel.name} bookmarks set to {enabled}."
            )
        await ctx.reply(tr("bookmarks set", str(enabled), ctx))

    @commands.check(check.acl)
    @bookmarks.command(name="unset")
    async def bookmarks_unset(self, ctx, channel: discord.TextChannel = None):
        """Remove bookmark settings."""
        if channel is None:
            Bookmark.remove(ctx.guild.id, None)
            await guild_log.info(ctx.author, ctx.channel, "Bookmarking unset globally.")
        else:
            Bookmark.remove(ctx.guild.id, channel.id)
            await guild_log.info(
                ctx.author, ctx.channel, f"Bookmarking unset in #{channel.name}."
            )
        await ctx.reply(tr("bookmarks unset", "reply"))

    @commands.guild_only()
    @commands.check(check.acl)
    @commands.group(name="autothread", aliases=["autothreads"])
    async def autothread(self, ctx):
        await utils.Discord.send_help(ctx)

    @commands.check(check.acl)
    @autothread.command(name="get")
    async def autothread_get(self, ctx, channel: discord.TextChannel = None):
        embed = utils.Discord.create_embed(
            author=ctx.author, title=tr("autothread get", "title", ctx)
        )
        limit: int = getattr(AutoThread.get(ctx.guild.id, None), "limit", 0)
        value: str = f"{limit}" if limit > 0 else tr("autothread get", "disabled", ctx)
        embed.add_field(
            name=tr("autothread get", "limit", ctx),
            value=value,
        )
        if discord.version_info.major < 2:
            embed.add_field(
                name=tr("autothread get", "warning", ctx),
                value=tr("autothread get", "support", ctx),
                inline=False,
            )

        if channel is None:
            channel = ctx.channel

        channel_pref = AutoThread.get(ctx.guild.id, channel.id)
        if channel_pref is not None:
            embed.add_field(
                name=tr("autothread get", "channel", ctx, channel=channel.name),
                value=f"{channel_pref.limit}"
                if channel_pref.limit > 0
                else tr("autothread get", "disabled", ctx),
            )

        await ctx.send(embed=embed)

    @commands.check(check.acl)
    @autothread.command(name="set")
    async def autothread_set(
        self, ctx, limit: int, channel: discord.TextChannel = None
    ):
        if limit < 1:
            raise commands.ArgumentError("Limit has to be at least one.")

        if channel is None:
            AutoThread.add(ctx.guild.id, None, limit)
            await guild_log.info(
                ctx.author,
                ctx.channel,
                f"Global autothread limit set to {limit}.",
            )
        else:
            AutoThread.add(ctx.guild.id, channel.id, limit)
            await guild_log.info(
                ctx.author,
                ctx.channel,
                f"#{channel.name} autothread limit set to {limit}.",
            )

        if limit == 0:
            await ctx.reply(tr("autothread set", "disabled", ctx))
        else:
            await ctx.reply(tr("autothread set", "reply", ctx))

    @commands.check(check.acl)
    @autothread.command(name="unset")
    async def autothread_unset(self, ctx, channel: discord.TextChannel = None):
        if channel is None:
            AutoThread.remove(ctx.guild.id, None)
            await guild_log.info(ctx.author, ctx.channel, "Autothread unset globally.")
        else:
            AutoThread.remove(ctx.guild.id, channel.id)
            await guild_log.info(
                ctx.author, ctx.channel, f"Autothread unset in #{channel.name}."
            )
        await ctx.reply(tr("autothread unset", "reply"))

    #

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        """Handle message pinning."""
        if payload.guild_id is None or payload.member is None:
            return

        message = await utils.Discord.get_message(
            self.bot, payload.guild_id, payload.channel_id, payload.message_id
        )
        if message is None:
            await bot_log.error(
                payload.member,
                None,
                "Could not find message "
                + utils.Discord.message_url_from_reaction_payload(payload),
            )
            return

        # do not allow the actions on system messages (boost announcements etc.)
        if message.type != discord.MessageType.default:
            return

        emoji = getattr(payload.emoji, "name", None)
        if emoji == "📌" or emoji == "📍":
            await self._autopin(payload, message, emoji)
        elif emoji == "🔖":
            await self._bookmark(payload, message)
        elif emoji == "🧵":
            await self._autothread(payload, message)

    async def _autopin(
        self,
        payload: discord.RawReactionActionEvent,
        message: discord.Message,
        emoji: str,
    ):
        """Handle autopin functionality."""
        tc = TranslationContext(payload.guild_id, payload.user_id)

        if emoji == "📍" and not payload.member.bot:
            await payload.member.send(tr("_autopin", "bad pin emoji", tc))
            await utils.Discord.remove_reaction(message, emoji, payload.member)
            return

        for reaction in message.reactions:
            if reaction.emoji != "📌":
                continue

            # remove if the message is pinned or is in unpinnable channel
            if message.pinned:
                await guild_log.debug(
                    payload.member,
                    message.channel,
                    f"Removing {payload.user_id}'s pin: Message is already pinned.",
                )
                await reaction.clear()
                return

            # stop if there isn't enough pins
            limit: int = getattr(
                AutoPin.get(payload.guild_id, payload.channel_id), "limit", -1
            )
            # overwrite for channel doesn't exist, use guild preference
            if limit < 0:
                limit = getattr(AutoPin.get(payload.guild_id, None), "limit", 0)
            if limit == 0 or reaction.count < limit:
                return

            try:
                await message.pin()
                await guild_log.info(
                    payload.member,
                    message.channel,
                    f"Pinned message {message.jump_url}",
                )
            except discord.errors.HTTPException:
                await guild_log.error(
                    payload.member, message.channel, "Could not pin message."
                )
                return

            await reaction.clear()
            await message.add_reaction("📍")

    async def _bookmark(
        self, payload: discord.RawReactionActionEvent, message: discord.Message
    ):
        """Handle bookmark functionality."""
        if not Bookmark.get(payload.guild_id).enabled:
            return

        tc = TranslationContext(payload.guild_id, payload.user_id)

        embed = utils.Discord.create_embed(
            author=payload.member,
            title=tr("_bookmark", "title", tc),
            description=message.content[:2000],
        )
        embed.set_author(
            name=message.author.display_name, icon_url=message.author.avatar_url
        )

        timestamp = utils.Time.datetime(message.created_at)
        embed.add_field(
            name=f"{timestamp} UTC",
            value=tr(
                "_bookmark",
                "info",
                tc,
                guild=utils.Text.sanitise(message.guild.name),
                channel=utils.Text.sanitise(message.channel.name),
                link=message.jump_url,
            ),
            inline=False,
        )

        if len(message.attachments):
            embed.add_field(
                name=tr("_bookmark", "files", tc),
                value=tr("_bookmark", "total", tc, count=len(message.attachments)),
            )
        if len(message.embeds):
            embed.add_field(
                name=tr("_bookmark", "embeds", tc),
                value=tr("_bookmark", "total", tc, count=len(message.embeds)),
            )

        await utils.Discord.remove_reaction(message, payload.emoji, payload.member)
        await payload.member.send(embed=embed)

        await guild_log.debug(
            payload.member, message.channel, f"Bookmarked message {message.jump_url}."
        )

    async def _autothread(
        self,
        payload: discord.RawReactionActionEvent,
        message: discord.Message,
    ):
        """Handle autothread functionality."""
        # only new versions of discord.py support threads
        if discord.version_info.major < 2:
            return
        tc = TranslationContext(payload.guild_id, payload.user_id)

        for reaction in message.reactions:
            if reaction.emoji != "🧵":
                continue

            # we can't open threads inside of threads
            if isinstance(message.channel, discord.Thread):
                await reaction.clear()
                return

            # get emoji limit for channel
            limit: int = getattr(
                AutoThread.get(payload.guild_id, payload.channel_id), "limit", -1
            )
            # overwrite for channel doesn't exist, use guild preference
            if limit < 0:
                limit = getattr(AutoThread.get(payload.guild_id, None), "limit", 0)

            # get message's existing thread
            thread_of_message: discord.Thread = None  # used globally in this loop
            if message.flags.has_thread:
                for thread in message.channel.threads:
                    if thread.id == message.id:
                        thread_of_message = thread
                        break
                # check if the given message has an archived thread
                if message.flags.has_thread:
                    if thread_of_message.archived:
                        # lower emoji limit
                        limit = ceil(limit * 0.75)
                    else:
                        await reaction.clear()
                        return

            # stop if there isn't enough thread reactions
            if limit == 0 or reaction.count < limit:
                return
            # unarchive thread if exists and is archived (filtered out previously)
            if thread_of_message is not None:
                await thread_of_message.edit(archived=False)
                await guild_log.info(
                    payload.member,
                    message.channel,
                    f"Thread unarchived on a message {message.jump_url}.",
                )
                await reaction.clear()
                return
            # create a new thread
            try:
                thread_name = (
                    tr("_autothread", "thread", tc) + " " + message.author.name
                )
                await message.create_thread(name=thread_name)
                await guild_log.info(
                    payload.member,
                    message.channel,
                    f"Thread opened on a message {message.jump_url}.",
                )
            except discord.errors.HTTPException:
                await guild_log.error(
                    payload.member,
                    message.channel,
                    f"Could not open a thread on a message {message.jump_url}.",
                )
                return

            await reaction.clear()


def setup(bot) -> None:
    bot.add_cog(Base(bot))
