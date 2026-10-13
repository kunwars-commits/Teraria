import pygame
import sys
import math
import random
import asyncio

pygame.init()
pygame.mixer.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Arcade")
clock = pygame.time.Clock()
font = pygame.font.SysFont("arial", 18, bold=True)
font_big = pygame.font.SysFont("arial", 44, bold=True)

try:
    player_img = pygame.image.load("assets/player.png").convert_alpha()
    cupcake_img = pygame.image.load("assets/cupcake.png").convert_alpha()
    jump_snd = pygame.mixer.Sound("assets/jump.ogg")
    collect_snd = pygame.mixer.Sound("assets/collect.ogg")
    win_snd = pygame.mixer.Sound("assets/win.ogg")
except:
    player_img = cupcake_img = jump_snd = collect_snd = win_snd = None

current_game = "MENU"

t_pos = pygame.Vector2(400, 450)
t_vel = pygame.Vector2(0, 0)
t_hp = t_score = t_fire_cd = t_wave = t_wave_cd = 0
t_jumps = 2
t_state = "PLAY"
t_bullets = []
t_enemies = []
t_pickups = []
t_plats = [pygame.Rect(0, 520, 800, 80), pygame.Rect(120, 400, 180, 16), pygame.Rect(500, 400, 180, 16),
           pygame.Rect(310, 290, 180, 16), pygame.Rect(180, 180, 140, 16), pygame.Rect(480, 180, 140, 16)]

def t_spawn_wave():
    global t_wave, t_wave_cd
    t_wave += 1
    n, spd, hp = 1 + t_wave * 2, 1.0 + t_wave * 0.2, 25 + t_wave * 10
    r = 14 + min(t_wave, 8)
    for _ in range(n):
        s = random.randint(0, 2)
        if s == 0: pos = pygame.Vector2(-30, random.randint(80, 480))
        elif s == 1: pos = pygame.Vector2(WIDTH + 30, random.randint(80, 480))
        else: pos = pygame.Vector2(random.randint(50, WIDTH - 50), -30)
        t_enemies.append({"pos": pos, "vel": pygame.Vector2(0, 0), "hp": hp, "mhp": hp,
                          "r": r, "spd": spd, "ang": random.uniform(0, 360)})
    t_wave_cd = 0

def reset_terraria():
    global t_pos, t_vel, t_hp, t_score, t_jumps, t_state, t_bullets, t_fire_cd
    global t_enemies, t_wave, t_wave_cd, t_pickups
    t_pos = pygame.Vector2(400, 450)
    t_vel = pygame.Vector2(0, 0)
    t_hp, t_score, t_jumps, t_fire_cd = 100, 0, 2, 0
    t_state = "PLAY"
    t_bullets, t_enemies, t_pickups = [], [], []
    t_wave, t_wave_cd = 0, 0
    t_spawn_wave()

ast_pos = pygame.Vector2(400, 300)
ast_vel = pygame.Vector2(0, 0)
ast_angle = 90.0
ast_hp = ast_score = ast_fire_cd = 0
ast_state = "PLAY"
ast_missiles = []
ast_e_missiles = []
ast_asteroids = []
ast_e_pos = pygame.Vector2(120, 120)
ast_e_vel = pygame.Vector2(1.2, 0.9)
ast_e_angle = 0.0
ast_e_state = "PATROL"
ast_e_cd = 0
ast_e_alive = True
ast_respawn = 0

def spawn_ast():
    side = random.choice(["top", "bottom", "left", "right"])
    if side == "top": pos = pygame.Vector2(random.randint(0, WIDTH), -30)
    elif side == "bottom": pos = pygame.Vector2(random.randint(0, WIDTH), HEIGHT + 30)
    elif side == "left": pos = pygame.Vector2(-30, random.randint(0, HEIGHT))
    else: pos = pygame.Vector2(WIDTH + 30, random.randint(0, HEIGHT))
    tgt = pygame.Vector2(random.randint(200, WIDTH - 200), random.randint(200, HEIGHT - 200))
    ast_asteroids.append({"pos": pos, "vel": (tgt - pos).normalize() * random.uniform(0.9, 2.0),
                          "radius": random.randint(20, 32)})

def reset_asteroids():
    global ast_pos, ast_vel, ast_angle, ast_hp, ast_score, ast_state, ast_fire_cd
    global ast_missiles, ast_e_missiles, ast_asteroids, ast_e_pos, ast_e_vel
    global ast_e_angle, ast_e_state, ast_e_cd, ast_e_alive, ast_respawn
    ast_pos, ast_vel = pygame.Vector2(400, 300), pygame.Vector2(0, 0)
    ast_angle, ast_hp, ast_score, ast_fire_cd = 90.0, 100, 0, 0
    ast_state = "PLAY"
    ast_missiles, ast_e_missiles, ast_asteroids = [], [], []
    ast_e_pos, ast_e_vel = pygame.Vector2(120, 120), pygame.Vector2(1.2, 0.9)
    ast_e_angle, ast_e_state, ast_e_cd = 0.0, "PATROL", 0
    ast_e_alive, ast_respawn = True, 0
    for _ in range(5): spawn_ast()

cc_player = pygame.Rect(380, 100, 40, 40)
cc_vel_x = cc_vel_y = 0
cc_grounded = cc_won = False
cc_cupcakes = []
cc_plats = [pygame.Rect(0, 550, 800, 50), pygame.Rect(80, 420, 220, 20), pygame.Rect(340, 320, 200, 20),
            pygame.Rect(560, 220, 180, 20), pygame.Rect(180, 180, 160, 20)]

def reset_cupcake():
    global cc_player, cc_vel_x, cc_vel_y, cc_grounded, cc_won, cc_cupcakes
    cc_player.x, cc_player.y = 380, 100
    cc_vel_x = cc_vel_y = 0
    cc_grounded = cc_won = False
    cc_cupcakes = [pygame.Rect(random.randint(60, 740), random.randint(60, 490), 28, 28) for _ in range(10)]

reset_terraria()
reset_asteroids()
reset_cupcake()

b1 = pygame.Rect(WIDTH // 2 - 160, 200, 320, 50)
b2 = pygame.Rect(WIDTH // 2 - 160, 270, 320, 50)
b3 = pygame.Rect(WIDTH // 2 - 160, 340, 320, 50)

async def main():
    global current_game
    global t_pos, t_vel, t_hp, t_score, t_jumps, t_state, t_bullets, t_fire_cd
    global t_enemies, t_wave, t_wave_cd, t_pickups
    global ast_pos, ast_vel, ast_angle, ast_hp, ast_score, ast_state, ast_fire_cd
    global ast_missiles, ast_e_missiles, ast_asteroids
    global ast_e_pos, ast_e_vel, ast_e_angle, ast_e_state, ast_e_cd, ast_e_alive, ast_respawn
    global cc_player, cc_vel_x, cc_vel_y, cc_grounded, cc_won, cc_cupcakes

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: current_game = "MENU"
                elif current_game == "MENU":
                    if event.key == pygame.K_1: reset_terraria(); current_game = "TERRARIA"
                    elif event.key == pygame.K_2: reset_asteroids(); current_game = "ASTEROIDS"
                    elif event.key == pygame.K_3: reset_cupcake(); current_game = "CUPCAKE"
                elif current_game == "TERRARIA":
                    if event.key == pygame.K_r and t_state != "PLAY": reset_terraria()
                    elif event.key in (pygame.K_w, pygame.K_SPACE, pygame.K_UP) and t_state == "PLAY" and t_jumps > 0:
                        t_vel.y = -11.5; t_jumps -= 1
                elif current_game == "ASTEROIDS":
                    if event.key == pygame.K_r and ast_state != "PLAY": reset_asteroids()
                elif current_game == "CUPCAKE":
                    if event.key == pygame.K_r and cc_won: reset_cupcake()
            elif event.type == pygame.MOUSEBUTTONDOWN and current_game == "MENU":
                if b1.collidepoint(event.pos): reset_terraria(); current_game = "TERRARIA"
                elif b2.collidepoint(event.pos): reset_asteroids(); current_game = "ASTEROIDS"
                elif b3.collidepoint(event.pos): reset_cupcake(); current_game = "CUPCAKE"

        keys = pygame.key.get_pressed()
        mpos = pygame.Vector2(pygame.mouse.get_pos())
        m_pressed = pygame.mouse.get_pressed()

        if current_game == "MENU":
            screen.fill((12, 14, 22))
            title = font_big.render("ARCADE", True, (255, 255, 255))
            screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 110))
            mp = pygame.mouse.get_pos()
            for rect, txt in [(b1, "Terraria"), (b2, "Asteroids"), (b3, "Cupcake Collector")]:
                bg = (40, 50, 75) if rect.collidepoint(mp) else (24, 28, 42)
                pygame.draw.rect(screen, bg, rect, border_radius=8)
                pygame.draw.rect(screen, (80, 110, 170), rect, 2, border_radius=8)
                lbl = font.render(txt, True, (240, 240, 240))
                screen.blit(lbl, (rect.centerx - lbl.get_width() // 2, rect.centery - lbl.get_height() // 2))

        elif current_game == "TERRARIA":
            pc = t_pos + pygame.Vector2(10, 16)
            if t_state == "PLAY":
                mx = 0
                if keys[pygame.K_a] or keys[pygame.K_LEFT]: mx -= 1
                if keys[pygame.K_d] or keys[pygame.K_RIGHT]: mx += 1
                t_vel.x += mx * 1.4
                t_vel.x *= 0.82
                if abs(t_vel.x) > 6.5: t_vel.x = 6.5 if t_vel.x > 0 else -6.5
                t_vel.y += 0.65
                if t_vel.y > 13.0: t_vel.y = 13.0
                t_pos.x += t_vel.x
                if t_pos.x < 10: t_pos.x = 10
                if t_pos.x > WIDTH - 30: t_pos.x = WIDTH - 30
                pb = pygame.Rect(int(t_pos.x), int(t_pos.y), 20, 32)
                for pl in t_plats:
                    if pb.colliderect(pl):
                        if t_vel.x > 0: pb.right = pl.left
                        elif t_vel.x < 0: pb.left = pl.right
                        t_pos.x = pb.x; t_vel.x = 0
                t_pos.y += t_vel.y
                pb = pygame.Rect(int(t_pos.x), int(t_pos.y), 20, 32)
                for pl in t_plats:
                    if pb.colliderect(pl):
                        if t_vel.y > 0 and pb.bottom - t_vel.y <= pl.top + 10:
                            pb.bottom = pl.top; t_pos.y = pb.y; t_vel.y = 0; t_jumps = 2
                        elif t_vel.y < 0 and pb.top - t_vel.y >= pl.bottom - 10:
                            pb.top = pl.bottom; t_pos.y = pb.y; t_vel.y = 0
                pc = t_pos + pygame.Vector2(10, 16)
                if (m_pressed[0] or keys[pygame.K_f]) and t_fire_cd == 0:
                    aim = mpos - pc
                    if aim.length() > 0:
                        d = aim.normalize()
                        t_bullets.append({"pos": pygame.Vector2(pc), "vel": d * 14.0, "life": 45})
                        t_vel -= d * 0.7
                        t_fire_cd = 6
                if t_fire_cd > 0: t_fire_cd -= 1
                for b in t_bullets[:]:
                    b["pos"] += b["vel"]; b["life"] -= 1
                    if b["life"] <= 0 or not (-10 < b["pos"].x < WIDTH + 10 and -10 < b["pos"].y < HEIGHT + 10):
                        t_bullets.remove(b); continue
                    hit = False
                    for pl in t_plats:
                        if pl.collidepoint(int(b["pos"].x), int(b["pos"].y)): hit = True; break
                    if hit: t_bullets.remove(b); continue
                    for e in t_enemies:
                        if b["pos"].distance_to(e["pos"]) < e["r"]:
                            e["hp"] -= random.randint(15, 22)
                            e["vel"] += b["vel"].normalize() * 3.0
                            hit = True
                            if e["hp"] <= 0:
                                t_score += 50 + t_wave * 10
                                if random.random() < 0.3:
                                    t_pickups.append({"pos": pygame.Vector2(e["pos"]), "life": 300})
                                t_enemies.remove(e)
                            break
                    if hit and b in t_bullets: t_bullets.remove(b)
                for i, e in enumerate(t_enemies):
                    diff = pc - e["pos"]
                    dist = diff.length()
                    top = diff.normalize() if dist > 0 else pygame.Vector2(1, 0)
                    erad = math.radians(e["ang"])
                    efwd = pygame.Vector2(math.cos(erad), -math.sin(erad))
                    dot = efwd.dot(top)
                    if dist < 350 and dot > 0.4:
                        des = math.degrees(math.atan2(-top.y, top.x))
                        ad = (des - e["ang"] + 180) % 360 - 180
                        e["ang"] += ad * 0.12
                        e["vel"] += top * e["spd"] * 0.12
                    else:
                        e["ang"] = (e["ang"] + 1.2) % 360
                        e["vel"] += pygame.Vector2(random.uniform(-0.2, 0.2), random.uniform(-0.2, 0.2))
                    for j in range(i + 1, len(t_enemies)):
                        o = t_enemies[j]
                        sd = e["pos"].distance_to(o["pos"])
                        if 0 < sd < e["r"] + o["r"]:
                            push = (e["pos"] - o["pos"]).normalize() * 0.5
                            e["vel"] += push; o["vel"] -= push
                    e["vel"] *= 0.94
                    if e["vel"].length() > e["spd"] * 3: e["vel"].scale_to_length(e["spd"] * 3)
                    e["pos"] += e["vel"]
                    if e["pos"].distance_to(pc) < e["r"] + 12:
                        t_hp -= 12
                        kb = (pc - e["pos"])
                        if kb.length() > 0: kb = kb.normalize()
                        t_vel += kb * 7.0; e["vel"] -= kb * 5.0
                        if t_hp <= 0: t_state = "GAMEOVER"
                for pk in t_pickups[:]:
                    pk["life"] -= 1
                    if pk["life"] <= 0: t_pickups.remove(pk); continue
                    if pc.distance_to(pk["pos"]) < 24: t_hp = min(100, t_hp + 20); t_pickups.remove(pk)
                if len(t_enemies) == 0 and t_state == "PLAY":
                    t_wave_cd += 1
                    if t_wave_cd >= 90:
                        if t_wave >= 10: t_state = "WIN"
                        else: t_spawn_wave()
            screen.fill((14, 16, 26))
            for pl in t_plats:
                pygame.draw.rect(screen, (45, 120, 75), pl)
                pygame.draw.rect(screen, (80, 180, 110), pygame.Rect(pl.x, pl.y, pl.width, 4))
            for pk in t_pickups:
                px, py = int(pk["pos"].x), int(pk["pos"].y)
                pygame.draw.circle(screen, (40, 220, 80), (px, py), 8)
                pygame.draw.line(screen, (255, 255, 255), (px - 4, py), (px + 4, py), 2)
                pygame.draw.line(screen, (255, 255, 255), (px, py - 4), (px, py + 4), 2)
            for b in t_bullets:
                pygame.draw.circle(screen, (255, 240, 100), (int(b["pos"].x), int(b["pos"].y)), 3)
            for e in t_enemies:
                ex, ey = int(e["pos"].x), int(e["pos"].y)
                erad = math.radians(e["ang"])
                efwd = pygame.Vector2(math.cos(erad), -math.sin(erad))
                pygame.draw.circle(screen, (255, 255, 255), (ex, ey), e["r"])
                pygame.draw.circle(screen, (180, 20, 20), (ex, ey), e["r"], 2)
                pupil = e["pos"] + efwd * (e["r"] * 0.4)
                pcol = (255, 30, 30) if e["pos"].distance_to(pc) < 350 else (30, 80, 220)
                pygame.draw.circle(screen, pcol, (int(pupil.x), int(pupil.y)), int(e["r"] * 0.4))
                pygame.draw.circle(screen, (10, 10, 20), (int(pupil.x), int(pupil.y)), int(e["r"] * 0.2))
                hw, hpct = 28, max(0, e["hp"] / e["mhp"])
                pygame.draw.rect(screen, (40, 40, 40), (ex - hw // 2, ey - e["r"] - 10, hw, 3))
                pygame.draw.rect(screen, (220, 50, 50), (ex - hw // 2, ey - e["r"] - 10, int(hw * hpct), 3))
            if t_state == "PLAY":
                pr = pygame.Rect(int(t_pos.x), int(t_pos.y), 20, 32)
                pygame.draw.rect(screen, (50, 160, 240), pr)
                pygame.draw.rect(screen, (240, 240, 255), pr, 2)
                aim = (mpos - pc).normalize() if (mpos - pc).length() > 0 else pygame.Vector2(1, 0)
                pygame.draw.line(screen, (255, 200, 60), (int(pc.x), int(pc.y)),
                                 (int(pc.x + aim.x * 18), int(pc.y + aim.y * 18)), 2)
            pygame.draw.rect(screen, (30, 30, 40), (20, 20, 140, 12))
            hpw = int(140 * max(0, t_hp / 100))
            pygame.draw.rect(screen, (50, 220, 90) if t_hp > 30 else (240, 50, 50), (20, 20, hpw, 12))
            pygame.draw.rect(screen, (200, 200, 200), (20, 20, 140, 12), 1)
            screen.blit(font.render(f"HP: {max(0, t_hp)}", True, (255, 255, 255)), (170, 17))
            screen.blit(font.render(f"Wave {t_wave}/10", True, (255, 240, 100)), (WIDTH // 2 - 40, 17))
            screen.blit(font.render(f"Score: {t_score}", True, (200, 200, 200)), (WIDTH - 120, 17))
            if len(t_enemies) == 0 and t_state == "PLAY" and t_wave < 10:
                lbl = font_big.render(f"Wave {t_wave} Clear!", True, (60, 240, 120))
                screen.blit(lbl, (WIDTH // 2 - lbl.get_width() // 2, HEIGHT // 2 - 30))
            if t_state == "GAMEOVER":
                screen.blit(font_big.render("You Lost!", True, (240, 50, 50)), (WIDTH // 2 - 90, HEIGHT // 2 - 40))
                screen.blit(font.render(f"Wave {t_wave} | Score: {t_score}", True, (200, 200, 200)),
                             (WIDTH // 2 - 80, HEIGHT // 2 + 10))
                screen.blit(font.render("R to restart", True, (180, 180, 180)), (WIDTH // 2 - 50, HEIGHT // 2 + 35))
            elif t_state == "WIN":
                screen.blit(font_big.render("You Won!", True, (60, 240, 120)), (WIDTH // 2 - 90, HEIGHT // 2 - 40))
                screen.blit(font.render(f"Score: {t_score}", True, (255, 240, 100)), (WIDTH // 2 - 40, HEIGHT // 2 + 10))
                screen.blit(font.render("R to restart", True, (180, 180, 180)), (WIDTH // 2 - 50, HEIGHT // 2 + 35))

        elif current_game == "ASTEROIDS":
            is_thrust = False
            if ast_state == "PLAY":
                if keys[pygame.K_LEFT] or keys[pygame.K_a]: ast_angle += 4.5
                if keys[pygame.K_RIGHT] or keys[pygame.K_d]: ast_angle -= 4.5
                if keys[pygame.K_SPACE] and ast_fire_cd == 0:
                    rad = math.radians(ast_angle)
                    fwd = pygame.Vector2(math.cos(rad), -math.sin(rad))
                    ast_missiles.append({"pos": ast_pos + fwd * 24, "vel": fwd * 11.0 + ast_vel * 0.3, "radius": 4})
                    ast_fire_cd = 10
                if ast_fire_cd > 0: ast_fire_cd -= 1
                rad = math.radians(ast_angle)
                fwd = pygame.Vector2(math.cos(rad), -math.sin(rad))
                if keys[pygame.K_UP] or keys[pygame.K_w]: ast_vel += fwd * 0.22; is_thrust = True
                elif keys[pygame.K_DOWN] or keys[pygame.K_s]: ast_vel -= fwd * 0.11
                ast_vel *= 0.985
                if ast_vel.length() > 7.5: ast_vel.scale_to_length(7.5)
                ast_pos += ast_vel
                if ast_pos.x > WIDTH: ast_pos.x = 0
                elif ast_pos.x < 0: ast_pos.x = WIDTH
                if ast_pos.y > HEIGHT: ast_pos.y = 0
                elif ast_pos.y < 0: ast_pos.y = HEIGHT
                if ast_e_alive:
                    diff = ast_pos - ast_e_pos
                    dist = ast_e_pos.distance_to(ast_pos)
                    top = diff.normalize() if diff.length() > 0 else pygame.Vector2(1, 0)
                    erad = math.radians(ast_e_angle)
                    efwd = pygame.Vector2(math.cos(erad), -math.sin(erad))
                    dot = efwd.dot(top)
                    det = dist < 280 and dot > 0.65
                    ast_e_state = "ATTACK" if det else "PATROL"
                    if det:
                        des = math.degrees(math.atan2(-top.y, top.x))
                        ad = (des - ast_e_angle + 180) % 360 - 180
                        ast_e_angle += ad * 0.08
                        if dist > 120: ast_e_pos += efwd * 1.8
                        ast_e_cd += 1
                        if ast_e_cd >= 40:
                            ast_e_missiles.append({"pos": ast_e_pos + efwd * 22, "vel": top * 6.0, "radius": 4})
                            ast_e_cd = 0
                    else:
                        ast_e_angle = (ast_e_angle + 0.6) % 360
                        ast_e_pos += ast_e_vel
                        if ast_e_pos.x < 50 or ast_e_pos.x > WIDTH - 50: ast_e_vel.x *= -1
                        if ast_e_pos.y < 50 or ast_e_pos.y > HEIGHT - 50: ast_e_vel.y *= -1
                else:
                    ast_respawn -= 1
                    if ast_respawn <= 0:
                        ast_e_alive = True
                        ast_e_pos = pygame.Vector2(random.choice([80, WIDTH - 80]), random.choice([80, HEIGHT - 80]))
                for m in ast_missiles[:]:
                    m["pos"] += m["vel"]
                    if not (-10 < m["pos"].x < WIDTH + 10 and -10 < m["pos"].y < HEIGHT + 10): ast_missiles.remove(m)
                for em in ast_e_missiles[:]:
                    em["pos"] += em["vel"]
                    if not (-10 < em["pos"].x < WIDTH + 10 and -10 < em["pos"].y < HEIGHT + 10):
                        ast_e_missiles.remove(em)
                    elif em["pos"].distance_to(ast_pos) < 18:
                        ast_hp -= 15; ast_e_missiles.remove(em)
                        if ast_hp <= 0: ast_state = "GAMEOVER"
                for a in ast_asteroids:
                    a["pos"] += a["vel"]
                    if a["pos"].x < -40: a["pos"].x = WIDTH + 40
                    elif a["pos"].x > WIDTH + 40: a["pos"].x = -40
                    if a["pos"].y < -40: a["pos"].y = HEIGHT + 40
                    elif a["pos"].y > HEIGHT + 40: a["pos"].y = -40
                    if a["pos"].distance_to(ast_pos) < a["radius"] + 14:
                        ast_hp -= 25; ast_vel += (ast_pos - a["pos"]).normalize() * 4.0
                        if ast_hp <= 0: ast_state = "GAMEOVER"
                for m in ast_missiles[:]:
                    hit = False
                    for a in ast_asteroids[:]:
                        if m["pos"].distance_to(a["pos"]) < m["radius"] + a["radius"]:
                            ast_asteroids.remove(a); spawn_ast(); ast_score += 20; hit = True; break
                    if not hit and ast_e_alive and m["pos"].distance_to(ast_e_pos) < 22:
                        ast_e_alive = False; ast_respawn = 240; ast_score += 100; hit = True
                    if hit and m in ast_missiles: ast_missiles.remove(m)
                if ast_score >= 600: ast_state = "WIN"
            screen.fill((10, 12, 18))
            if ast_e_alive and ast_state == "PLAY":
                pygame.draw.circle(screen, (40, 45, 60), (int(ast_e_pos.x), int(ast_e_pos.y)), 280, 1)
                e_col = (255, 60, 60) if ast_e_state == "ATTACK" else (220, 220, 220)
                erad = math.radians(ast_e_angle)
                efwd = pygame.Vector2(math.cos(erad), -math.sin(erad))
                ep1 = ast_e_pos + efwd * 20
                ep2 = ast_e_pos + efwd.rotate(135) * 15
                ep3 = ast_e_pos + efwd.rotate(-135) * 15
                pygame.draw.polygon(screen, e_col, [ep1, ep2, ep3])
                pygame.draw.polygon(screen, (255, 255, 255), [ep1, ep2, ep3], 1)
            for a in ast_asteroids:
                pygame.draw.circle(screen, (135, 130, 120), (int(a["pos"].x), int(a["pos"].y)), a["radius"])
                pygame.draw.circle(screen, (75, 70, 65), (int(a["pos"].x), int(a["pos"].y)), a["radius"], 2)
            for m in ast_missiles:
                pygame.draw.circle(screen, (255, 230, 80), (int(m["pos"].x), int(m["pos"].y)), 4)
            for em in ast_e_missiles:
                pygame.draw.circle(screen, (255, 60, 60), (int(em["pos"].x), int(em["pos"].y)), 4)
            if ast_state == "PLAY":
                rad = math.radians(ast_angle)
                fwd = pygame.Vector2(math.cos(rad), -math.sin(rad))
                p1 = ast_pos + fwd * 22
                p2 = ast_pos + fwd.rotate(140) * 16
                p3 = ast_pos + fwd.rotate(-140) * 16
                if is_thrust:
                    flen = random.uniform(14, 22)
                    pygame.draw.polygon(screen, (255, 120, 20),
                        [ast_pos - fwd * flen, ast_pos + fwd.rotate(140) * 8, ast_pos + fwd.rotate(-140) * 8])
                pygame.draw.polygon(screen, (0, 220, 255), [p1, p2, p3])
                pygame.draw.polygon(screen, (255, 255, 255), [p1, p2, p3], 2)
                hp_pct = max(0, ast_hp / 100)
                pygame.draw.rect(screen, (40, 40, 40), (20, 20, 140, 14))
                pygame.draw.rect(screen, (50, 230, 90) if hp_pct > 0.35 else (230, 50, 50),
                                 (20, 20, int(140 * hp_pct), 14))
                pygame.draw.rect(screen, (255, 255, 255), (20, 20, 140, 14), 1)
                screen.blit(font.render(f"HP: {max(0, ast_hp)}   Score: {ast_score}", True, (255, 255, 255)),
                             (170, 18))
            elif ast_state == "GAMEOVER":
                screen.blit(font_big.render("You Lost!", True, (255, 60, 60)), (WIDTH // 2 - 80, HEIGHT // 2 - 30))
                screen.blit(font.render("R to restart", True, (220, 220, 220)), (WIDTH // 2 - 50, HEIGHT // 2 + 15))
            elif ast_state == "WIN":
                screen.blit(font_big.render("You Won!", True, (60, 255, 120)), (WIDTH // 2 - 80, HEIGHT // 2 - 30))
                screen.blit(font.render("R to restart", True, (220, 220, 220)), (WIDTH // 2 - 50, HEIGHT // 2 + 15))

        elif current_game == "CUPCAKE":
            cc_vel_x = 0
            if keys[pygame.K_LEFT] or keys[pygame.K_a]: cc_vel_x = -6
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]: cc_vel_x = 6
            if (keys[pygame.K_UP] or keys[pygame.K_w] or keys[pygame.K_SPACE]) and cc_grounded:
                cc_vel_y = -15; cc_grounded = False
                if jump_snd: jump_snd.play()
            cc_vel_y += 0.8
            cc_player.x += cc_vel_x
            if cc_player.left < 0: cc_player.left = 0
            if cc_player.right > WIDTH: cc_player.right = WIDTH
            cc_player.y += cc_vel_y
            cc_grounded = False
            for p in cc_plats:
                if cc_player.colliderect(p):
                    if cc_vel_y > 0 and cc_player.bottom - cc_vel_y <= p.top + 6:
                        cc_player.bottom = p.top; cc_vel_y = 0; cc_grounded = True
                    elif cc_vel_y < 0 and cc_player.top - cc_vel_y >= p.bottom - 6:
                        cc_player.top = p.bottom; cc_vel_y = 0
            if cc_player.bottom > 550: cc_player.bottom = 550; cc_vel_y = 0; cc_grounded = True
            for c in cc_cupcakes[:]:
                if cc_player.colliderect(c):
                    cc_cupcakes.remove(c)
                    if collect_snd: collect_snd.play()
                    if len(cc_cupcakes) == 0 and not cc_won:
                        cc_won = True
                        if win_snd: win_snd.play()
            screen.fill((25, 25, 35))
            for p in cc_plats:
                pygame.draw.rect(screen, (70, 130, 240), p, border_radius=6)
                pygame.draw.rect(screen, (100, 160, 255), p, 2, border_radius=6)
            for c in cc_cupcakes:
                if cupcake_img: screen.blit(cupcake_img, c)
                else: pygame.draw.circle(screen, (255, 120, 180), c.center, 14)
            if player_img: screen.blit(player_img, cc_player)
            else: pygame.draw.rect(screen, (240, 60, 60), cc_player, border_radius=4)
            screen.blit(font.render(f"Cupcakes: {len(cc_cupcakes)}", True, (255, 235, 120)), (20, 20))
            if cc_won:
                screen.blit(font_big.render("You Won!", True, (255, 215, 0)), (WIDTH // 2 - 80, HEIGHT // 2 - 30))
                screen.blit(font.render("R to restart", True, (255, 255, 255)), (WIDTH // 2 - 50, HEIGHT // 2 + 15))

        pygame.display.flip()
        clock.tick(60)
        await asyncio.sleep(0)

    pygame.quit()
    sys.exit()

asyncio.run(main())
