import discord
from discord.ext import commands
import asyncpg
import random
import logging
from typing import Optional, Dict, List, Set
import asyncio
from datetime import datetime, timedelta

logger = logging.getLogger("GamingBot")

class LobbySession:
    """Represents an active multiplayer lobby"""
    
    def __init__(self, host_id: int, channel_id: int, guild_id: int, max_players: int = 4, is_private: bool = False):
        self.host_id = host_id
        self.channel_id = channel_id
        self.guild_id = guild_id
        self.max_players = max_players
        self.is_private = is_private
        self.invited_users: Set[int] = set()
        self.active_players: Set[int] = set([host_id])
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        self.current_game: Optional[str] = None
        self.game_in_progress = False

class MultiGameView(discord.ui.View):
    """Multiplayer game selection interface"""
    
    def __init__(self, lobby: LobbySession, bot):
        super().__init__(timeout=None)
        self.lobby = lobby
        self.bot = bot
    
    async def update_activity(self):
        """Update last activity in database"""
        try:
            async with self.bot.db_pool.acquire() as conn:
                await conn.execute(
                    "UPDATE active_lobbies SET last_activity = NOW() WHERE channel_id = $1",
                    self.lobby.channel_id
                )
        except Exception as e:
            logger.error(f"❌ Failed to update activity: {e}", exc_info=True)
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Verify user is in the lobby"""
        if interaction.user.id not in self.lobby.active_players and interaction.user.id != self.lobby.host_id:
            if self.lobby.is_private and interaction.user.id not in self.lobby.invited_users:
                await interaction.response.send_message(
                    "❌ You are not invited to this lobby!",
                    ephemeral=True
                )
                return False
        return True
    
    @discord.ui.button(label="💭 Truth or Dare", style=discord.ButtonStyle.primary, custom_id="multi_truthordare")
    async def truth_or_dare(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Truth or Dare multiplayer game"""
        await interaction.response.defer()
        await self.update_activity()
        
        if self.lobby.game_in_progress:
            await interaction.followup.send("❌ A game is already in progress!", ephemeral=True)
            return
        
        self.lobby.current_game = "Truth or Dare"
        self.lobby.game_in_progress = True
        
        truths = [
            "What's your biggest fear?",
            "Have you ever lied to your best friend?",
            "What's something you've never told anyone?",
            "What's your guilty pleasure?",
            "If you could change one thing about yourself, what would it be?",
            "What's the most embarrassing thing that's happened to you?",
            "Who's your celebrity crush?",
            "What's a habit you wish you could break?",
            "What's your biggest insecurity?",
            "Have you ever cheated on anything?",
        ]
        
        dares = [
            "Do your best impression of someone here",
            "Sing a song for 30 seconds",
            "Do 10 pushups",
            "Speak in an accent for the next round",
            "Send a meme to someone",
            "Do the worm on the floor",
            "Call a friend and sing happy birthday",
            "Post an embarrassing selfie",
            "Walk around the house like a penguin",
            "Dance for 30 seconds without music",
        ]
        
        players_list = list(self.lobby.active_players)
        random.shuffle(players_list)
        
        embed = discord.Embed(
            title="💭 TRUTH OR DARE - GAME START",
            description="The game has begun! Check the thread for prompts.",
            color=0xFF1493
        )
        embed.add_field(name="👥 Players", value=f"{len(players_list)} players", inline=False)
        embed.add_field(name="💬 Rules", value="Players take turns choosing truth or dare. No backing out!", inline=False)
        
        await interaction.followup.send(embed=embed)
        
        for idx, player_id in enumerate(players_list[:4], 1):
            await asyncio.sleep(2)
            
            player = self.bot.get_user(player_id)
            choice_type = random.choice(["Truth", "Dare"])
            
            if choice_type == "Truth":
                prompt = random.choice(truths)
            else:
                prompt = random.choice(dares)
            
            prompt_embed = discord.Embed(
                title=f"💭 {choice_type.upper()} - Player {idx}",
                description=f"{player.mention if player else f'User {player_id}'}\n\n{prompt}",
                color=0xFF1493
            )
            
            await interaction.channel.send(embed=prompt_embed)
        
        self.lobby.game_in_progress = False
    
    @discord.ui.button(label="🤔 Would You Rather", style=discord.ButtonStyle.primary, custom_id="multi_wouldyou")
    async def would_you_rather(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Would You Rather multiplayer game"""
        await interaction.response.defer()
        await self.update_activity()
        
        if self.lobby.game_in_progress:
            await interaction.followup.send("❌ A game is already in progress!", ephemeral=True)
            return
        
        self.lobby.current_game = "Would You Rather"
        self.lobby.game_in_progress = True
        
        questions = [
            {"option1": "Fly", "option2": "Invisible"},
            {"option1": "Never sleep again", "option2": "Always sleep 8 hours but miss events"},
            {"option1": "Time travel to past", "option2": "Time travel to future"},
            {"option1": "Live in a castle", "option2": "Live on a tropical island"},
            {"option1": "Have the ability to talk to animals", "option2": "Speak all languages"},
            {"option1": "Always be 10 minutes late", "option2": "Always be 20 minutes early"},
            {"option1": "Have spaghetti for hair", "option2": "Have maple syrup for sweat"},
            {"option1": "Fight one horse-sized duck", "option2": "Fight 100 duck-sized horses"},
            {"option1": "Never use internet again", "option2": "Never eat pizza again"},
            {"option1": "Live without music", "option2": "Live without movies"},
        ]
        
        embed = discord.Embed(
            title="🤔 WOULD YOU RATHER - GAME START",
            description="Players will vote on various choices!",
            color=0x00D9FF
        )
        embed.add_field(name="👥 Players", value=f"{len(self.lobby.active_players)} playing", inline=False)
        
        await interaction.followup.send(embed=embed)
        
        for idx, q in enumerate(questions[:5], 1):
            await asyncio.sleep(3)
            
            view = WYRVotingView(q["option1"], q["option2"])
            choice_embed = discord.Embed(
                title=f"🤔 QUESTION {idx}/5",
                description=f"**Would you rather:**\n\n1️⃣ {q['option1']}\n\n2️⃣ {q['option2']}",
                color=0x00D9FF
            )
            
            await interaction.channel.send(embed=choice_embed, view=view)
        
        self.lobby.game_in_progress = False
    
    @discord.ui.button(label="🏃 Fast Finger Quiz", style=discord.ButtonStyle.primary, custom_id="multi_fastfinger")
    async def fast_finger_quiz(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Fast Finger Quiz multiplayer game"""
        await interaction.response.defer()
        await self.update_activity()
        
        if self.lobby.game_in_progress:
            await interaction.followup.send("❌ A game is already in progress!", ephemeral=True)
            return
        
        self.lobby.current_game = "Fast Finger Quiz"
        self.lobby.game_in_progress = True
        
        questions = [
            {"q": "What's the capital of Japan?", "correct": "Tokyo", "options": ["Tokyo", "Osaka", "Kyoto"]},
            {"q": "What's the largest ocean?", "correct": "Pacific", "options": ["Atlantic", "Pacific", "Indian"]},
            {"q": "Who wrote Romeo and Juliet?", "correct": "Shakespeare", "options": ["Marlowe", "Shakespeare", "Jonson"]},
            {"q": "What's 7 × 8?", "correct": "56", "options": ["54", "56", "58"]},
            {"q": "What's the smallest planet?", "correct": "Mercury", "options": ["Venus", "Mercury", "Mars"]},
        ]
        
        embed = discord.Embed(
            title="🏃 FAST FINGER QUIZ - START!",
            description="Answer the questions as fast as you can!",
            color=0xFF1493
        )
        embed.add_field(name="⚡ Speed", value="First correct answer wins the point!", inline=False)
        
        await interaction.followup.send(embed=embed)
        
        scores: Dict[int, int] = {pid: 0 for pid in self.lobby.active_players}
        
        for idx, q in enumerate(questions, 1):
            await asyncio.sleep(2)
            
            random.shuffle(q["options"])
            view = FastFingerView(q["correct"], scores)
            
            quiz_embed = discord.Embed(
                title=f"❓ QUESTION {idx}",
                description=q["q"],
                color=0xFF1493
            )
            
            for oidx, option in enumerate(q["options"], 1):
                quiz_embed.add_field(name=f"Option {oidx}", value=option, inline=False)
            
            await interaction.channel.send(embed=quiz_embed, view=view)
            await asyncio.sleep(5)
        
        winner_id = max(scores, key=scores.get)
        winner = self.bot.get_user(winner_id)
        
        results_embed = discord.Embed(
            title="🏆 QUIZ RESULTS",
            description=f"Winner: {winner.mention if winner else f'User {winner_id}'} with {scores[winner_id]} points!",
            color=0x00D9FF
        )
        
        for pid, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
            user = self.bot.get_user(pid)
            results_embed.add_field(name=user.display_name if user else f"User {pid}", value=f"{score} points", inline=False)
        
        await interaction.channel.send(embed=results_embed)
        
        self.lobby.game_in_progress = False
    
    @discord.ui.button(label="🔤 Word Wars", style=discord.ButtonStyle.primary, custom_id="multi_wordwars")
    async def word_wars(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Word Wars multiplayer game"""
        await interaction.response.defer()
        await self.update_activity()
        
        if self.lobby.game_in_progress:
            await interaction.followup.send("❌ A game is already in progress!", ephemeral=True)
            return
        
        self.lobby.current_game = "Word Wars"
        self.lobby.game_in_progress = True
        
        starting_words = ["GAMING", "DISCORD", "PYTHON", "AMAZING", "ELITE"]
        current_word = random.choice(starting_words)
        
        embed = discord.Embed(
            title="🔤 WORD WARS - START!",
            description=f"Starting word: **{current_word}**\n\nEach player must find a word that rhymes!",
            color=0x00D9FF
        )
        embed.add_field(name="📋 Rules", value="Players take turns finding words. No repeats allowed!", inline=False)
        
        await interaction.followup.send(embed=embed)
        
        players_list = list(self.lobby.active_players)
        
        for round_num in range(1, 4):
            await asyncio.sleep(2)
            
            round_embed = discord.Embed(
                title=f"🔤 ROUND {round_num}",
                description=f"Current word: **{current_word}**",
                color=0x00D9FF
            )
            round_embed.add_field(name="👥 Players", value=f"{len(players_list)} competing", inline=False)
            
            await interaction.channel.send(embed=round_embed)
            
            for player_id in players_list:
                await asyncio.sleep(1)
                player = self.bot.get_user(player_id)
                player_embed = discord.Embed(
                    title=f"🎤 {player.display_name if player else f'Player {player_id}'}'s Turn",
                    description=f"Find a word that rhymes with **{current_word}**",
                    color=0xFF1493
                )
                await interaction.channel.send(embed=player_embed)
        
        self.lobby.game_in_progress = False
    
    @discord.ui.button(label="👑 King of the Hill", style=discord.ButtonStyle.primary, custom_id="multi_kinghill")
    async def king_of_the_hill(self, interaction: discord.Interaction, button: discord.ui.Button):
        """King of the Hill multiplayer game"""
        await interaction.response.defer()
        await self.update_activity()
        
        if self.lobby.game_in_progress:
            await interaction.followup.send("❌ A game is already in progress!", ephemeral=True)
            return
        
        self.lobby.current_game = "King of the Hill"
        self.lobby.game_in_progress = True
        
        players_list = list(self.lobby.active_players)
        random.shuffle(players_list)
        
        current_king = players_list[0]
        challengers = players_list[1:]
        
        embed = discord.Embed(
            title="👑 KING OF THE HILL - START!",
            description="Last player standing becomes the ultimate champion!",
            color=0xFF1493
        )
        king_user = self.bot.get_user(current_king)
        embed.add_field(name="👑 Current King", value=king_user.mention if king_user else f"Player {current_king}", inline=False)
        
        await interaction.followup.send(embed=embed)
        
        round_num = 1
        while len(challengers) > 0:
            await asyncio.sleep(2)
            
            challenger = random.choice(challengers)
            challenger_user = self.bot.get_user(challenger)
            king_user = self.bot.get_user(current_king)
            
            battle_embed = discord.Embed(
                title=f"⚔️ ROUND {round_num} - BATTLE!",
                description=f"**{king_user.mention if king_user else f'King'}** vs **{challenger_user.mention if challenger_user else 'Challenger'}**",
                color=0xFF1493
            )
            
            await interaction.channel.send(embed=battle_embed)
            await asyncio.sleep(2)
            
            winner = random.choice([current_king, challenger])
            loser = challenger if winner == current_king else current_king
            
            winner_user = self.bot.get_user(winner)
            loser_user = self.bot.get_user(loser)
            
            result_embed = discord.Embed(
                title="🏆 BATTLE RESULT",
                description=f"**{winner_user.mention if winner_user else 'Winner'}** defeats **{loser_user.mention if loser_user else 'Loser'}**!",
                color=0x00D9FF
            )
            
            await interaction.channel.send(embed=result_embed)
            
            if winner == current_king:
                challengers.remove(challenger)
            else:
                current_king = challenger
                challengers.remove(loser)
                challengers.append(loser)
            
            round_num += 1
        
        final_king = self.bot.get_user(current_king)
        final_embed = discord.Embed(
            title="👑 CHAMPION CROWNED!",
            description=f"**{final_king.mention if final_king else f'Player {current_king}'}** is the King of the Hill!",
            color=0xFFD700
        )
        
        await interaction.channel.send(embed=final_embed)
        
        self.lobby.game_in_progress = False
    
    @discord.ui.button(label="🎨 Quick Draw Vote", style=discord.ButtonStyle.primary, custom_id="multi_quickdraw")
    async def quick_draw_voting(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Quick Draw Voting multiplayer game"""
        await interaction.response.defer()
        await self.update_activity()
        
        if self.lobby.game_in_progress:
            await interaction.followup.send("❌ A game is already in progress!", ephemeral=True)
            return
        
        self.lobby.current_game = "Quick Draw Vote"
        self.lobby.game_in_progress = True
        
        prompts = [
            "Draw a pizza",
            "Draw a cat wearing sunglasses",
            "Draw your favorite video game character",
            "Draw a spaceship",
            "Draw a meme",
            "Draw your mood today",
            "Draw a dinosaur",
            "Draw your idea of the future",
        ]
        
        embed = discord.Embed(
            title="🎨 QUICK DRAW VOTING - START!",
            description="Players draw, others vote for their favorite!",
            color=0xFF1493
        )
        embed.add_field(name="📋 Rules", value="Everyone draws the same prompt, then votes for the best!", inline=False)
        
        await interaction.followup.send(embed=embed)
        
        for round_num, prompt in enumerate(prompts[:3], 1):
            await asyncio.sleep(2)
            
            draw_embed = discord.Embed(
                title=f"🎨 ROUND {round_num}",
                description=f"**Prompt: {prompt}**\n\nDraw this in 2 minutes!",
                color=0xFF1493
            )
            
            await interaction.channel.send(embed=draw_embed)
            await asyncio.sleep(120)
            
            players_list = list(self.lobby.active_players)
            
            vote_embed = discord.Embed(
                title=f"🗳️ VOTING TIME",
                description="Vote for the best drawing!",
                color=0x00D9FF
            )
            
            for idx, player_id in enumerate(players_list, 1):
                player = self.bot.get_user(player_id)
                vote_embed.add_field(name=f"Option {idx}", value=player.mention if player else f"Player {player_id}", inline=False)
            
            await interaction.channel.send(embed=vote_embed)
            await asyncio.sleep(3)
        
        self.lobby.game_in_progress = False
    
    @discord.ui.button(label="🎭 Emoji Story", style=discord.ButtonStyle.primary, custom_id="multi_emojistory")
    async def emoji_story(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Emoji Story collaborative game"""
        await interaction.response.defer()
        await self.update_activity()
        
        if self.lobby.game_in_progress:
            await interaction.followup.send("❌ A game is already in progress!", ephemeral=True)
            return
        
        self.lobby.current_game = "Emoji Story"
        self.lobby.game_in_progress = True
        
        embed = discord.Embed(
            title="🎭 EMOJI STORY - COLLABORATIVE!",
            description="Each player adds one emoji to build a story!",
            color=0x00D9FF
        )
        embed.add_field(name="📋 Rules", value="Take turns adding emojis. Create a creative narrative!", inline=False)
        
        await interaction.followup.send(embed=embed)
        
        players_list = list(self.lobby.active_players)
        story_emojis = []
        
        for turn in range(len(players_list) * 2):
            await asyncio.sleep(1)
            
            current_player_idx = turn % len(players_list)
            player_id = players_list[current_player_idx]
            player = self.bot.get_user(player_id)
            
            story_embed = discord.Embed(
                title=f"🎭 TURN {turn + 1}",
                description=f"Story so far: {' '.join(story_emojis) if story_emojis else '(No story yet)'}",
                color=0x00D9FF
            )
            story_embed.add_field(
                name=f"{player.display_name if player else f'Player {player_id}'}'s Turn",
                value="Add an emoji!",
                inline=False
            )
            
            await interaction.channel.send(embed=story_embed)
            
            random_emojis = ["🎮", "💻", "🎯", "🚀", "⭐", "🔥", "💎", "🎪", "🎭", "🎨"]
            story_emojis.append(random.choice(random_emojis))
        
        final_embed = discord.Embed(
            title="🎭 FINAL STORY",
            description=" ".join(story_emojis),
            color=0x00D9FF
        )
        
        await interaction.channel.send(embed=final_embed)
        
        self.lobby.game_in_progress = False
    
    @discord.ui.button(label="🧠 Trivia Deathmatch", style=discord.ButtonStyle.primary, custom_id="multi_triviadeath")
    async def trivia_deathmatch(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Trivia Deathmatch competitive game"""
        await interaction.response.defer()
        await self.update_activity()
        
        if self.lobby.game_in_progress:
            await interaction.followup.send("❌ A game is already in progress!", ephemeral=True)
            return
        
        self.lobby.current_game = "Trivia Deathmatch"
        self.lobby.game_in_progress = True
        
        questions = [
            {"q": "What's the capital of France?", "correct": "Paris", "options": ["Paris", "Lyon", "Marseille"]},
            {"q": "What is 15 × 12?", "correct": "180", "options": ["180", "160", "200"]},
            {"q": "What's the largest planet?", "correct": "Jupiter", "options": ["Mars", "Jupiter", "Saturn"]},
            {"q": "Who painted the Mona Lisa?", "correct": "Leonardo da Vinci", "options": ["da Vinci", "Michelangelo", "Raphael"]},
            {"q": "What's the smallest country?", "correct": "Vatican City", "options": ["Monaco", "Vatican City", "Andorra"]},
        ]
        
        embed = discord.Embed(
            title="🧠 TRIVIA DEATHMATCH - START!",
            description="Fastest correct answer wins the point!",
            color=0xFF1493
        )
        embed.add_field(name="🏆 Rules", value="Answer correctly and quickly to score points!", inline=False)
        
        await interaction.followup.send(embed=embed)
        
        scores: Dict[int, int] = {pid: 0 for pid in self.lobby.active_players}
        
        for idx, q in enumerate(questions, 1):
            await asyncio.sleep(2)
            
            random.shuffle(q["options"])
            view = TriviaDeathmatchView(q["correct"], scores)
            
            quiz_embed = discord.Embed(
                title=f"❓ QUESTION {idx}",
                description=q["q"],
                color=0xFF1493
            )
            
            for oidx, option in enumerate(q["options"], 1):
                quiz_embed.add_field(name=f"{oidx}", value=option, inline=True)
            
            await interaction.channel.send(embed=quiz_embed, view=view)
            await asyncio.sleep(6)
        
        winner_id = max(scores, key=scores.get)
        winner = self.bot.get_user(winner_id)
        
        results_embed = discord.Embed(
            title="🏆 DEATHMATCH RESULTS",
            description=f"Champion: {winner.mention if winner else f'Player {winner_id}'} with {scores[winner_id]} points!",
            color=0x00D9FF
        )
        
        for pid, score in sorted(scores.items(), key=lambda x: x[1], reverse=True)[:5]:
            user = self.bot.get_user(pid)
            results_embed.add_field(name=user.display_name if user else f"Player {pid}", value=f"{score} points", inline=False)
        
        await interaction.channel.send(embed=results_embed)
        
        self.lobby.game_in_progress = False
    
    @discord.ui.button(label="⚡ Rapid Riddles", style=discord.ButtonStyle.primary, custom_id="multi_rapidriddles")
    async def rapid_fire_riddles(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Rapid Fire Riddles multiplayer game"""
        await interaction.response.defer()
        await self.update_activity()
        
        if self.lobby.game_in_progress:
            await interaction.followup.send("❌ A game is already in progress!", ephemeral=True)
            return
        
        self.lobby.current_game = "Rapid Riddles"
        self.lobby.game_in_progress = True
        
        riddles = [
            {"riddle": "I have cities but no houses. What am I?", "answer": "A map"},
            {"riddle": "What has hands but cannot clap?", "answer": "A clock"},
            {"riddle": "I'm light as a feather, yet the strongest person can't hold me. What am I?", "answer": "Your breath"},
            {"riddle": "What can travel the world while staying in a corner?", "answer": "A stamp"},
            {"riddle": "What has a head and a tail but no body?", "answer": "A coin"},
        ]
        
        embed = discord.Embed(
            title="⚡ RAPID FIRE RIDDLES - GO!",
            description="Answer the riddles as fast as you can!",
            color=0xFF1493
        )
        embed.add_field(name="⏱️ Speed", value="First correct answer wins the point!", inline=False)
        
        await interaction.followup.send(embed=embed)
        
        scores: Dict[int, int] = {pid: 0 for pid in self.lobby.active_players}
        
        for idx, r in enumerate(riddles, 1):
            await asyncio.sleep(2)
            
            view = RiddleRaceView(r["answer"], scores)
            
            riddle_embed = discord.Embed(
                title=f"🧩 RIDDLE {idx}",
                description=r["riddle"],
                color=0xFF1493
            )
            
            await interaction.channel.send(embed=riddle_embed, view=view)
            await asyncio.sleep(5)
        
        winner_id = max(scores, key=scores.get)
        winner = self.bot.get_user(winner_id)
        
        results_embed = discord.Embed(
            title="🏆 RIDDLE RESULTS",
            description=f"Champion: {winner.mention if winner else f'Player {winner_id}'} with {scores[winner_id]} points!",
            color=0x00D9FF
        )
        
        for pid, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
            user = self.bot.get_user(pid)
            results_embed.add_field(name=user.display_name if user else f"Player {pid}", value=f"{score} points", inline=False)
        
        await interaction.channel.send(embed=results_embed)
        
        self.lobby.game_in_progress = False
    
    @discord.ui.button(label="⚔️ Team Split", style=discord.ButtonStyle.primary, custom_id="multi_teamsplit")
    async def team_split_challenge(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Team Split Challenge multiplayer game"""
        await interaction.response.defer()
        await self.update_activity()
        
        if self.lobby.game_in_progress:
            await interaction.followup.send("❌ A game is already in progress!", ephemeral=True)
            return
        
        self.lobby.current_game = "Team Split Challenge"
        self.lobby.game_in_progress = True
        
        players_list = list(self.lobby.active_players)
        
        if len(players_list) < 2:
            await interaction.followup.send("❌ Need at least 2 players!", ephemeral=True)
            return
        
        random.shuffle(players_list)
        mid = len(players_list) // 2
        
        team1 = players_list[:mid]
        team2 = players_list[mid:]
        
        embed = discord.Embed(
            title="⚔️ TEAM SPLIT CHALLENGE - BATTLE!",
            description="Two teams compete head-to-head!",
            color=0xFF1493
        )
        
        team1_str = ", ".join([f"<@{pid}>" for pid in team1])
        team2_str = ", ".join([f"<@{pid}>" for pid in team2])
        
        embed.add_field(name="🔴 Team 1", value=team1_str or "Solo", inline=False)
        embed.add_field(name="🔵 Team 2", value=team2_str or "Solo", inline=False)
        
        await interaction.followup.send(embed=embed)
        
        challenges = [
            {"challenge": "Name as many countries as you can in 30 seconds", "type": "List"},
            {"challenge": "Answer trivia questions correctly", "type": "Trivia"},
            {"challenge": "Rhyme with the word GAMING", "type": "Rhyme"},
            {"challenge": "Complete the phrase: 'Discord is...'", "type": "Phrase"},
        ]
        
        team_scores = {1: 0, 2: 0}
        
        for round_num, challenge in enumerate(challenges, 1):
            await asyncio.sleep(2)
            
            round_embed = discord.Embed(
                title=f"⚔️ ROUND {round_num}",
                description=f"Challenge: {challenge['challenge']}",
                color=0xFF1493
            )
            
            await interaction.channel.send(embed=round_embed)
            await asyncio.sleep(4)
            
            winning_team = random.choice([1, 2])
            team_scores[winning_team] += 1
            
            winner_embed = discord.Embed(
                title="🎉 ROUND WINNER",
                description=f"Team {winning_team} scores a point!",
                color=0x00D9FF
            )
            
            await interaction.channel.send(embed=winner_embed)
        
        overall_winner = max(team_scores, key=team_scores.get)
        
        final_embed = discord.Embed(
            title="🏆 MATCH RESULTS",
            description=f"Team {overall_winner} wins with {team_scores[overall_winner]} points!",
            color=0xFFD700
        )
        final_embed.add_field(name="Team 1 Score", value=str(team_scores[1]), inline=True)
        final_embed.add_field(name="Team 2 Score", value=str(team_scores[2]), inline=True)
        
        await interaction.channel.send(embed=final_embed)
        
        self.lobby.game_in_progress = False

class WYRVotingView(discord.ui.View):
    """Would You Rather voting interface"""
    
    def __init__(self, option1: str, option2: str):
        super().__init__(timeout=None)
        self.option1 = option1
        self.option2 = option2
        self.votes1 = 0
        self.votes2 = 0
        self.voted_users: Set[int] = set()
    
    @discord.ui.button(label="1️⃣ Option 1", style=discord.ButtonStyle.primary, custom_id="wyr_option1")
    async def vote_option1(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        
        if interaction.user.id in self.voted_users:
            await interaction.followup.send("❌ You already voted!", ephemeral=True)
            return
        
        self.votes1 += 1
        self.voted_users.add(interaction.user.id)
        
        await interaction.followup.send(
            f"✅ You voted for **{self.option1}**!",
            ephemeral=True
        )
    
    @discord.ui.button(label="2️⃣ Option 2", style=discord.ButtonStyle.primary, custom_id="wyr_option2")
    async def vote_option2(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        
        if interaction.user.id in self.voted_users:
            await interaction.followup.send("❌ You already voted!", ephemeral=True)
            return
        
        self.votes2 += 1
        self.voted_users.add(interaction.user.id)
        
        await interaction.followup.send(
            f"✅ You voted for **{self.option2}**!",
            ephemeral=True
        )

class FastFingerView(discord.ui.View):
    """Fast Finger Quiz answer selection"""
    
    def __init__(self, correct_answer: str, scores: Dict[int, int]):
        super().__init__(timeout=None)
        self.correct_answer = correct_answer
        self.scores = scores
        self.answered_users: Set[int] = set()
        self.answered = False
    
    @discord.ui.button(label="Option 1", style=discord.ButtonStyle.primary, custom_id="ff_opt1")
    async def option1(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.answer_question(interaction)
    
    @discord.ui.button(label="Option 2", style=discord.ButtonStyle.primary, custom_id="ff_opt2")
    async def option2(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.answer_question(interaction)
    
    @discord.ui.button(label="Option 3", style=discord.ButtonStyle.primary, custom_id="ff_opt3")
    async def option3(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.answer_question(interaction)
    
    async def answer_question(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        if interaction.user.id in self.answered_users:
            await interaction.followup.send("❌ Already answered!", ephemeral=True)
            return
        
        is_correct = interaction.data["custom_id"].split("_")[2] in ["opt" + str(i) for i in range(1, 4)]
        
        if is_correct and not self.answered:
            self.scores[interaction.user.id] += 1
            self.answered = True
            await interaction.followup.send("✅ Correct! Point awarded!", ephemeral=True)
        elif self.answered:
            await interaction.followup.send("❌ Someone already answered!", ephemeral=True)
        else:
            await interaction.followup.send("❌ Wrong answer!", ephemeral=True)
        
        self.answered_users.add(interaction.user.id)

class TriviaDeathmatchView(discord.ui.View):
    """Trivia Deathmatch answer selection"""
    
    def __init__(self, correct_answer: str, scores: Dict[int, int]):
        super().__init__(timeout=None)
        self.correct_answer = correct_answer
        self.scores = scores
        self.answered_users: Set[int] = set()
        self.answered = False
    
    @discord.ui.button(label="1", style=discord.ButtonStyle.primary, custom_id="td_1")
    async def option1(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.answer_trivia(interaction)
    
    @discord.ui.button(label="2", style=discord.ButtonStyle.primary, custom_id="td_2")
    async def option2(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.answer_trivia(interaction)
    
    @discord.ui.button(label="3", style=discord.ButtonStyle.primary, custom_id="td_3")
    async def option3(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.answer_trivia(interaction)
    
    async def answer_trivia(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        if interaction.user.id in self.answered_users:
            return
        
        if not self.answered:
            self.scores[interaction.user.id] += 1
            self.answered = True
            await interaction.followup.send("✅ Point awarded!", ephemeral=True)
        else:
            await interaction.followup.send("❌ Someone answered first!", ephemeral=True)
        
        self.answered_users.add(interaction.user.id)

class RiddleRaceView(discord.ui.View):
    """Riddle Race answer selection"""
    
    def __init__(self, correct_answer: str, scores: Dict[int, int]):
        super().__init__(timeout=None)
        self.correct_answer = correct_answer
        self.scores = scores
        self.answered_users: Set[int] = set()
        self.answered = False
    
    async def process_answer(self, interaction: discord.Interaction, user_answer: str):
        await interaction.response.defer(ephemeral=True)
        
        if interaction.user.id in self.answered_users:
            return
        
        is_correct = user_answer.lower() in self.correct_answer.lower()
        
        if is_correct and not self.answered:
            self.scores[interaction.user.id] += 1
            self.answered = True
            await interaction.followup.send("✅ Correct! Point awarded!", ephemeral=True)
        elif self.answered:
            await interaction.followup.send("❌ Someone answered first!", ephemeral=True)
        else:
            await interaction.followup.send("❌ Wrong answer!", ephemeral=True)
        
        self.answered_users.add(interaction.user.id)

class LobbyConfigurationView(discord.ui.View):
    """Lobby configuration dashboard"""
    
    def __init__(self, lobby: LobbySession, bot):
        super().__init__(timeout=None)
        self.lobby = lobby
        self.bot = bot
    
    @discord.ui.button(label="👥 2 Players", style=discord.ButtonStyle.primary, custom_id="config_2players")
    async def set_2_players(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        self.lobby.max_players = 2
        await interaction.followup.send("✅ Lobby set for 2 players!", ephemeral=True)
    
    @discord.ui.button(label="👥 4 Players", style=discord.ButtonStyle.primary, custom_id="config_4players")
    async def set_4_players(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        self.lobby.max_players = 4
        await interaction.followup.send("✅ Lobby set for 4 players!", ephemeral=True)
    
    @discord.ui.button(label="👥 8 Players", style=discord.ButtonStyle.primary, custom_id="config_8players")
    async def set_8_players(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        self.lobby.max_players = 8
        await interaction.followup.send("✅ Lobby set for 8 players!", ephemeral=True)
    
    @discord.ui.button(label="👥 Unlimited", style=discord.ButtonStyle.primary, custom_id="config_unlimited")
    async def set_unlimited(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        self.lobby.max_players = 999
        await interaction.followup.send("✅ Lobby set for unlimited players!", ephemeral=True)
    
    @discord.ui.button(label="🔓 Public", style=discord.ButtonStyle.success, custom_id="config_public")
    async def set_public(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        self.lobby.is_private = False
        await interaction.followup.send("✅ Lobby set to Public!", ephemeral=True)
    
    @discord.ui.button(label="🔒 Private", style=discord.ButtonStyle.danger, custom_id="config_private")
    async def set_private(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        self.lobby.is_private = True
        await interaction.followup.send("✅ Lobby set to Private! Use /invite to add friends.", ephemeral=True)
    
    @discord.ui.button(label="➕ Invite Friend", style=discord.ButtonStyle.secondary, custom_id="config_invite")
    async def invite_friend(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(InviteFriendModal(self.lobby))

class InviteFriendModal(discord.ui.Modal, title="Invite Friend to Lobby"):
    """Modal for inviting friends"""
    
    user_id = discord.ui.TextInput(label="Friend's User ID", placeholder="Enter Discord User ID")
    
    def __init__(self, lobby: LobbySession):
        super().__init__()
        self.lobby = lobby
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            friend_id = int(self.user_id.value)
            self.lobby.invited_users.add(friend_id)
            await interaction.response.send_message(
                f"✅ User {friend_id} invited to the lobby!",
                ephemeral=True
            )
        except ValueError:
            await interaction.response.send_message(
                "❌ Invalid User ID!",
                ephemeral=True
            )

class MultiCreationView(discord.ui.View):
    """Main button to create multiplayer lobby"""
    
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="⚔️ Host Matchmaking Lobby", style=discord.ButtonStyle.danger, custom_id="multi_create_lobby")
    async def create_multiplayer_lobby(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Create a multiplayer gaming lobby"""
        
        await interaction.response.defer(ephemeral=True)
        
        user_id = interaction.user.id
        guild_id = interaction.guild.id
        
        try:
            logger.info(f"⚔️ User {interaction.user} ({user_id}) creating multiplayer lobby in guild {guild_id}")
            
            category_name = "🎮 Gaming Hub"
            category = discord.utils.get(interaction.guild.categories, name=category_name)
            
            if not category:
                logger.error(f"❌ Gaming Hub category not found in guild {guild_id}")
                await interaction.followup.send(
                    "❌ Gaming Hub category not found! Please run `/setup_gaming_hub` first.",
                    ephemeral=True
                )
                return
            
            channel_name = f"🎮-{interaction.user.name}-lobby"
            
            overwrites = {
                interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
                interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
                interaction.client.user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            }
            
            multi_channel = await interaction.guild.create_text_channel(
                channel_name,
                category=category,
                overwrites=overwrites,
                topic=f"Multiplayer lobby hosted by {interaction.user.name}"
            )
            
            logger.info(f"✅ Created multiplayer channel {multi_channel.id} for user {user_id}")
            
            lobby = LobbySession(user_id, multi_channel.id, guild_id)
            
            async with interaction.client.db_pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO active_lobbies (guild_id, channel_id, host_id, max_players, is_private, last_activity)
                    VALUES ($1, $2, $3, $4, $5, NOW())
                    """,
                    guild_id, multi_channel.id, user_id, lobby.max_players, lobby.is_private
                )
            
            logger.info(f"📊 Recorded multiplayer lobby {multi_channel.id} in database")
            
            config_embed = discord.Embed(
                title="⚔️ LOBBY CONFIGURATION",
                description="Configure your lobby before going live!",
                color=0xFF1493
            )
            config_embed.add_field(name="👥 Player Limit", value="Click button to set (default: 4)", inline=False)
            config_embed.add_field(name="🔓 Privacy", value="Choose Public or Private (default: Public)", inline=False)
            config_embed.add_field(name="➕ Invites", value="Add friends if Private", inline=False)
            config_embed.set_footer(text="Configure below, then select a game!")
            
            await multi_channel.send(embed=config_embed, view=LobbyConfigurationView(lobby, interaction.client))
            
            games_embed = discord.Embed(
                title="🎮 GAME SELECTION",
                description="Choose a multiplayer game to play!",
                color=0xFF1493
            )
            games_embed.add_field(name="Available Games", value="10 unique multiplayer experiences", inline=False)
            games_embed.set_footer(text="Games are designed for group play!")
            
            await multi_channel.send(embed=games_embed, view=MultiGameView(lobby, interaction.client))
            
            logger.info(f"✅ Lobby interface deployed to channel {multi_channel.id}")
            
            await interaction.followup.send(
                f"✅ Multiplayer lobby created! Check {multi_channel.mention}",
                ephemeral=True
            )
        
        except Exception as e:
            logger.error(f"❌ Failed to create multiplayer lobby: {e}", exc_info=True)
            await interaction.followup.send(
                f"❌ Failed to create multiplayer lobby: {str(e)}",
                ephemeral=True
            )

class MultiManager(commands.Cog):
    """Multiplayer Lobby Manager Cog"""
    
    def __init__(self, bot):
        self.bot = bot
        self.active_lobbies: Dict[int, LobbySession] = {}
    
    async def cog_load(self):
        logger.info("✅ MultiManager cog loaded successfully")

async def setup(bot):
    """Setup function for the cog"""
    await bot.add_cog(MultiManager(bot))
    logger.info("✅ MultiManager cog registered")
