import json
import logging
import re

import aiohttp
import discord
from discord.ext import commands

log = logging.getLogger(__name__)
err_regex = re.compile(r"^error(\[.*\])*:", re.MULTILINE)


class CodeBlock:
    missing_error = "Missing code block. Please use the following markdown\n\\`\\`\\`rust\ncode here\n\\`\\`\\`"

    def __init__(self, argument):
        try:
            block, code = argument.split("\n", 1)
        except ValueError:
            raise commands.BadArgument(self.missing_error)

        if not block.startswith("```") and not code.endswith("```"):
            raise commands.BadArgument(self.missing_error)

        self.source = code.rstrip("`")


class CodeSection:
    missing_error = "Missing code section. Please use the following markdown\n\\`code here\\`\nor\n\\`\\`\\`rust\ncode here\n\\`\\`\\`"

    def __init__(self, code):
        codeblock = code.startswith("```") and code.endswith("```")
        codesection = code.startswith("`") and code.endswith("`")
        if not codesection and not codeblock:
            raise commands.BadArgument(self.missing_error)

        if codeblock:
            self.source = "\n".join(code.split("\n")[1:]).rstrip("`")
        else:
            self.source = code.strip("`")


class Playground(commands.Cog):
    """Evaluates Rust code with an optional compilation mode.
    Defaults to debug.

    Usage:

    ?play (--release|--debug) ```rs
    <your Rust code here>
    ```

    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.session = aiohttp.ClientSession(loop=self.bot.loop)
        self.sent_evals = {}

    def cog_unload(self):
        self.bot.loop.create_task(self.session.close())

    @commands.command()
    async def play(self, ctx: commands.Context, *, arg):
        """Evaluates Rust code. Exactly equal to https://play.rust-lang.org/"""
        (mode, code) = self.parse_args(arg)
        await self.send_playground(ctx, mode, code.source)

    @commands.command()
    async def playwarn(self, ctx: commands.Context, *, arg):
        """Evaluates Rust code and outputs generated warnings. Exactly equal to https://play.rust-lang.org/"""
        (mode, code) = self.parse_args(arg)
        await self.send_playground(ctx, mode, code.source, warnings=True)

    @commands.command()
    async def eval(self, ctx: commands.Context, *, arg):
        """Evaluates Rust code and debug prints the results. Exactly equal to https://play.rust-lang.org/"""
        (mode, code) = self.parse_args(arg)
        comment_index = code.source.find("//")
        end_idx = comment_index if comment_index != -1 else len(code.source)
        await self.send_playground(
            ctx, mode, 'fn main(){println!("{:?}",{' + code.source[:end_idx] + "});}"
        )

    @commands.command()
    async def go(self, ctx: commands.Context):
        """Evaluates Go code"""
        await ctx.send("No")

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        sent_eval_id = self.sent_evals.get(before.id, None)
        if sent_eval_id is not None:
            ctx: commands.Context = await self.bot.get_context(after)
            if not ctx.valid:
                return

            try:
                sent_eval = await ctx.fetch_message(sent_eval_id)

                await ctx.command.prepare(ctx)

                # 'arg' depends on the name of the argument in the commands above; they must all at least be the same,
                # and if they change, this must be changed too. Messy, but arguments are only provided as a dict.
                (mode, code) = self.parse_args(ctx.kwargs['arg'])

                warnings = False
                if ctx.command.name == "eval":
                    comment_index = code.source.find("//")
                    end_idx = comment_index if comment_index != -1 else len(code.source)
                    code.source = 'fn main(){println!("{:?}",{' + code.source[:end_idx] + "});}"
                elif ctx.command.name == "playwarn":
                    warnings = True
                elif ctx.command.name != "play":
                    return

                await self.edit_playground(ctx, sent_eval, mode, code.source, warnings)
            except (
                    discord.HTTPException, discord.Forbidden, commands.MissingRequiredArgument, commands.CommandError
            ) as e:
                await self.cog_command_error(ctx, e)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        self.sent_evals.pop(message.id, None)

    def parse_args(self, args):
        args = args.replace("\n`", " `").split(" ")
        if args[0].startswith("--"):
            mode = args[0][2:]
            mode.strip()
            code = " ".join(args[1:])
            if mode != "release" and mode != "debug":
                raise commands.BadArgument(
                    "Bad compile mode. Valid options are `--release` and `--debug`"
                )

            return mode, CodeSection(code)
        else:
            code = " ".join(args[0:])
            return None, CodeSection(code)

    async def edit_playground(self, ctx: commands.Context, sent_message, mode, code, warnings: bool = False):
        async with ctx.typing():
            await sent_message.edit(content=await self.query_playground(mode, code, warnings))

    async def send_playground(self, ctx: commands.Context, mode, code, warnings: bool = False):
        async with ctx.typing():
            sent_message = await ctx.send(await self.query_playground(mode, code, warnings))

        self.sent_evals[ctx.message.id] = sent_message.id

    async def query_playground(
            self, mode, code, warnings: bool = False
    ):
        payload = json.dumps(
            {
                "channel": "nightly",
                "edition": "2018",
                "code": code,
                "crateType": "bin",
                "mode": mode if mode is not None else "debug",
                "tests": False,
            }
        )

        async with self.session.post(
                "https://play.rust-lang.org/execute", data=payload
        ) as r:
            if r.status != 200:
                raise commands.CommandError(
                    "Rust Playground didn't respond in time. :("
                )

            response = await r.json()
            if "error" in response:
                raise commands.CommandError(response["error"])

            stderr = response["stderr"]
            stdout = response["stdout"]

            full_response = (
                stdout
                if err_regex.search(stderr) is None
                   and not (warnings and len(stderr) >= 4)
                   and "panicked" not in stderr
                else "\n".join(stderr.split("\n")[1:]) + "\n\n" + stdout
            )
            len_response = len(full_response)
            if len_response == 0:
                msg = "``` ```"
            elif len_response < 1990:
                full_response = full_response.replace("```", "  ̀  ̀  ̀")
                msg = f"```rs\n{full_response}```"
            else:
                msg = await self.get_playground_link(code)

            return msg

    async def get_playground_link(self, code):
        headers = {
            "Content-Type": "application/json",
            "Referer": "https://discord.gg/aVESxV8",
        }

        data = json.dumps({"code": code})

        async with self.session.post(
                "https://play.rust-lang.org/meta/gist/", data=data, headers=headers
        ) as r:
            response = await r.json()

        return "https://play.rust-lang.org/?version=nightly&mode=debug&edition=2018&gist=" + response["id"]

    async def cog_command_error(self, ctx: commands.Context, error):
        log.error("Playground error: %s", error)
        if isinstance(error, (discord.HTTPException, discord.Forbidden)):
            await ctx.send("Error while sending the output.")
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(CodeBlock.missing_error)
        if isinstance(error, commands.CommandError):
            await ctx.send(str(error))


def setup(bot):
    bot.add_cog(Playground(bot))
