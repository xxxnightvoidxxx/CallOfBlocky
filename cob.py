#!/usr/bin/env python3
import pygame
import random
import math
import os
import sys

# Initialize
pygame.init()
pygame.mixer.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Call of Blocky: Duel Protocol")
clock = pygame.time.Clock()

# Fonts
font_sm = pygame.font.SysFont("Consolas", 18)
font_md = pygame.font.SysFont("Consolas", 28, bold=True)
font_lg = pygame.font.SysFont("Consolas", 45, bold=True)

# Colors
COLOR_PLAYER = (80, 150, 255)
COLOR_NPC = (255, 60, 60)
COLOR_BLOCK = (40, 40, 45)
COLOR_TRACER = (255, 200, 50)
COLOR_BG = (10, 10, 12)
COLOR_FLASH = (255, 255, 200)
COLOR_SPARK = (255, 255, 150)
COLOR_RELOAD = (100, 100, 100)

class AudioManager:
    def __init__(self):
        self.base_path = os.path.join("assets", "sound")
        self.player_shots = []
        self.npc_shots = []
        self.match_end_music = None
        self.load_assets()

    def load_assets(self):
        # Load Player Gunshots
        p_dir = os.path.join(self.base_path, "fireplayer")
        if os.path.exists(p_dir):
            for f in os.listdir(p_dir):
                if f.endswith((".wav", ".mp3", ".ogg")):
                    self.player_shots.append(pygame.mixer.Sound(os.path.join(p_dir, f)))

        # Load NPC Gunshots
        n_dir = os.path.join(self.base_path, "firenpc")
        if os.path.exists(n_dir):
            for f in os.listdir(n_dir):
                if f.endswith((".wav", ".mp3", ".ogg")):
                    self.npc_shots.append(pygame.mixer.Sound(os.path.join(n_dir, f)))

        # Match Results Music
        results_file = os.path.join(self.base_path, "matchresults.mp3")
        if os.path.exists(results_file):
            self.match_end_music = results_file

    def play_fire(self, owner):
        sounds = self.player_shots if owner == "player" else self.npc_shots
        if sounds:
            snd = random.choice(sounds)
            snd.play()
            # Fade out after 200ms to keep shots "snappy" as requested
            snd.fadeout(200)

    def play_results(self):
        if self.match_end_music:
            pygame.mixer.music.load(self.match_end_music)
            pygame.mixer.music.play(-1) # Loop until reset

    def stop_music(self):
        pygame.mixer.music.stop()

class Particle:
    def __init__(self, x, y, color):
        self.pos = [x, y]
        angle = random.uniform(0, math.pi * 2)
        s = random.uniform(1, 4)
        self.vel = [math.cos(angle) * s, math.sin(angle) * s]
        self.life = random.randint(20, 40)
        self.color = color
        self.size = random.randint(2, 4)

    def update(self):
        self.pos[0] += self.vel[0]; self.pos[1] += self.vel[1]
        self.life -= 1
        self.vel[0] *= 0.95; self.vel[1] *= 0.95

    def draw(self, surf, ox, oy):
        if self.life <= 0: return
        p_surf = pygame.Surface((self.size, self.size))
        p_surf.set_alpha(min(255, self.life * 8))
        p_surf.fill(self.color)
        surf.blit(p_surf, (self.pos[0] + ox, self.pos[1] + oy))

class Game:
    def __init__(self, audio_manager, kills=0, deaths=0):
        self.audio = audio_manager
        self.total_kills = kills
        self.total_deaths = deaths
        self.game_timer = 60.0
        self.match_over = False
        self.results_audio_played = False
        self.shake_amount = 0
        self.flashes = []
        self.particles = []
        self.reset_match()

    def reset_match(self):
        self.audio.stop_music()
        self.player = pygame.Rect(380, 500, 30, 30)
        self.npc = pygame.Rect(380, 60, 30, 30)
        self.npc_vel = pygame.Vector2(0, 0)
        self.player_vel = pygame.Vector2(0, 0)
        self.npc_decision_timer = 0
        self.blocks = [pygame.Rect(random.randint(50, 700), random.randint(100, 450), 
                       random.choice([60, 120]), 30) for _ in range(10)]
        self.player_hp = 100
        self.npc_hp = 100
        self.tracers = []
        self.pistol_ready_timer = 0
        self.pistol_cooldown_max = 30 

    def trigger_shake(self, intensity):
        self.shake_amount = max(self.shake_amount, intensity)

    def ray_cast(self, start_pos, target_pos, owner):
        if self.match_over: return
        
        # Audio feedback for shooting
        self.audio.play_fire(owner)
        self.flashes.append({"pos": start_pos, "life": 3})
        
        start_vec = pygame.Vector2(start_pos)
        target_vec = pygame.Vector2(target_pos)
        
        if owner == "npc":
            target_vec += self.player_vel * 15 

        direction = (target_vec - start_vec)
        if direction.length() == 0: return
        
        spread = max(2, 18 - self.total_kills) if owner == "npc" else 15
        offset = pygame.Vector2(random.uniform(-spread, spread), random.uniform(-spread, spread))
        target_vec += offset
        
        direction = (target_vec - start_vec).normalize()
        current_pos = pygame.Vector2(start_vec)
        hit_point = (current_pos.x + direction.x * 1000, current_pos.y + direction.y * 1000)
        
        for _ in range(120):
            current_pos += direction * 8
            test_rect = pygame.Rect(current_pos.x - 2, current_pos.y - 2, 4, 4)
            for b in self.blocks:
                if test_rect.colliderect(b):
                    hit_point = (current_pos.x, current_pos.y)
                    for _ in range(2): self.particles.append(Particle(hit_point[0], hit_point[1], COLOR_SPARK))
                    self.tracers.append({"start": start_pos, "end": hit_point, "life": 4})
                    return

            target_rect = self.npc if owner == "player" else self.player
            if test_rect.colliderect(target_rect):
                hit_point = (current_pos.x, current_pos.y)
                if owner == "player": 
                    self.npc_hp -= 20
                    for _ in range(8): self.particles.append(Particle(hit_point[0], hit_point[1], COLOR_NPC))
                else: 
                    self.player_hp -= 20
                    for _ in range(8): self.particles.append(Particle(hit_point[0], hit_point[1], COLOR_PLAYER))
                    self.trigger_shake(15)
                break
        
        self.tracers.append({"start": start_pos, "end": hit_point, "life": 4})

    def update(self):
        if self.shake_amount > 0: self.shake_amount *= 0.8
        if self.pistol_ready_timer > 0: self.pistol_ready_timer -= 1
        
        if not self.match_over:
            self.game_timer -= 1/60
            if self.game_timer <= 0: 
                self.game_timer = 0
                self.match_over = True

        if self.match_over:
            if not self.results_audio_played:
                self.audio.play_results()
                self.results_audio_played = True
            return

        # Player Movement
        keys = pygame.key.get_pressed()
        self.player_vel = pygame.Vector2(0, 0)
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: self.player_vel.x = -4
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: self.player_vel.x = 4
        if keys[pygame.K_UP] or keys[pygame.K_w]: self.player_vel.y = -4
        if keys[pygame.K_DOWN] or keys[pygame.K_s]: self.player_vel.y = 4
        self.player.x += self.player_vel.x; self.player.y += self.player_vel.y
        self.player.clamp_ip(screen.get_rect())

        # STEERING AI
        self.npc_decision_timer += 1
        if self.npc_decision_timer > 20: 
            npc_pos = pygame.Vector2(self.npc.center)
            player_pos = pygame.Vector2(self.player.center)
            diff = player_pos - npc_pos
            dist = diff.length()
            
            if dist < 220:
                steering = -diff.normalize() * 5 
            elif dist > 350:
                steering = diff.normalize() * 4 
            else:
                steering = pygame.Vector2(-diff.y, diff.x).normalize() * 5
                if random.random() > 0.5: steering *= -1

            if npc_pos.x < 100: steering.x += 6
            if npc_pos.x > WIDTH - 100: steering.x -= 6
            if npc_pos.y < 100: steering.y += 6
            if npc_pos.y > HEIGHT - 100: steering.y -= 6

            self.npc_vel = steering
            self.npc_decision_timer = 0

        self.npc.x += self.npc_vel.x; self.npc.y += self.npc_vel.y
        self.npc.clamp_ip(screen.get_rect())

        if random.randint(1, 35) == 1:
            self.ray_cast(self.npc.center, self.player.center, "npc")

        # Visuals update
        for t in self.tracers[:]:
            t["life"] -= 1
            if t["life"] <= 0: self.tracers.remove(t)
        for p in self.particles[:]:
            p.update()
            if p.life <= 0: self.particles.remove(p)

        if self.npc_hp <= 0:
            self.total_kills += 1; self.reset_match()
        elif self.player_hp <= 0:
            self.total_deaths += 1; self.reset_match()

    def draw(self):
        ox = random.uniform(-self.shake_amount, self.shake_amount) if self.shake_amount > 0 else 0
        oy = random.uniform(-self.shake_amount, self.shake_amount) if self.shake_amount > 0 else 0
        screen.fill(COLOR_BG)
        
        for b in self.blocks: pygame.draw.rect(screen, COLOR_BLOCK, b.move(ox, oy))
        for p in self.particles: p.draw(screen, ox, oy)
        for t in self.tracers: 
            pygame.draw.line(screen, COLOR_TRACER, (t["start"][0]+ox, t["start"][1]+oy), (t["end"][0]+ox, t["end"][1]+oy), 2)
        
        pygame.draw.rect(screen, COLOR_PLAYER, self.player.move(ox, oy))
        pygame.draw.rect(screen, COLOR_NPC, self.npc.move(ox, oy))

        # OVER-HEAD UI
        pygame.draw.rect(screen, (50, 50, 50), (self.player.x + ox, self.player.y + oy - 12, 30, 4))
        pygame.draw.rect(screen, (50, 200, 50), (self.player.x + ox, self.player.y + oy - 12, (self.player_hp/100)*30, 4))
        if self.pistol_ready_timer > 0:
            w = (self.pistol_ready_timer/self.pistol_cooldown_max)*30
            pygame.draw.rect(screen, COLOR_RELOAD, (self.player.x + ox, self.player.y + oy - 18, w, 3))

        pygame.draw.rect(screen, (50, 50, 50), (self.npc.x + ox, self.npc.y + oy - 12, 30, 4))
        pygame.draw.rect(screen, COLOR_NPC, (self.npc.x + ox, self.npc.y + oy - 12, (self.npc_hp/100)*30, 4))

        # HUD
        timer_txt = font_md.render(f"TIME: {int(self.game_timer)}s", True, (255, 255, 255))
        screen.blit(timer_txt, (WIDTH//2 - 50, 20))
        
        if self.match_over:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 230))
            screen.blit(overlay, (0,0))
            screen.blit(font_lg.render("COMBAT COMPLETE", True, (255, 215, 0)), (WIDTH//2 - 180, 150))
            stats_txt = f"ELIMINATIONS: {self.total_kills} | DEATHS: {self.total_deaths}"
            screen.blit(font_md.render(stats_txt, True, (255, 255, 255)), (WIDTH//2 - 190, 250))
            screen.blit(font_sm.render("PRESS 'R' TO RE-ENGAGE", True, (150, 150, 150)), (WIDTH//2 - 120, 400))

# Initialize Managers
audio_manager = AudioManager()
game = Game(audio_manager)

# Main Loop
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT: 
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and not game.match_over and game.pistol_ready_timer <= 0:
                game.ray_cast(game.player.center, game.npc.center, "player")
                game.trigger_shake(4)
                game.pistol_ready_timer = game.pistol_cooldown_max
            if event.key == pygame.K_r and game.match_over: 
                # Preserve total stats across matches
                saved_kills = game.total_kills
                saved_deaths = game.total_deaths
                game = Game(audio_manager, saved_kills, saved_deaths)
                
    game.update()
    game.draw()
    pygame.display.flip()
    clock.tick(60)