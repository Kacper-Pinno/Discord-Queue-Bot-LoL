import discord
from discord import app_commands
from discord.ext import commands
import random

# Riot API Imports
from riot_api import get_account_by_riot_id, get_summoner_icon
from config import VERIFY_ICON_PATHS, VERIFIED_ROLE_ID

class VerificationModal(discord.ui.Modal, title="X9 Esports Registration"):
    summoner_name = discord.ui.TextInput(label="LoL Name", placeholder="e.g. Faker", required=True)
    tag = discord.ui.TextInput(label="LoL # (hashtag)", placeholder="e.g. #EUW", required=True)
    discord_username = discord.ui.TextInput(label="Your Discord Name", placeholder="Name you want to be called", required=True)

    def __init__(self):
        super().__init__()
        self.server = None
        self.puuid = None
        self.icon_to_set = None  # Store which icon user must set

    async def send_icon_instruction(self, interaction, icon_id_to_set):
        path = VERIFY_ICON_PATHS.get(icon_id_to_set)
        if path:
            await interaction.followup.send(
                f"Please set your League of Legends icon to this one:",
                file=discord.File(path),
                ephemeral=True
            )
        else:
            await interaction.followup.send(
                "Sorry, I couldn't find the icon image to show you.",
                ephemeral=True
            )

    async def on_submit(self, interaction: discord.Interaction):
        name = self.summoner_name.value.strip()
        tag = self.tag.value.strip().replace("#", "")
        discord_name = self.discord_username.value.strip()
        server = self.server or "euw1"

        await interaction.response.send_message(
            f"Searching for **{name}#{tag}** on **{server.upper()}** server...",
            ephemeral=True
        )

        # Call your Riot API function to get account info
        account_data = get_account_by_riot_id(name, tag)
        if not account_data:
            await interaction.followup.send("❌ Could not find this LoL account. Please check your name , tag or server.", ephemeral=True)
            return

        self.puuid = account_data.get("puuid")
        if not self.puuid:
            await interaction.followup.send("❌ Could not retrieve your PUUID. Please try again later.", ephemeral=True)
            return

        # Get user's current icon id
        icon_id = get_summoner_icon(self.puuid, server)
        if icon_id is None:
            await interaction.followup.send("❌ Could not retrieve your profile icon. Please try again later.", ephemeral=True)
            return

        # Check icon and decide which icon user needs to set
        if icon_id not in [9, 23]:
            self.icon_to_set = random.choice([9, 23])
            await interaction.followup.send(
                f"❗Account found! \n"
                "Please follow next steps.",
                ephemeral=True
            )
            await self.send_icon_instruction(interaction, self.icon_to_set)
        elif icon_id == 9:
            self.icon_to_set = 23
            await interaction.followup.send(
                f"❗Account found!",
                ephemeral=True
            )
            await self.send_icon_instruction(interaction, 23)
        elif icon_id == 23:
            self.icon_to_set = 9
            await interaction.followup.send(
                f"❗Account found!",
                ephemeral=True
            )
            await self.send_icon_instruction(interaction, 9)

        # Button to verify after user sets the icon
        await interaction.followup.send(
            "When you have changed your icon, click the button below to verify.",
            view=VerifyIconView(self),
            ephemeral=True
        )


class VerifyIconView(discord.ui.View):
    def __init__(self, modal: VerificationModal):
        super().__init__(timeout=300)
        self.modal = modal

    @discord.ui.button(label="Verify Icon", style=discord.ButtonStyle.primary)
    async def verify(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Check icon again
        icon_id = get_summoner_icon(self.modal.puuid, self.modal.server or "euw1")
        if icon_id == self.modal.icon_to_set:
            # Assign role
            guild = interaction.guild
            member = interaction.user
            role = guild.get_role(VERIFIED_ROLE_ID)
            if role:
                await member.add_roles(role)
                await interaction.response.send_message("✅ Verification successful! You have been given the verified role.", ephemeral=True)
            else:
                await interaction.response.send_message("❌ Verified role not found on this server.", ephemeral=True)
            self.stop()
        else:
            await interaction.response.send_message(
                f"""❌ Your icon is still not set to the required one. Please change it and try again.\n
                Make sure you've closed the window in which you've changed your icon.
                """,
                ephemeral=True
            )


class RegionSelect(discord.ui.Select):
    def __init__(self, modal: VerificationModal):
        self.modal = modal
        options = [
            discord.SelectOption(label="EUW", value="euw1", description="Europe West"),
            discord.SelectOption(label="EUNE", value="eun1", description="Europe Nordic & East"),
        ]
        super().__init__(placeholder="Select your server", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        self.modal.server = self.values[0]
        await interaction.response.send_modal(self.modal)


class RegionView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)
        self.modal = VerificationModal()
        self.add_item(RegionSelect(self.modal))


class AcceptRulesView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)

    @discord.ui.button(label="✅ Accept", style=discord.ButtonStyle.success)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Select your server:", view=RegionView(), ephemeral=True)


class StartVerificationView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)

    @discord.ui.button(label="Start Verification", style=discord.ButtonStyle.primary)
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="**Rules & Regulations**",
            description="""**You must agree to the rules to verify your League of Legends account**\n
            **1.** Trolling/Griefing/Afking is sctrictly forbidden.
            **2.** Cheating will result with permanent ban.
            **3.** Extream toxicity / hate speech is forbidden.
            **4.** Each team is allowed to pause the game when needed - (except during team-fights).
            **5.** False player reports will be punished.
            **6.** Leaving matches will be punished.
            **7.** General misconduct will be punished.
            **8.** Using alt-accounts is strictly forbidden.
            **9.** Win-trading will be punished.
            **10.** Trying to avoid the rules will result with a punishment.
            **11.** Players are meant to stay in voice-channel until the end of the match.
            """,
            color=discord.Color.orange()
        )
        await interaction.response.send_message(embed=embed, view=AcceptRulesView(), ephemeral=True)


class Verification(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="setup_verification", description="Create the verification panel.")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_verification(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🎮 League of Legends Verification",
            description="Click below to start verifying your account and get access to the full server!",
            color=discord.Color.blurple()
        )
        await interaction.response.send_message(embed=embed, view=StartVerificationView())

async def setup(bot: commands.Bot):
    await bot.add_cog(Verification(bot))