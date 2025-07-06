class Paginator:
    def __init__(self, ctx, pages):
        self.ctx = ctx
        self.pages = pages
        self.current = 0
        self.message = None

    async def start(self):
        self.message = await self.ctx.send(embed=self.pages[self.current])
        await self.message.add_reaction('⬅️')
        await self.message.add_reaction('➡️')

        def check(reaction, user):
            return (
                user == self.ctx.author and
                str(reaction.emoji) in ['⬅️', '➡️'] and
                reaction.message.id == self.message.id
            )

        while True:
            try:
                reaction, user = await self.ctx.bot.wait_for('reaction_add', timeout=60.0, check=check)

                if str(reaction.emoji) == '⬅️':
                    self.current = (self.current - 1) % len(self.pages)
                elif str(reaction.emoji) == '➡️':
                    self.current = (self.current + 1) % len(self.pages)

                await self.message.edit(embed=self.pages[self.current])
                await self.message.remove_reaction(reaction, user)

            except Exception:
                # 60秒無反應後清除反應結束分頁
                try:
                    await self.message.clear_reactions()
                except:
                    pass
                break
