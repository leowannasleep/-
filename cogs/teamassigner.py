import discord
from discord.ext import commands
import json

FILE_PATH = "data/registered_users.json"

# Load the registered users and language map
def load_registered():
    try:
        with open(FILE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return set(data["registered_users"]), data.get("lang", {})
    except:
        return set(), {}

def save_registered(registered_users, lang_map):
    # Save the updated registered users and their language map
    with open(FILE_PATH, "w", encoding="utf-8") as f:
        json.dump({"registered_users": list(registered_users), "lang": lang_map}, f)

# Get roles by name for the guild
def get_role_by_name(guild, role_name):
    return discord.utils.get(guild.roles, name=role_name)

# Assign roles based on user language
async def assign_roles(guild):
    # Load data from the registered users
    registered_users, lang_map = load_registered()

    zh_users = {user_id for user_id in registered_users if lang_map.get(str(user_id)) == 'zh'}
    en_users = {user_id for user_id in registered_users if lang_map.get(str(user_id)) == 'en'}
    both_users = {user_id for user_id in registered_users if lang_map.get(str(user_id)) == 'both'}

    # Calculate the distribution of users into 8 teams (A-H)
    team_roles = {
        'A': 'zh', 'B': 'zh', 'C': 'zh', 'D': 'zh', 'E': 'zh', 'F': 'zh',
        'G': 'en', 'H': 'en'
    }

    # Assign zh users to teams A-F
    zh_team_count = 6  # A-F are for zh users
    zh_per_team = len(zh_users) // zh_team_count
    remaining_zh_users = len(zh_users) % zh_team_count

    # Assign en users to teams G-H
    en_team_count = 2  # G-H are for en users
    en_per_team = len(en_users) // en_team_count
    remaining_en_users = len(en_users) % en_team_count

    # Now we begin assigning roles
    teams = {team: [] for team in team_roles}

    # Assign zh users to A-F
    zh_users_list = list(zh_users)
    for i, team in enumerate(list(teams.keys())[:6]):  # Teams A-F
        user_count = zh_per_team + (1 if i < remaining_zh_users else 0)
        teams[team].extend(zh_users_list[:user_count])
        zh_users_list = zh_users_list[user_count:]

    # Assign en users to G-H
    en_users_list = list(en_users)
    for i, team in enumerate(list(teams.keys())[6:]):  # Teams G-H
        user_count = en_per_team + (1 if i < remaining_en_users else 0)
        teams[team].extend(en_users_list[:user_count])
        en_users_list = en_users_list[user_count:]

    # Now assign both users to the teams, priority given to en teams (G and H)
    both_users_list = list(both_users)

    # Assign to en teams (G, H) first
    for i, team in enumerate(list(teams.keys())[6:]):  # Teams G-H
        if both_users_list:
            teams[team].append(both_users_list.pop(0))

    # Then assign to zh teams (A-F)
    for i, team in enumerate(list(teams.keys())[:6]):  # Teams A-F
        if both_users_list:
            teams[team].append(both_users_list.pop(0))

    # Assign roles to members in each team and print the count of assigned users
    for team, members in teams.items():
        team_role = get_role_by_name(guild, team)  # Get the role object from the guild
        if team_role:
            print(f"Assigned {len(members)} members to Team {team}")  # Print count of users assigned to this role

        # Loop through each member and assign the role
        for user_id in members:
            member = discord.utils.get(guild.members, id=user_id)
            if member and team_role:
                await member.add_roles(team_role)

    return teams

class TeamAssigner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def assign_teams(self, ctx):
        # Assign roles to all registered users based on their language selection
        guild = ctx.guild
        await assign_roles(guild)
        await ctx.send("Roles have been successfully assigned to users based on their language selection.")

    @commands.command()
    async def display_roles(self, ctx):
        """Show total registered users and breakdown by language."""
        guild = ctx.guild
        registered_users, lang_map = load_registered()

        total = len(registered_users)
        zh_count = sum(1 for uid in registered_users if lang_map.get(str(uid)) == "zh")
        en_count = sum(1 for uid in registered_users if lang_map.get(str(uid)) == "en")
        both_count = sum(1 for uid in registered_users if lang_map.get(str(uid)) == "both")

        embed = discord.Embed(
            title="Registration Summary",
            color=discord.Color.blue()
        )
        embed.add_field(name="Total Users", value=str(total), inline=False)
        embed.add_field(name="ZH Users",    value=str(zh_count), inline=True)
        embed.add_field(name="EN Users",    value=str(en_count), inline=True)
        embed.add_field(name="Both Users",  value=str(both_count), inline=True)

        await ctx.send(embed=embed)

# Add the cog to the bot
async def setup(bot: commands.Bot):
    await bot.add_cog(TeamAssigner(bot))