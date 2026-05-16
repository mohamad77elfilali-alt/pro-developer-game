"""
Multiplayer Lobby Manager - Dynamic Party & Competitive Gaming Hub
Production-Ready | Button-Based Lobby Configuration | 10 Multiplayer Games
"""

import asyncio
import logging
import random
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime, timedelta

import discord
from discord import app_commands
from discord.ext import commands, tasks

logger = logging.getLogger("MultiplayerHub")

# Neon color scheme
NEON_PURPLE = 0x9D00FF
NEON_CYAN = 0x00F0FF
NEON_MAGENTA = 0xFF00FF
NEON_GREEN = 0x39FF14
NEON_ORANGE = 0xFF6600

# ============================================================================
# MULTIPLAYER GAME DATA & STATE MANAGEMENT
# ============================================================================

class LobbySession:
    """Represents an active multiplayer lobby"""
    
    def __init__(self, channel_id: int, host_id: int, guild_id: int):
        self.channel_id = channel_id
        self.host_id = host_id
        self.guild_id = guild_id
        self.max_players = 4
        self.is_private = False
        self.invited_users: Set[int] = set()
        self.players: List[int] = [host_id]
        self.current_game: Optional[str] = None
        self.game_state: Dict = {}
        self.created_at = datetime.now()
    
    def add_player(self, user_id: int) -> bool:
        """Add a player to the lobby"""
        if len(self.players) >= self.max_players:
            return False
        if user_id not in self.players:
            self.players.append(user_id)
            return True
        return False
    
    def remove_player(self, user_id: int) -> None:
        """Remove a player from the lobby"""
        if user_id in self.players:
            self.players.remove(user_id)
    
    def is_full(self) -> bool:
        """Check if lobby is full"""
        return len(self.players) >= self.max_players
    
    def can_join(self, user_id: int) -> bool:
        """Check if user can join the lobby"""
        if self.is_full() and user_id != self.host_id:
            return False
        if self.is_private and user_id not in self.invited_users and user_id != self.host_id:
            return False
        return True

# Global lobby tracking
ACTIVE_LOBBIES: Dict[int, LobbySession] = {}

# ============================================================================
# MULTIPLAYER GAME FUNCTIONS
# ============================================================================

async def play_truth_or_dare() -> Tuple[str, str]:
    """💭 Truth or Dare Game"""
    truths = [
        "What's your biggest fear?",
        "What's the most embarrassing thing you've ever done?",
        "Who do you have a crush on?",
        "What's your guilty pleasure?",
        "Have you ever lied to your best friend?",
    ]
    
    dares = [
        "Send a funny selfie to the group",
        "Talk in an accent for the next 5 minutes",
        "Do 10 pushups right now",
        "Send an embarrassing screenshot",
        "Do a funny dance and record it",
    ]
    
    choice = random.choice(["truth", "dare"])
    if choice == "truth":
        return "💭 TRUTH", random.choice(truths)
    else:
        return "🔥 DARE", random.choice(dares)

async def play_would_you_rather() -> Tuple[str, str]:
    """🤔 Would You Rather Game"""
    questions = [
        ("Fly or be invisible?", "Fly", "Invisible"),
        ("Time travel to past or future?", "Past", "Future"),
        ("Be rich or famous?", "Rich", "Famous"),
        ("Live in mountains or beach?", "Mountains", "Beach"),
        ("Have super strength or super speed?", "Strength", "Speed"),
        ("Talk to animals or speak all languages?", "Animals", "Languages"),
        ("Teleport or time travel?", "Teleport", "Time Travel"),
        ("Always be too hot or too cold?", "Too Hot", "Too Cold"),
        ("Win the lottery or find true love?", "Lottery", "True Love"),
        ("Rewind time or see the future?", "Rewind", "See Future"),
    ]
    
    question, option1, option2 = random.choice(questions)
    return question, f"{option1} or {option2}"

async def play_fast_finger_quiz() -> Tuple[str, str]:
    """🏃 Fast Finger Quiz"""
    questions = [
        ("How many continents?", "7"),
        ("Capital of Japan?", "Tokyo"),
        ("Largest planet?", "Jupiter"),
        ("Chemical symbol for gold?", "Au"),
        ("How many sides in a hexagon?", "6"),
        ("Fastest land animal?", "Cheetah"),
        ("Smallest prime number?", "2"),
        ("How many strings on a violin?", "4"),
    ]
    
    question, answer = random.choice(questions)
    return question, answer

async def play_word_wars() -> Tuple[str, str]:
    """🔤 Word Wars (Rhyme Challenge)"""
    words = [
        ("BLUE", "clue"),
        ("GAME", "fame"),
        ("DANCE", "chance"),
        ("LIGHT", "night"),
        ("SOUND", "ground"),
    ]
    
    word, hint = random.choice(words)
    return f"Find a word that rhymes with {word}", hint

async def play_king_of_the_hill() -> str:
    """👑 King of the Hill - Last Player Standing"""
    return "👑 **KING OF THE HILL**\n\nLast person standing wins! Players get eliminated one by one."

async def play_quick_draw_voting() -> Tuple[str, str]:
    """🎨 Quick Draw Voting"""
    drawing_prompts = [
        "A dragon",
        "A pizza",
        "A spaceship",
        "A unicorn",
        "A haunted house",
    ]
    
    prompt = random.choice(drawing_prompts)
    return prompt, "Draw this and others vote on the best!"

async def play_emoji_story() -> str:
    """🎭 Emoji Story - Build a story together"""
    return "🎭 **EMOJI STORY**\n\nEach player sends one emoji to build a story. Funniest story wins!"

async def play_trivia_deathmatch() -> Tuple[str, str, List[str]]:
    """🧠 Trivia Deathmatch - Competitive trivia"""
    questions = [
        {
            "q": "What's the capital of France?",
            "a": "Paris",
            "opts": ["London", "Berlin", "Paris", "Madrid"]
        },
        {
            "q": "Which planet is closest to the sun?",
            "a": "Mercury",
            "opts": ["Venus", "Mercury", "Earth", "Mars"]
        },
        {
            "q": "What is the largest ocean?",
            "a": "Pacific",
            "opts": ["Atlantic", "Indian", "Arctic", "Pacific"]
        },
        {
            "q": "Who wrote 1984?",
            "a": "Orwell",
            "opts": ["Orwell", "Asimov", "Bradbury", "Clarke"]
        },
        {
            "q": "What is the smallest country?",
            "a": "Vatican City",
            "opts": ["Monaco", "Vatican City", "Malta", "Cyprus"]
        },
    ]
    
    q = random.choice(questions)
    return q["q"], q["a"], q["opts"]

async def play_rapid_fire_riddles() -> List[Tuple[str, str]]:
    """⚡ Rapid Fire Riddles"""
    riddles = [
        ("What can run but never walks?", "Water"),
        ("I have a face but no eyes. What am I?", "Clock"),
        ("What has hands but cannot clap?", "Clock"),
        ("I am something people love or hate. What am I?", "Vegetables"),
    ]
    
    return random.sample(riddles, 3)

async def play_team_split_challenge() -> str:
    """⚔️ Team Split Challenge"""
    return "⚔️ **TEAM SPLIT CHALLENGE**\n\nPlayers split into teams. First team to reach 10 points wins!"

# ============================================================================
# BUTTON VIEWS FOR LOBBY CONFIGURATION
# ============================================================================

class MultiplayerLobbyView(discord.ui.View):
    """Main button view for creating multiplayer lobbies"""
    
    def __init__(self, bot: commands.Bot) -> None:
        super().__init__(timeout=None)
        self.bot = bot
    
    @discord.ui.button(label="⚔️ Host Matchmaking Lobby", style=discord.ButtonStyle.blurple, custom_id="create_multiplayer_lobby")
    async def create_lobby(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        """Create a new multiplayer lobby"""
        try:
            await interaction.response.defer(ephemeral=True)
            
            user_id = interaction.user.id
            guild = interaction.guild
            
            # Create private channel
            channel = await guild.create_text_channel(
                name=f"lobby-{user_id}",
                overwrites={
                    guild.default_role: discord.PermissionOverwrite(view=False),
                    interaction.user: discord.PermissionOverwrite(view=True),
                    self.bot.user: discord.PermissionOverwrite(send_messages=True, manage_messages=True),
                }
            )
            
            logger.info(f"✅ Created multiplayer lobby channel: {channel.name} for user {user_id}")
            
            # Create lobby session
            lobby = LobbySession(channel.id, user_id, guild.id)
            ACTIVE_LOBBIES[channel.id] = lobby
            
            # Store in database
            from main import DatabasePool
            async with DatabasePool.pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO game_channels (guild_id, channel_id, host_id, lobby_type, max_players, is_private)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    """,
                    guild.id,
                    channel.id,
                    user_id,
                    "multiplayer",
                    4,
                    False
                )
            
            # Send lobby configuration panel
            embed = discord.Embed(
                title="⚔️ MULTIPLAYER LOBBY CONFIGURATION",
                description=(
                    "**Configure your custom matchmaking lobby before going public!**\n\n"
                    "Use the buttons below to customize:\n"
                    "• Maximum player count\n"
                    "• Privacy settings (Public/Private)\n"
                    "• Invite specific friends\n\n"
                    "Once configured, click **LAUNCH LOBBY** to start!"
                ),
                color=NEON_CYAN
            )
            embed.set_footer(text="⚡ Elite Multiplayer Gaming Hub")
            
            view = LobbyConfigView(self.bot, channel.id, lobby)
            
            await channel.send(embed=embed, view=view)
            
            await interaction.followup.send(
                f"✅ **Multiplayer Lobby Created!**\n\n"
                f"📍 {channel.mention}\n\n"
                f"Configure your lobby and start playing!",
                ephemeral=True
            )
            
            logger.info(f"✅ Multiplayer lobby fully setup in {guild.name}")
            
        except Exception as e:
            logger.error(f"❌ Error creating lobby: {e}", exc_info=True)
            await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)


class LobbyConfigView(discord.ui.View):
    """View for configuring lobby settings"""
    
    def __init__(self, bot: commands.Bot, channel_id: int, lobby: LobbySession) -> None:
        super().__init__(timeout=None)
        self.bot = bot
        self.channel_id = channel_id
        self.lobby = lobby
    
    @discord.ui.button(label="👥 Max Players: 4", style=discord.ButtonStyle.primary, custom_id="set_player_limit")
    async def set_player_limit(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        """Configure maximum player limit"""
        await interaction.response.send_message(
            "👥 Select maximum player limit:",
            view=PlayerLimitView(self.bot, self.channel_id, self.lobby),
            ephemeral=True
        )
    
    @discord.ui.button(label="🔓 Privacy: Public", style=discord.ButtonStyle.green, custom_id="toggle_privacy")
    async def toggle_privacy(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        """Toggle privacy settings"""
        if self.lobby.is_private:
            self.lobby.is_private = False
            button.label = "🔓 Privacy: Public"
            button.style = discord.ButtonStyle.green
            status = "🔓 **PUBLIC** - Anyone can join this lobby!"
        else:
            self.lobby.is_private = True
            button.label = "🔒 Privacy: Private"
            button.style = discord.ButtonStyle.red
            status = "🔒 **PRIVATE** - Invite-only lobby"
        
        embed = discord.Embed(
            title="Privacy Setting Updated",
            description=status,
            color=NEON_GREEN if not self.lobby.is_private else NEON_ORANGE
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
        # Update database
        from main import DatabasePool
        async with DatabasePool.pool.acquire() as conn:
            await conn.execute(
                "UPDATE game_channels SET is_private = $1 WHERE channel_id = $2",
                self.lobby.is_private,
                self.channel_id
            )
    
    @discord.ui.button(label="➕ Invite Friends", style=discord.ButtonStyle.primary, custom_id="invite_friends")
    async def invite_friends(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        """Invite specific friends to the lobby"""
        await interaction.response.send_modal(InviteFriendsModal(self.bot, self.channel_id, self.lobby))
    
    @discord.ui.button(label="🚀 LAUNCH LOBBY", style=discord.ButtonStyle.success, custom_id="launch_lobby")
    async def launch_lobby(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        """Launch the configured lobby"""
        await interaction.response.defer(ephemeral=True)
        
        channel = self.bot.get_channel(self.channel_id)
        if not channel:
            await interaction.followup.send("❌ Channel not found", ephemeral=True)
            return
        
        # Send lobby info embed
        player_list = ", ".join([f"<@{pid}>" for pid in self.lobby.players])
        embed = discord.Embed(
            title="⚔️ MULTIPLAYER LOBBY LAUNCHED!",
            description=(
                f"**Players:** {len(self.lobby.players)}/{self.lobby.max_players}\n"
                f"{player_list}\n\n"
                f"**Privacy:** {'🔒 Private' if self.lobby.is_private else '🔓 Public'}\n\n"
                f"Select a game to begin!"
            ),
            color=NEON_PURPLE
        )
        
        # Send game selection panel
        game_view = MultiplayerGameSelectView(self.bot, self.channel_id, self.lobby)
        await channel.send(embed=embed, view=game_view)
        
        await interaction.followup.send(
            f"✅ Lobby launched! Check {channel.mention} for game selection.",
            ephemeral=True
        )
        
        logger.info(f"✅ Lobby {self.channel_id} launched with {len(self.lobby.players)} players")


class PlayerLimitView(discord.ui.View):
    """View for selecting player limit"""
    
    def __init__(self, bot: commands.Bot, channel_id: int, lobby: LobbySession) -> None:
        super().__init__(timeout=None)
        self.bot = bot
        self.channel_id = channel_id
        self.lobby = lobby
    
    @discord.ui.button(label="2 Players", style=discord.ButtonStyle.primary, custom_id="limit_2")
    async def limit_2(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        self.lobby.max_players = 2
        await interaction.response.send_message("✅ Max players set to **2**", ephemeral=True)
    
    @discord.ui.button(label="4 Players", style=discord.ButtonStyle.primary, custom_id="limit_4")
    async def limit_4(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        self.lobby.max_players = 4
        await interaction.response.send_message("✅ Max players set to **4**", ephemeral=True)
    
    @discord.ui.button(label="8 Players", style=discord.ButtonStyle.primary, custom_id="limit_8")
    async def limit_8(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        self.lobby.max_players = 8
        await interaction.response.send_message("✅ Max players set to **8**", ephemeral=True)
    
    @discord.ui.button(label="Unlimited", style=discord.ButtonStyle.primary, custom_id="limit_unlimited")
    async def limit_unlimited(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        self.lobby.max_players = 999
        await interaction.response.send_message("✅ Max players set to **Unlimited**", ephemeral=True)


class InviteFriendsModal(discord.ui.Modal, title="Invite Friends to Lobby"):
    """Modal for inviting friends"""
    
    friend_ids = discord.ui.TextInput(
        label="Friend Discord IDs (comma-separated)",
        placeholder="123456789,987654321,etc.",
        required=False
    )
    
    def __init__(self, bot: commands.Bot, channel_id: int, lobby: LobbySession) -> None:
        super().__init__()
        self.bot = bot
        self.channel_id = channel_id
        self.lobby = lobby
    
    async def on_submit(self, interaction: discord.Interaction) -> None:
        try:
            ids_str = self.friend_ids.value
            if ids_str:
                ids = [int(x.strip()) for x in ids_str.split(",")]
                self.lobby.invited_users.update(ids)
                
                # Update database
                from main import DatabasePool
                async with DatabasePool.pool.acquire() as conn:
                    await conn.execute(
                        "UPDATE game_channels SET invited_users = $1 WHERE channel_id = $2",
                        list(self.lobby.invited_users),
                        self.channel_id
                    )
                
                await interaction.response.send_message(
                    f"✅ **{len(ids)} friends invited!**\n\n"
                    f"They can now join this private lobby.",
                    ephemeral=True
                )
                logger.info(f"Invited {len(ids)} users to lobby {self.channel_id}")
            else:
                await interaction.response.send_message(
                    "❌ Please provide at least one friend ID",
                    ephemeral=True
                )
        except ValueError:
            await interaction.response.send_message(
                "❌ Invalid ID format! Please use comma-separated numeric IDs.",
                ephemeral=True
            )
        except Exception as e:
            logger.error(f"Error inviting friends: {e}")
            await interaction.response.send_message(
                f"❌ Error: {str(e)}",
                ephemeral=True
            )


class MultiplayerGameSelectView(discord.ui.View):
    """View for selecting multiplayer games"""
    
    def __init__(self, bot: commands.Bot, channel_id: int, lobby: LobbySession) -> None:
        super().__init__(timeout=None)
        self.bot = bot
        self.channel_id = channel_id
        self.lobby = lobby
    
    @discord.ui.button(label="💭 Truth or Dare", style=discord.ButtonStyle.green, custom_id="game_truth_or_dare")
    async def truth_or_dare(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        game_type, content = await play_truth_or_dare()
        embed = discord.Embed(
            title=game_type,
            description=content,
            color=NEON_PURPLE
        )
        await interaction.response.send_message(embed=embed)
        self.lobby.current_game = "truth_or_dare"
        logger.info(f"Started Truth or Dare in lobby {self.channel_id}")
    
    @discord.ui.button(label="🤔 Would You Rather", style=discord.ButtonStyle.green, custom_id="game_would_you_rather")
    async def would_you_rather(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        question, options = await play_would_you_rather()
        embed = discord.Embed(
            title="🤔 WOULD YOU RATHER",
            description=f"{question}\n\n**Options:** {options}",
            color=NEON_CYAN
        )
        await interaction.response.send_message(embed=embed, view=WouldYouRatherVoteView())
        self.lobby.current_game = "would_you_rather"
        logger.info(f"Started Would You Rather in lobby {self.channel_id}")
    
    @discord.ui.button(label="🏃 Fast Finger Quiz", style=discord.ButtonStyle.green, custom_id="game_fast_finger")
    async def fast_finger(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        question, answer = await play_fast_finger_quiz()
        embed = discord.Embed(
            title="🏃 FAST FINGER QUIZ",
            description=f"**Question:** {question}\n\n⏱️ Who can answer first?",
            color=NEON_GREEN
        )
        await interaction.response.send_message(embed=embed)
        self.lobby.current_game = "fast_finger"
        self.lobby.game_state = {"question": question, "answer": answer}
        logger.info(f"Started Fast Finger Quiz in lobby {self.channel_id}")
    
    @discord.ui.button(label="🔤 Word Wars", style=discord.ButtonStyle.green, custom_id="game_word_wars")
    async def word_wars(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        question, hint = await play_word_wars()
        embed = discord.Embed(
            title="🔤 WORD WARS",
            description=f"{question}\n\n**Hint:** {hint}",
            color=NEON_MAGENTA
        )
        await interaction.response.send_message(embed=embed)
        self.lobby.current_game = "word_wars"
        logger.info(f"Started Word Wars in lobby {self.channel_id}")
    
    @discord.ui.button(label="👑 King of the Hill", style=discord.ButtonStyle.green, custom_id="game_king_hill")
    async def king_of_hill(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        result = await play_king_of_the_hill()
        embed = discord.Embed(
            title="👑 KING OF THE HILL",
            description=result,
            color=NEON_ORANGE
        )
        embed.add_field(name="Players", value=", ".join([f"<@{p}>" for p in self.lobby.players]), inline=False)
        await interaction.response.send_message(embed=embed, view=KingOfHillView(self.lobby.players))
        self.lobby.current_game = "king_of_hill"
        logger.info(f"Started King of the Hill in lobby {self.channel_id}")
    
    @discord.ui.button(label="🎨 Quick Draw", style=discord.ButtonStyle.green, custom_id="game_quick_draw")
    async def quick_draw(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        prompt, instructions = await play_quick_draw_voting()
        embed = discord.Embed(
            title="🎨 QUICK DRAW VOTING",
            description=f"**Draw:** {prompt}\n\n{instructions}",
            color=NEON_CYAN
        )
        await interaction.response.send_message(embed=embed)
        self.lobby.current_game = "quick_draw"
        logger.info(f"Started Quick Draw in lobby {self.channel_id}")
    
    @discord.ui.button(label="🎭 Emoji Story", style=discord.ButtonStyle.green, custom_id="game_emoji_story")
    async def emoji_story(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        result = await play_emoji_story()
        embed = discord.Embed(
            title="🎭 EMOJI STORY",
            description=result,
            color=NEON_PURPLE
        )
        await interaction.response.send_message(embed=embed)
        self.lobby.current_game = "emoji_story"
        logger.info(f"Started Emoji Story in lobby {self.channel_id}")
    
    @discord.ui.button(label="🧠 Trivia Deathmatch", style=discord.ButtonStyle.green, custom_id="game_trivia_death")
    async def trivia_deathmatch(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        question, answer, options = await play_trivia_deathmatch()
        embed = discord.Embed(
            title="🧠 TRIVIA DEATHMATCH",
            description=f"**Question:** {question}",
            color=NEON_GREEN
        )
        embed.add_field(name="Players", value=", ".join([f"<@{p}>" for p in self.lobby.players]), inline=False)
        await interaction.response.send_message(embed=embed, view=TriviaDeathmatchView(options, answer))
        self.lobby.current_game = "trivia_deathmatch"
        logger.info(f"Started Trivia Deathmatch in lobby {self.channel_id}")
    
    @discord.ui.button(label="⚡ Rapid Riddles", style=discord.ButtonStyle.green, custom_id="game_rapid_riddles")
    async def rapid_riddles(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        riddles = await play_rapid_fire_riddles()
        riddle_text = "\n\n".join([f"**{i+1}.** {r[0]}\n*Answer: {r[1]}*" for i, r in enumerate(riddles)])
        embed = discord.Embed(
            title="⚡ RAPID FIRE RIDDLES",
            description=riddle_text,
            color=NEON_MAGENTA
        )
        await interaction.response.send_message(embed=embed)
        self.lobby.current_game = "rapid_riddles"
        logger.info(f"Started Rapid Riddles in lobby {self.channel_id}")


class WouldYouRatherVoteView(discord.ui.View):
    """View for Would You Rather voting"""
    
    def __init__(self) -> None:
        super().__init__(timeout=None)
        self.option1_votes = 0
        self.option2_votes = 0
    
    @discord.ui.button(label="Option 1", style=discord.ButtonStyle.primary, custom_id="wyr_option1")
    async def option1(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        self.option1_votes += 1
        await interaction.response.send_message(
            f"✅ Voted for Option 1!\n\n📊 Current votes: Option 1 ({self.option1_votes}) vs Option 2 ({self.option2_votes})",
            ephemeral=True
        )
    
    @discord.ui.button(label="Option 2", style=discord.ButtonStyle.primary, custom_id="wyr_option2")
    async def option2(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        self.option2_votes += 1
        await interaction.response.send_message(
            f"✅ Voted for Option 2!\n\n📊 Current votes: Option 1 ({self.option1_votes}) vs Option 2 ({self.option2_votes})",
            ephemeral=True
        )


class KingOfHillView(discord.ui.View):
    """View for King of the Hill game"""
    
    def __init__(self, players: List[int]) -> None:
        super().__init__(timeout=None)
        self.players = players.copy()
        self.current_king = players[0] if players else None
    
    @discord.ui.button(label="⚔️ Challenge", style=discord.ButtonStyle.danger, custom_id="challenge_king")
    async def challenge(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if interaction.user.id == self.current_king:
            await interaction.response.send_message("❌ You can't challenge yourself!", ephemeral=True)
            return
        
        challenger_wins = random.choice([True, False])
        if challenger_wins:
            old_king = self.current_king
            self.current_king = interaction.user.id
            embed = discord.Embed(
                title="⚔️ CHALLENGE WON!",
                description=f"<@{interaction.user.id}> is the new **KING OF THE HILL**!\n\n"
                           f"Dethroned: <@{old_king}>",
                color=NEON_GREEN
            )
        else:
            embed = discord.Embed(
                title="❌ CHALLENGE FAILED!",
                description=f"<@{self.current_king}> defended the hill!",
                color=NEON_ORANGE
            )
        
        await interaction.response.send_message(embed=embed)


class TriviaDeathmatchView(discord.ui.View):
    """View for Trivia Deathmatch game"""
    
    def __init__(self, options: List[str], correct_answer: str) -> None:
        super().__init__(timeout=None)
        self.options = options
        self.correct_answer = correct_answer
        
        for option in options:
            self.add_item(TriviaDeathmatchButton(option, correct_answer))


class TriviaDeathmatchButton(discord.ui.Button):
    def __init__(self, option: str, correct_answer: str):
        super().__init__(label=option, style=discord.ButtonStyle.primary, custom_id=f"trivia_death_{option}")
        self.option = option
        self.correct_answer = correct_answer
    
    async def callback(self, interaction: discord.Interaction) -> None:
        if self.option == self.correct_answer:
            await interaction.response.send_message(
                f"✅ **<@{interaction.user.id}> WINS! CORRECT!**",
                ephemeral=False
            )
        else:
            await interaction.response.send_message(
                f"❌ Wrong! The answer was **{self.correct_answer}**",
                ephemeral=True
            )

# ============================================================================
# AUTO-CLEANUP FOR LOBBIES
# ============================================================================

async def auto_cleanup_lobby(bot: commands.Bot, channel_id: int, lobby_id: str, timeout_seconds: int = 1800) -> None:
    """Automatically delete lobby after inactivity timeout"""
    try:
        await asyncio.sleep(timeout_seconds)
        
        channel = bot.get_channel(channel_id)
        if channel:
            await channel.delete(reason="Multiplayer lobby expired (inactivity timeout)")
            logger.info(f"🗑️ Cleaned up lobby channel: {channel_id}")
            
            # Remove from database
            from main import DatabasePool
            async with DatabasePool.pool.acquire() as conn:
                await conn.execute(
                    "DELETE FROM game_channels WHERE channel_id = $1",
                    channel_id
                )
            
            # Remove from active lobbies
            if channel_id in ACTIVE_LOBBIES:
                del ACTIVE_LOBBIES[channel_id]
    except Exception as e:
        logger.error(f"Error in lobby cleanup: {e}")

# ============================================================================
# COG REGISTRATION
# ============================================================================

class MultiplayerLobbyManagerCog(commands.Cog):
    """Multiplayer Lobby Manager Cog"""
    
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

async def setup(bot: commands.Bot) -> None:
    """Setup the cog"""
    await bot.add_cog(MultiplayerLobbyManagerCog(bot))
    logger.info("✅ Multiplayer Lobby Manager Cog loaded")
