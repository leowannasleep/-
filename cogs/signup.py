import discord
import json
import os
from datetime import datetime, timedelta, time, timezone
from discord.ext import commands

#define
FILE_PATH = "data/registered_users.json"
TIME_FILE = "data/game_start.json"
LANG_ZH   = "zh"
LANG_EN   = "en"
LANG_BOTH = "both"
timezone_type = timezone(timedelta(hours=8), name="CST") #change timedelta and name if needed to adjust to your timezone
TEAM_NAMES = ["A", "B", "C", "D", "E", "F", "G", "H"] # change this to exact same role name!!
# Ensure the 'data' directory exists
os.makedirs(os.path.dirname(FILE_PATH), exist_ok=True)
# --------------------------------
def load_registered():
    try:
        with open(FILE_PATH, "r") as f:
            data = json.load(f)
            return set(data.get("registered_users", [])), data.get("lang", {})
    except (FileNotFoundError, json.JSONDecodeError):
        return set(), {}

def save_registered(registered_users, lang_map):
    os.makedirs(os.path.dirname(FILE_PATH), exist_ok=True)
    with open(FILE_PATH, "w") as f:
        json.dump({
            "registered_users": list(registered_users),
            "lang": lang_map
        }, f, indent=2)

def clear_registered():
    os.makedirs(os.path.dirname(FILE_PATH), exist_ok=True)
    with open(FILE_PATH, "w") as f:
        json.dump({"registered_users": [], "lang": {}}, f, indent=2)

# -------------------------------------
def set_game_start_time():
    os.makedirs(os.path.dirname(TIME_FILE), exist_ok=True)

    now = datetime.now(timezone_type) 
    
    future_date = now.date() + timedelta(days=2) # change timedelta if needed more time
    # Set deadline at 21:00 (9 PM)
    deadline = datetime.combine(future_date, time(hour=21, tzinfo=timezone_type)) # change time(hour = int) can set when the time of the deadline


    with open(TIME_FILE, "w") as f:
        json.dump({
            "start_time": now.isoformat(),
            "deadline": deadline.isoformat()
        }, f)

def get_registration_deadline():
    try:
        with open(TIME_FILE, "r") as f:
            data = json.load(f)
            return datetime.fromisoformat(data["deadline"])
    except (FileNotFoundError, KeyError, ValueError):
        return None
# -------------------------
async def remove_all_team_roles(guild: discord.Guild) -> dict[str, int]:
    """
    Remove team roles from every user in registered_users.json.
    """
    registered_users, lang_map = load_registered()
    removals: dict[str, int] = {team: 0 for team in TEAM_NAMES}

    # If registered_users is a dictionary, get the keys (user IDs)
    if isinstance(registered_users, dict):
        registered_users = registered_users.keys()

    for team in TEAM_NAMES:
        role = discord.utils.get(guild.roles, name=team)
        if not role:
            continue

        for user_id in registered_users:
            try:
                # Attempt to fetch the member from the guild
                member = await guild.fetch_member(int(user_id))  # Make sure the user_id is an integer
                if member and role in member.roles:
                    await member.remove_roles(role, reason="Bulk role cleanup")
                    removals[team] += 1
            except discord.NotFound:
                # Member not found in the guild
                print(f"Member with ID {user_id} not found in the guild.")
            except discord.HTTPException as e:
                # Handle HTTP errors
                print(f"HTTP error occurred while trying to fetch member {user_id}: {e}")

    return removals

    
# Commands
class SignUp(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="signupcogtest", help="Check if SignUp cog is loaded.")
    async def signupcogtest(self, ctx: commands.Context):
        await ctx.send(f"SignUp loaded")

    @commands.command(name="gamestart", help="Start new game and reset all data (confirmation needed).")
    @commands.has_role("Admin")
    async def gamestart(self, ctx: commands.Context):
        view = GameStart(author=ctx.author)
        await ctx.message.delete()  
        await ctx.send("Start a new game?", view=view)

# 1st confirmation
class GameStart(discord.ui.View):
    def __init__(self, author: discord.User):
        super().__init__(timeout=60)
        self.author = author

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("This button isn't for you.", ephemeral=True)
            return False
        return True    

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.message.delete()
        sec_confirm = ConfirmAgain(author=self.author)
        await interaction.channel.send("Confirm again to proceed...", view = sec_confirm)
        
        

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Cancel...", ephemeral=True)
        await interaction.message.delete()
   
# 2nd confirmation
class ConfirmAgain(discord.ui.View):
    def __init__(self, author: discord.User):
        super().__init__(timeout=30)
        self.author = author

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("This button isn't for you.", ephemeral=True)
            return False
        return True 
    
    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild 
        await interaction.response.send_message("A new game will begin. Reset all user data...", ephemeral=True)
        await interaction.message.delete()
        os.makedirs(os.path.dirname(FILE_PATH), exist_ok=True)
        set_game_start_time()
        deadline = get_registration_deadline()
        unix_ts = int(deadline.timestamp())
        counts = await remove_all_team_roles(guild)
        print("Removed roles:", counts)
        clear_registered()
        register = Register()
        await interaction.channel.send(f"請於這裏按下按鈕註冊 \n Please press button to register.\n 註冊截止時間 | Registration deadline : <t:{unix_ts}:F>", view = register)


    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Cancel...", ephemeral=True)
        await interaction.message.delete()


# Register
class Register(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="註冊 | Register",
        style=discord.ButtonStyle.primary,
        custom_id="register_once"
    )
    async def register(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        deadline = get_registration_deadline()
        now = datetime.now(timezone_type)

        if deadline and now > deadline:
            await interaction.response.send_message(
                "註冊時間已結束！\nRegistration period is over!",
                ephemeral=True
            )

            return
        
        registered_users, lang_map = load_registered()
        uid = interaction.user.id
        
        if uid in registered_users and str(uid) in lang_map:
            await interaction.response.send_message(
                "你已經註冊並選擇語言了！\nYou are already registered and have chosen a language!",
                ephemeral=True
            )
            return

        # add user to registered set, save, then show language picker
        registered_users.add(interaction.user.id)
        save_registered(registered_users, lang_map)

        await interaction.response.send_message(
            "# 請選擇語言 | Please select language\n"
            "選擇 **[兩者都可]** 將會隨機進入中文或英文頻道\n"
            "Select **[Both]** will enter the Chinese or English channel randomly.\n"
            "\n**此選擇無法更改請謹慎選擇 | This selection cannot be changed; choose carefully.**",
            view=Language(),
            ephemeral=True
        )

# Language to assign team
class Language(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.user_chosen = set()

    async def _finalize(self, interaction: discord.Interaction, lang_code: str, msg: str):
        # load -> update map -> save
        registered_users, lang_map = load_registered()
        lang_map[str(interaction.user.id)] = lang_code
        save_registered(registered_users, lang_map)

        await interaction.response.send_message(msg, ephemeral=True)
        await interaction.message.delete()   

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id in self.user_chosen:
            await interaction.response.send_message("您已經選擇了一種語言！ | You already selected a language!", ephemeral=True)
            return False
        self.user_chosen.add(interaction.user.id)
        return True

    @discord.ui.button(label="中文", style=discord.ButtonStyle.success)
    async def zh(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._finalize(interaction, LANG_ZH, "已註冊!!")

    @discord.ui.button(label="英文", style=discord.ButtonStyle.primary)
    async def en(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._finalize(interaction, LANG_EN, "REGISTERED!!")

    @discord.ui.button(label="兩者都可 | Both", style=discord.ButtonStyle.secondary)
    async def both(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._finalize(interaction, LANG_BOTH, "已註冊!! | REGISTERED!!")
    



async def setup(bot: commands.Bot):
    await bot.add_cog(SignUp(bot))
        