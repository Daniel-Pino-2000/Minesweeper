import pygame
import random
import json
import os
from datetime import datetime
from enum import Enum

# Initialize Pygame
pygame.init()

class CellState(Enum):
    HIDDEN = 0
    REVEALED = 1
    FLAGGED = 2
    MINE_EXPLODED = 3

class GameState(Enum):
    PLAYING = 0
    WON = 1
    LOST = 2

class Colors:
    # Modern color scheme
    BACKGROUND = (45, 52, 65)
    CELL_HIDDEN = (108, 117, 125)
    CELL_REVEALED = (248, 249, 250)
    CELL_MINE = (220, 53, 69)
    CELL_HOVER = (134, 142, 150)
    BORDER = (73, 80, 87)
    TEXT_PRIMARY = (33, 37, 41)
    TEXT_SECONDARY = (108, 117, 125)
    FLAG = (255, 193, 7)
    MINE = (52, 58, 64)
    HEADER_BG = (52, 58, 64)
    BUTTON_BG = (0, 123, 255)
    BUTTON_HOVER = (0, 86, 179)
    SUCCESS = (40, 167, 69)
    
    # Number colors
    NUMBERS = {
        1: (0, 123, 255),
        2: (40, 167, 69),
        3: (220, 53, 69),
        4: (102, 16, 242),
        5: (255, 193, 7),
        6: (255, 108, 180),
        7: (0, 0, 0),
        8: (108, 117, 125)
    }

class ModernMinesweeper:
    def __init__(self):
        self.SAVE_FILE = "minesweeper_save.json"
        self.cell_size = 40
        self.header_height = 100
        self.margin = 20
        
        # Game state
        self.reset_game_state()
        
        # Fonts
        self.font_large = pygame.font.Font(None, 32)
        self.font_medium = pygame.font.Font(None, 24)
        self.font_small = pygame.font.Font(None, 20)
        
        # Animation variables
        self.hover_cell = None
        self.animation_time = 0
        self.reveal_animations = {}
        
        self.show_menu = True
        self.clock = pygame.time.Clock()
        
    def reset_game_state(self):
        self.rows = 9
        self.cols = 9
        self.mines = 10
        self.board = []
        self.cell_states = []
        self.mine_positions = set()
        self.game_state = GameState.PLAYING
        self.flags_placed = 0
        self.cells_revealed = 0
        self.start_time = None
        self.end_time = None
        
    def create_window(self):
        window_width = self.cols * self.cell_size + 2 * self.margin
        window_height = self.rows * self.cell_size + self.header_height + 2 * self.margin
        self.screen = pygame.display.set_mode((window_width, window_height))
        pygame.display.set_caption("Modern Minesweeper")
        
    def initialize_game(self, difficulty):
        if difficulty == "easy":
            self.rows, self.cols, self.mines = 9, 9, 10
        elif difficulty == "medium":
            self.rows, self.cols, self.mines = 16, 16, 40
        elif difficulty == "hard":
            self.rows, self.cols, self.mines = 16, 30, 99
            
        self.create_window()
        self.board = [[0 for _ in range(self.cols)] for _ in range(self.rows)]
        self.cell_states = [[CellState.HIDDEN for _ in range(self.cols)] for _ in range(self.rows)]
        self.mine_positions = set()
        self.game_state = GameState.PLAYING
        self.flags_placed = 0
        self.cells_revealed = 0
        self.start_time = None
        self.end_time = None
        self.show_menu = False
        
    def place_mines(self, first_click_row, first_click_col):
        mines_placed = 0
        while mines_placed < self.mines:
            row = random.randint(0, self.rows - 1)
            col = random.randint(0, self.cols - 1)
            
            # Don't place mine on first click or if already has mine
            if (row, col) not in self.mine_positions and (row, col) != (first_click_row, first_click_col):
                self.mine_positions.add((row, col))
                self.board[row][col] = -1  # -1 represents mine
                mines_placed += 1
                
        self.calculate_numbers()
        
    def calculate_numbers(self):
        for row in range(self.rows):
            for col in range(self.cols):
                if self.board[row][col] != -1:  # Not a mine
                    count = 0
                    for dr in [-1, 0, 1]:
                        for dc in [-1, 0, 1]:
                            if dr == 0 and dc == 0:
                                continue
                            new_row, new_col = row + dr, col + dc
                            if (0 <= new_row < self.rows and 0 <= new_col < self.cols 
                                and self.board[new_row][new_col] == -1):
                                count += 1
                    self.board[row][col] = count
                    
    def get_cell_at_pos(self, pos):
        x, y = pos
        if y < self.header_height + self.margin:
            return None
        
        col = (x - self.margin) // self.cell_size
        row = (y - self.header_height - self.margin) // self.cell_size
        
        if 0 <= row < self.rows and 0 <= col < self.cols:
            return row, col
        return None
        
    def reveal_cell(self, row, col):
        if self.cell_states[row][col] != CellState.HIDDEN:
            return
            
        if self.start_time is None:
            self.start_time = pygame.time.get_ticks()
            
        self.cell_states[row][col] = CellState.REVEALED
        self.cells_revealed += 1
        
        # Add reveal animation
        self.reveal_animations[(row, col)] = pygame.time.get_ticks()
        
        if self.board[row][col] == -1:  # Hit a mine
            self.cell_states[row][col] = CellState.MINE_EXPLODED
            self.game_state = GameState.LOST
            self.end_time = pygame.time.get_ticks()
            self.reveal_all_mines()
            return
            
        if self.board[row][col] == 0:  # Empty cell, reveal neighbors
            self.reveal_neighbors(row, col)
            
        # Check win condition
        if self.cells_revealed + self.mines == self.rows * self.cols:
            self.game_state = GameState.WON
            self.end_time = pygame.time.get_ticks()
            
    def reveal_neighbors(self, row, col):
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                new_row, new_col = row + dr, col + dc
                if (0 <= new_row < self.rows and 0 <= new_col < self.cols 
                    and self.cell_states[new_row][new_col] == CellState.HIDDEN):
                    self.reveal_cell(new_row, new_col)
                    
    def reveal_all_mines(self):
        for row, col in self.mine_positions:
            if self.cell_states[row][col] != CellState.MINE_EXPLODED:
                self.cell_states[row][col] = CellState.REVEALED
                
    def toggle_flag(self, row, col):
        if self.cell_states[row][col] == CellState.HIDDEN:
            self.cell_states[row][col] = CellState.FLAGGED
            self.flags_placed += 1
        elif self.cell_states[row][col] == CellState.FLAGGED:
            self.cell_states[row][col] = CellState.HIDDEN
            self.flags_placed -= 1
            
    def draw_menu(self):
        self.screen.fill(Colors.BACKGROUND)
        
        # Title
        title = self.font_large.render("MINESWEEPER", True, Colors.CELL_REVEALED)
        title_rect = title.get_rect(center=(self.screen.get_width()//2, 100))
        self.screen.blit(title, title_rect)
        
        # Buttons
        button_width, button_height = 200, 50
        button_spacing = 70
        start_y = 200
        
        buttons = [
            ("Easy (9x9, 10 mines)", "easy"),
            ("Medium (16x16, 40 mines)", "medium"),
            ("Hard (16x30, 99 mines)", "hard"),
            ("Load Game", "load")
        ]
        
        mouse_pos = pygame.mouse.get_pos()
        self.menu_buttons = {}
        
        for i, (text, action) in enumerate(buttons):
            y = start_y + i * button_spacing
            button_rect = pygame.Rect(
                self.screen.get_width()//2 - button_width//2, 
                y, 
                button_width, 
                button_height
            )
            
            # Button hover effect
            color = Colors.BUTTON_HOVER if button_rect.collidepoint(mouse_pos) else Colors.BUTTON_BG
            pygame.draw.rect(self.screen, color, button_rect, border_radius=8)
            pygame.draw.rect(self.screen, Colors.BORDER, button_rect, 2, border_radius=8)
            
            # Button text
            button_text = self.font_small.render(text, True, Colors.CELL_REVEALED)
            text_rect = button_text.get_rect(center=button_rect.center)
            self.screen.blit(button_text, text_rect)
            
            self.menu_buttons[action] = button_rect
            
    def draw_header(self):
        import math  # Import math module for calculations
        
        # Header background
        header_rect = pygame.Rect(0, 0, self.screen.get_width(), self.header_height)
        pygame.draw.rect(self.screen, Colors.HEADER_BG, header_rect)
        
        # Mines remaining
        mines_remaining = max(0, self.mines - self.flags_placed)
        mines_text = self.font_medium.render(f"Mines: {mines_remaining:03d}", True, Colors.CELL_REVEALED)
        self.screen.blit(mines_text, (20, 20))
        
        # Timer
        if self.start_time:
            if self.end_time:
                elapsed = (self.end_time - self.start_time) // 1000
            else:
                elapsed = (pygame.time.get_ticks() - self.start_time) // 1000
            timer_text = self.font_medium.render(f"Time: {elapsed:03d}", True, Colors.CELL_REVEALED)
            timer_rect = timer_text.get_rect(topright=(self.screen.get_width() - 20, 20))
            self.screen.blit(timer_text, timer_rect)
        
        # Status/Reset button - draw stunning emoji faces
        button_rect = pygame.Rect(self.screen.get_width()//2 - 25, 10, 50, 50)
        mouse_pos = pygame.mouse.get_pos()
        button_color = Colors.BUTTON_HOVER if button_rect.collidepoint(mouse_pos) else Colors.BUTTON_BG
        pygame.draw.rect(self.screen, button_color, button_rect, border_radius=15)
        pygame.draw.rect(self.screen, Colors.BORDER, button_rect, 2, border_radius=15)
        
        # Perfect emoji face design
        center = button_rect.center
        face_radius = 22
        
        # Premium emoji face with perfect gradients
        # Multiple shadow layers for depth
        pygame.draw.circle(self.screen, (220, 180, 80), (center[0] + 2, center[1] + 2), face_radius + 1)  # Outer shadow
        pygame.draw.circle(self.screen, (255, 223, 0), center, face_radius)  # Perfect emoji yellow
        
        # Face highlight for 3D depth
        highlight_center = (center[0] - 4, center[1] - 4)
        pygame.draw.circle(self.screen, (255, 240, 100), highlight_center, face_radius // 2, 0)
        
        # Face outline
        pygame.draw.circle(self.screen, (200, 160, 0), center, face_radius, 2)
        
        if self.game_state == GameState.WON:
            # 🤩 Amazing star-struck victory face
            
            # Star-struck sparkling eyes
            # Left star eye
            star_size = 4
            left_center = (center[0] - 8, center[1] - 6)
            
            # Draw beautiful 5-pointed star
            star_points_left = []
            for i in range(10):  # 5 points, 2 coordinates each
                angle = (i * math.pi) / 5 - math.pi/2  # Start from top
                if i % 2 == 0:  # Outer points
                    radius = star_size
                else:  # Inner points
                    radius = star_size * 0.4
                x = left_center[0] + radius * math.cos(angle)
                y = left_center[1] + radius * math.sin(angle)
                star_points_left.append((x, y))
            
            pygame.draw.polygon(self.screen, (255, 215, 0), star_points_left)  # Gold star
            pygame.draw.polygon(self.screen, (255, 255, 100), star_points_left, 1)  # Bright outline
            
            # Right star eye
            right_center = (center[0] + 8, center[1] - 6)
            star_points_right = []
            for i in range(10):
                angle = (i * math.pi) / 5 - math.pi/2
                if i % 2 == 0:
                    radius = star_size
                else:
                    radius = star_size * 0.4
                x = right_center[0] + radius * math.cos(angle)
                y = right_center[1] + radius * math.sin(angle)
                star_points_right.append((x, y))
            
            pygame.draw.polygon(self.screen, (255, 215, 0), star_points_right)  # Gold star
            pygame.draw.polygon(self.screen, (255, 255, 100), star_points_right, 1)  # Bright outline
            
            # Huge excited smile - perfectly curved
            smile_points = []
            smile_width = 18
            smile_height = 8
            for i in range(25):  # More points for smoother curve
                t = i / 24.0  # 0 to 1
                angle = math.pi * t  # 0 to π
                x = center[0] - smile_width//2 + smile_width * t
                y = center[1] + 4 + smile_height * math.sin(angle)
                smile_points.append((x, y))
            
            # Draw thick, vibrant smile
            if len(smile_points) > 2:
                pygame.draw.lines(self.screen, (255, 50, 100), False, smile_points, 4)
                # Add inner highlight for depth
                inner_smile = [(x, y-1) for x, y in smile_points[2:-2]]
                pygame.draw.lines(self.screen, (255, 150, 200), False, inner_smile, 2)
            
            # Add sparkle effects around the face
            sparkles = [
                (center[0] - 18, center[1] - 12),
                (center[0] + 18, center[1] - 8),
                (center[0] - 15, center[1] + 8),
                (center[0] + 16, center[1] + 12)
            ]
            
            for sparkle_pos in sparkles:
                # Small 4-pointed sparkle
                pygame.draw.line(self.screen, (255, 255, 255), 
                               (sparkle_pos[0] - 3, sparkle_pos[1]), 
                               (sparkle_pos[0] + 3, sparkle_pos[1]), 2)
                pygame.draw.line(self.screen, (255, 255, 255), 
                               (sparkle_pos[0], sparkle_pos[1] - 3), 
                               (sparkle_pos[0], sparkle_pos[1] + 3), 2)
            
        elif self.game_state == GameState.LOST:
            # 😵 Perfect dizzy/dead face
            # Spiral dizzy eyes
            import math
            
            # Left spiral eye
            for i in range(15):
                angle = i * 0.8
                radius = i * 0.4
                x = center[0] - 8 + math.cos(angle) * radius
                y = center[1] - 6 + math.sin(angle) * radius
                pygame.draw.circle(self.screen, (180, 50, 50), (int(x), int(y)), max(1, 3 - i//5))
            
            # Right spiral eye  
            for i in range(15):
                angle = i * 0.8
                radius = i * 0.4
                x = center[0] + 8 + math.cos(angle) * radius
                y = center[1] - 6 + math.sin(angle) * radius
                pygame.draw.circle(self.screen, (180, 50, 50), (int(x), int(y)), max(1, 3 - i//5))
            
            # Perfect "O" shocked mouth
            mouth_rect = pygame.Rect(center[0] - 6, center[1] + 6, 12, 10)
            pygame.draw.ellipse(self.screen, (50, 50, 50), mouth_rect)
            pygame.draw.ellipse(self.screen, (30, 30, 30), (center[0] - 5, center[1] + 7, 10, 8))
            pygame.draw.ellipse(self.screen, (100, 100, 100), mouth_rect, 2)
            
        else:
            # 😊 Perfect happy emoji face
            
            # Beautiful realistic eyes
            # Left eye
            eye_white_left = pygame.Rect(center[0] - 12, center[1] - 8, 8, 6)
            pygame.draw.ellipse(self.screen, (255, 255, 255), eye_white_left)
            pygame.draw.ellipse(self.screen, (200, 200, 200), eye_white_left, 1)
            
            # Left iris and pupil
            pygame.draw.circle(self.screen, (70, 130, 180), (center[0] - 8, center[1] - 5), 3)  # Blue iris
            pygame.draw.circle(self.screen, (30, 30, 30), (center[0] - 8, center[1] - 5), 2)     # Pupil
            pygame.draw.circle(self.screen, (255, 255, 255), (center[0] - 9, center[1] - 6), 1)  # Eye shine
            
            # Right eye
            eye_white_right = pygame.Rect(center[0] + 4, center[1] - 8, 8, 6)
            pygame.draw.ellipse(self.screen, (255, 255, 255), eye_white_right)
            pygame.draw.ellipse(self.screen, (200, 200, 200), eye_white_right, 1)
            
            # Right iris and pupil
            pygame.draw.circle(self.screen, (70, 130, 180), (center[0] + 8, center[1] - 5), 3)   # Blue iris
            pygame.draw.circle(self.screen, (30, 30, 30), (center[0] + 8, center[1] - 5), 2)     # Pupil
            pygame.draw.circle(self.screen, (255, 255, 255), (center[0] + 7, center[1] - 6), 1)  # Eye shine
            
            # Perfect curved smile
            smile_points = []
            for i in range(21):
                angle = 3.14159 * i / 20  # 0 to π
                x = center[0] - 10 + 20 * i / 20
                y = center[1] + 6 + 6 * math.sin(angle)
                smile_points.append((x, y))
            
            if len(smile_points) > 2:
                pygame.draw.lines(self.screen, (220, 80, 80), False, smile_points, 3)
                
            # Add subtle pink blush on cheeks
            pygame.draw.circle(self.screen, (255, 200, 200), (center[0] - 16, center[1] + 2), 4, 0)
            pygame.draw.circle(self.screen, (255, 180, 180), (center[0] - 16, center[1] + 2), 3, 0)
            pygame.draw.circle(self.screen, (255, 200, 200), (center[0] + 16, center[1] + 2), 4, 0)
            pygame.draw.circle(self.screen, (255, 180, 180), (center[0] + 16, center[1] + 2), 3, 0)
        
        self.reset_button = button_rect
        
        # Menu button
        menu_text = self.font_small.render("Menu", True, Colors.CELL_REVEALED)
        menu_rect = pygame.Rect(self.screen.get_width()//2 - 30, 70, 60, 25)
        menu_color = Colors.BUTTON_HOVER if menu_rect.collidepoint(mouse_pos) else Colors.BUTTON_BG
        pygame.draw.rect(self.screen, menu_color, menu_rect, border_radius=4)
        menu_text_rect = menu_text.get_rect(center=menu_rect.center)
        self.screen.blit(menu_text, menu_text_rect)
        self.menu_button = menu_rect
        
    def draw_cell(self, row, col, x, y):
        cell_rect = pygame.Rect(x, y, self.cell_size, self.cell_size)
        state = self.cell_states[row][col]
        
        # Cell background - Fixed: flagged cells keep hidden appearance
        if state == CellState.HIDDEN or state == CellState.FLAGGED:
            color = Colors.CELL_HOVER if self.hover_cell == (row, col) else Colors.CELL_HIDDEN
        elif state == CellState.MINE_EXPLODED:
            color = Colors.CELL_MINE
        else:
            color = Colors.CELL_REVEALED
            
        pygame.draw.rect(self.screen, color, cell_rect)
        pygame.draw.rect(self.screen, Colors.BORDER, cell_rect, 1)
        
        # Cell content
        if state == CellState.FLAGGED:
            # Draw flag with pole
            pole_x = x + self.cell_size//4
            flag_top = y + self.cell_size//6
            flag_bottom = y + 5*self.cell_size//6
            
            # Flag pole
            pygame.draw.line(self.screen, Colors.TEXT_PRIMARY, 
                           (pole_x, flag_top),
                           (pole_x, flag_bottom), 2)
            
            # Flag triangle
            flag_points = [
                (pole_x, flag_top),
                (pole_x + self.cell_size//2, flag_top + self.cell_size//6),
                (pole_x, flag_top + self.cell_size//3)
            ]
            pygame.draw.polygon(self.screen, Colors.FLAG, flag_points)
            pygame.draw.polygon(self.screen, (200, 150, 0), flag_points, 1)  # Flag outline
            
        elif state == CellState.REVEALED or state == CellState.MINE_EXPLODED:
            if self.board[row][col] == -1:  # Mine
                center = (x + self.cell_size//2, y + self.cell_size//2)
                pygame.draw.circle(self.screen, Colors.MINE, center, self.cell_size//4)
                # Mine spikes
                for angle in range(0, 360, 45):
                    import math
                    end_x = center[0] + math.cos(math.radians(angle)) * (self.cell_size//3)
                    end_y = center[1] + math.sin(math.radians(angle)) * (self.cell_size//3)
                    pygame.draw.line(self.screen, Colors.MINE, center, (end_x, end_y), 2)
                    
            elif self.board[row][col] > 0:  # Number
                number = str(self.board[row][col])
                color = Colors.NUMBERS.get(self.board[row][col], Colors.TEXT_PRIMARY)
                text_surface = self.font_medium.render(number, True, color)
                text_rect = text_surface.get_rect(center=(x + self.cell_size//2, y + self.cell_size//2))
                self.screen.blit(text_surface, text_rect)
                
        # Reveal animation
        if (row, col) in self.reveal_animations:
            animation_start = self.reveal_animations[(row, col)]
            elapsed = pygame.time.get_ticks() - animation_start
            if elapsed < 200:  # 200ms animation
                progress = elapsed / 200
                overlay_alpha = int(255 * (1 - progress))
                overlay = pygame.Surface((self.cell_size, self.cell_size))
                overlay.set_alpha(overlay_alpha)
                overlay.fill(Colors.CELL_HIDDEN)
                self.screen.blit(overlay, (x, y))
            else:
                del self.reveal_animations[(row, col)]
                
    def draw_game(self):
        self.screen.fill(Colors.BACKGROUND)
        self.draw_header()
        
        # Draw grid
        for row in range(self.rows):
            for col in range(self.cols):
                x = self.margin + col * self.cell_size
                y = self.header_height + self.margin + row * self.cell_size
                self.draw_cell(row, col, x, y)
                
        # Game over overlay
        if self.game_state != GameState.PLAYING:
            overlay = pygame.Surface(self.screen.get_size())
            overlay.set_alpha(128)
            overlay.fill((0, 0, 0))
            self.screen.blit(overlay, (0, 0))
            
            # Draw custom game over graphics
            center_x = self.screen.get_width() // 2
            center_y = self.screen.get_height() // 2
            
            if self.game_state == GameState.WON:
                # Draw trophy icon
                trophy_color = (255, 215, 0)  # Gold
                trophy_base = (218, 165, 32)  # Dark gold
                
                # Trophy cup
                cup_rect = pygame.Rect(center_x - 30, center_y - 60, 60, 40)
                pygame.draw.ellipse(self.screen, trophy_color, cup_rect)
                pygame.draw.ellipse(self.screen, trophy_base, cup_rect, 3)
                
                # Trophy handles
                pygame.draw.arc(self.screen, trophy_base, (center_x - 45, center_y - 50, 20, 30), 1.57, 4.71, 4)
                pygame.draw.arc(self.screen, trophy_base, (center_x + 25, center_y - 50, 20, 30), 4.71, 1.57, 4)
                
                # Trophy base
                base_rect = pygame.Rect(center_x - 20, center_y - 20, 40, 15)
                pygame.draw.rect(self.screen, trophy_base, base_rect, border_radius=3)
                
                # Trophy stem
                stem_rect = pygame.Rect(center_x - 5, center_y - 30, 10, 20)
                pygame.draw.rect(self.screen, trophy_base, stem_rect)
                
                text = "YOU WON!"
                color = Colors.SUCCESS
                
            else:
                # Draw explosion/bomb icon
                explosion_color = (255, 69, 0)  # Red-orange
                
                # Main explosion circle
                pygame.draw.circle(self.screen, explosion_color, (center_x, center_y - 20), 25)
                pygame.draw.circle(self.screen, (255, 140, 0), (center_x, center_y - 20), 20)
                pygame.draw.circle(self.screen, (255, 215, 0), (center_x, center_y - 20), 15)
                
                # Explosion spikes
                spike_length = 35
                for angle in range(0, 360, 30):
                    import math
                    end_x = center_x + math.cos(math.radians(angle)) * spike_length
                    end_y = (center_y - 20) + math.sin(math.radians(angle)) * spike_length
                    start_x = center_x + math.cos(math.radians(angle)) * 20
                    start_y = (center_y - 20) + math.sin(math.radians(angle)) * 20
                    pygame.draw.line(self.screen, explosion_color, (start_x, start_y), (end_x, end_y), 4)
                
                text = "GAME OVER"
                color = Colors.CELL_MINE
                
            game_over_text = self.font_large.render(text, True, color)
            text_rect = game_over_text.get_rect(center=(center_x, center_y + 40))
            self.screen.blit(game_over_text, text_rect)
            
    def handle_click(self, pos, button):
        if self.game_state != GameState.PLAYING:
            return
            
        cell = self.get_cell_at_pos(pos)
        if cell is None:
            return
            
        row, col = cell
        
        if button == 1:  # Left click
            if self.cell_states[row][col] == CellState.HIDDEN:
                if not self.mine_positions:  # First click
                    self.place_mines(row, col)
                self.reveal_cell(row, col)
                
        elif button == 3:  # Right click
            if self.cell_states[row][col] in [CellState.HIDDEN, CellState.FLAGGED]:
                self.toggle_flag(row, col)
                
    def save_game(self):
        if self.game_state == GameState.PLAYING and self.start_time:
            game_data = {
                'rows': self.rows,
                'cols': self.cols,
                'mines': self.mines,
                'board': self.board,
                'cell_states': [[state.value for state in row] for row in self.cell_states],
                'mine_positions': list(self.mine_positions),
                'flags_placed': self.flags_placed,
                'cells_revealed': self.cells_revealed,
                'start_time': self.start_time,
                'timestamp': datetime.now().isoformat()
            }
            
            try:
                with open(self.SAVE_FILE, 'w') as f:
                    json.dump(game_data, f)
            except Exception as e:
                print(f"Could not save game: {e}")
                
    def load_game(self):
        try:
            with open(self.SAVE_FILE, 'r') as f:
                game_data = json.load(f)
                
            self.rows = game_data['rows']
            self.cols = game_data['cols']
            self.mines = game_data['mines']
            self.board = game_data['board']
            self.cell_states = [[CellState(state) for state in row] for row in game_data['cell_states']]
            self.mine_positions = set(tuple(pos) for pos in game_data['mine_positions'])
            self.flags_placed = game_data['flags_placed']
            self.cells_revealed = game_data['cells_revealed']
            self.start_time = game_data['start_time']
            
            self.create_window()
            self.game_state = GameState.PLAYING
            self.show_menu = False
            return True
            
        except Exception as e:
            print(f"Could not load game: {e}")
            return False
            
    def run(self):
        # Create initial window for menu
        self.screen = pygame.display.set_mode((600, 500))
        pygame.display.set_caption("Modern Minesweeper")
        
        running = True
        while running:
            self.animation_time += self.clock.get_time()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    if not self.show_menu:
                        self.save_game()
                    running = False
                    
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if not self.show_menu:
                            self.save_game()
                        self.show_menu = True
                        self.screen = pygame.display.set_mode((600, 500))
                        
                elif event.type == pygame.MOUSEMOTION:
                    if not self.show_menu:
                        cell = self.get_cell_at_pos(event.pos)
                        self.hover_cell = cell
                        
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if self.show_menu:
                        for action, rect in self.menu_buttons.items():
                            if rect.collidepoint(event.pos):
                                if action == "load":
                                    if not self.load_game():
                                        continue
                                else:
                                    self.initialize_game(action)
                                break
                    else:
                        # Check UI buttons
                        if hasattr(self, 'reset_button') and self.reset_button.collidepoint(event.pos):
                            difficulty = "easy" if self.mines == 10 else "medium" if self.mines == 40 else "hard"
                            self.initialize_game(difficulty)
                        elif hasattr(self, 'menu_button') and self.menu_button.collidepoint(event.pos):
                            self.save_game()
                            self.show_menu = True
                            self.screen = pygame.display.set_mode((600, 500))
                        else:
                            self.handle_click(event.pos, event.button)
                            
            # Draw
            if self.show_menu:
                self.draw_menu()
            else:
                self.draw_game()
                
            pygame.display.flip()
            self.clock.tick(60)
            
        pygame.quit()

if __name__ == "__main__":
    game = ModernMinesweeper()
    game.run()