import discord
from discord import app_commands
from discord.ext import commands
from views.helpers import EmbedView, EmbedPugView

class Queue(commands.Cog):
    group = app_commands.Group(name="queue",description="Related to pug queues")

    def __init__(self, bot) -> None:
        self.bot = bot
        self.adminCog = bot.get_cog("Admin")
        self.queueDict = {}

    def getmsg(self, channel: discord.TextChannel):
        if len(self.queueDict[channel.id]["players"]) == 0:
            return "\nNo one is in this channel\n"
        
        msg = "The following users are in the queue:\n"

        for x in range (0,len(self.queueDict[channel.id]["players"])):
            msg += (self.queueDict[channel.id]["players"][x]).mention
            if(x != len(self.queueDict[channel.id]["players"])-1):
                msg += "\n"

        msg += ("\n["+str(len(self.queueDict[channel.id]["players"]))+"/"+str(self.queueDict[channel.id]["max"])+"]")
        
        return msg

    async def editMessage(self, channel: discord.TextChannel):
        if channel.id in self.queueDict.keys():
            msg = await channel.fetch_message(self.queueDict[channel.id]["msg_id"])
            await msg.edit(view=EmbedPugView(myQueueName=self.queueDict[channel.id]["name"],myText=self.getmsg(channel),myQueue=self))


    # we ask the admin cog to verify admins for us
    def verifyAdmin(self, user: discord.User):
        return self.adminCog.verifyAdmin(user)
    

    # ADMIN ONLY COMMANDS

    # creates queue
    @group.command(name="create",description="ADMIN ONLY: Starts a queue if one does not exist in the current channel")
    async def startqueue(self, interaction: discord.Interaction, game: str, maxplayers: int):
        if not self.verifyAdmin(interaction.user): # admin check
            return await interaction.response.send_message(view=EmbedView(myText="This command is reserved for administrators"),ephemeral=True)

        cur_channel = interaction.channel
        if cur_channel.id in self.queueDict.keys(): # make sure the channel does not have queue
            return await interaction.response.send_message(view=EmbedView(myText="A queue already exists in this channel"),ephemeral=True)
        
        # add the queue to the dictionary
        self.queueDict[cur_channel.id] = {
            "name": game,
            "max": maxplayers,
            "players": [],
            "msg_id": None,
        }

        await interaction.response.send_message(view=EmbedView(myText="Game creation success!"),ephemeral=True)

        msg = await cur_channel.send(view=EmbedView(myText=f"Queue for {game}\n\n\n/queue join  ,  /queue leave"))
        self.queueDict[cur_channel.id]["msg_id"] = msg.id

    # stops queue
    @group.command(name="end",description="ADMIN ONLY: Ends the queue in the current channel if one exists")
    async def stopqueue(self, interaction: discord.Interaction):
        if not self.verifyAdmin(interaction.user):
            return await interaction.response.send_message(view=EmbedView(myText="This command is reserved for administrators"),ephemeral=True)

        cur_channel = interaction.channel
        if cur_channel.id not in self.queueDict.keys():
            return await interaction.response.send_message(view=EmbedView(myText="There is no queue in this channel"),ephemeral=True)

        try: # remove queue from dictionary and delete original queue message
            msg = await cur_channel.fetch_message(self.queueDict[cur_channel.id]["msg_id"])
            await msg.delete()
            del self.queueDict[cur_channel.id]
            await interaction.response.send_message(view=EmbedView(myText=f"The queue in this channel has ended"))
        except: 
            await interaction.response.send_message(view=EmbedView(myText="Error in removing queue from this channel"))
    
    # add a user to the queue if not full
    @group.command(name="add",description="ADMIN ONLY: Adds the specified User (not already in queue) to the current queue")
    async def add(self, interaction: discord.Interaction, user: discord.User):
        if not self.verifyAdmin(interaction.user):
            return await interaction.response.send_message(view=EmbedView(myText="This command is reserved for administrators"),ephemeral=True)

        cur_channel = interaction.channel
        if cur_channel.id not in self.queueDict.keys():
            return await interaction.response.send_message(view=EmbedView(myText="There is no queue in this channel"),ephemeral=True)

        if user in self.queueDict[cur_channel.id]["players"]: # make sure target is not already in queue
            return await interaction.response.send_message(view=EmbedView(myText="That user is already in the queue"),ephemeral=True)
        
        if len(self.queueDict[cur_channel.id]["players"]) == self.queueDict[cur_channel.id]["max"]:
            return await interaction.response.send_message(view=EmbedView(myText="The queue is already full"),ephemeral=True)
        
        self.queueDict[cur_channel.id]["players"].append(user)
        await interaction.response.send_message(view=EmbedView(myText="Successfully added player"),ephemeral=True)

        return await self.editMessage(cur_channel)
    
    # kick a user from the queue
    @group.command(name="kick",description="ADMIN ONLY: Kicks the specified User (in the queue) from the current queue")
    async def remove(self, interaction: discord.Interaction, user: discord.User):
        if not self.verifyAdmin(interaction.user):
            return await interaction.response.send_message(view=EmbedView(myText="This command is reserved for administrators"),ephemeral=True)

        cur_channel = interaction.channel
        if cur_channel.id not in self.queueDict.keys():
            return await interaction.response.send_message(view=EmbedView(myText="There is no queue in this channel"),ephemeral=True)
        
        if user not in self.queueDict[cur_channel.id]["players"]: # make sure target is actually in queue
            return await interaction.response.send_message(view=EmbedView(myText="That user is not in the queue"),ephemeral=True)
        
        self.queueDict[cur_channel.id]["players"].remove(user)
        await interaction.response.send_message(view=EmbedView(myText="Successfully kicked player"),ephemeral=True)

        return await self.editMessage(cur_channel)
    
    # TODO: start the game
    @group.command(name="start",description="ADMIN ONLY: Immediately starts the game")
    async def start(self, interaction: discord.Interaction):
        """
        1. Create a new VC channel somewhere in the server
        2. Send a DM to every user in the queue for this channel with a link to the VC
        """
        return
    

    # Below are commands which anyone can use

    # join the queue
    @group.command(name="join",description="Join the queue in the current channel")
    async def join(self, interaction: discord.Interaction):
        cur_channel = interaction.channel
        if cur_channel.id not in self.queueDict.keys():
            return await interaction.response.send_message(view=EmbedView(myText="There is no queue in this channel"),ephemeral=True)

        if interaction.user in self.queueDict[cur_channel.id]["players"]:
            return await interaction.response.send_message(view=EmbedView(myText="You are already in the queue"),ephemeral=True)
        
        if len(self.queueDict[cur_channel.id]["players"]) == self.queueDict[cur_channel.id]["max"]:
            return await interaction.response.send_message(view=EmbedView(myText="The queue is already full"),ephemeral=True)
        
        self.queueDict[cur_channel.id]["players"].append(interaction.user)
        await interaction.response.send_message(view=EmbedView(myText="You joined the queue!"),ephemeral=True)

        return await self.editMessage(cur_channel)
    
    # leave the queue
    @group.command(name="leave",description="Leave the queue in the current channel")
    async def remove(self, interaction: discord.Interaction):
        cur_channel = interaction.channel

        if cur_channel.id not in self.queueDict.keys():
            return await interaction.response.send_message(view=EmbedView(myText="There is no queue in this channel"),ephemeral=True)
        
        if interaction.user not in self.queueDict[cur_channel.id]["players"]: # make sure target is actually in queue
            return await interaction.response.send_message(view=EmbedView(myText="You are not in the queue"),ephemeral=True)
        
        self.queueDict[cur_channel.id]["players"].remove(interaction.user)
        await interaction.response.send_message(view=EmbedView(myText="You left the queue!"),ephemeral=True)

        return await self.editMessage(cur_channel)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Queue(bot))