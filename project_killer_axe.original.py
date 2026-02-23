from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import random
import math
import time

# Constants
WIDTH, HEIGHT = 800, 600
VILLAGER_RADIUS = 15
STONE_RADIUS = 10
FPS = 60
STONE_THROW_DELAY = 3
START_DELAY = 5
VILLAGER_GENERATION_DELAY = 5

# Global variables
villagers = []
axe = None
stones = []
key_state = {}
game_start_time = None
score = 0
last_villager_generation_time = None
game_paused = False
button_size = 15
restart_pos = (WIDTH - 150, HEIGHT - 30)  # Restart symbol position
pause_pos = (WIDTH - 100, HEIGHT - 30)    # Pause symbol position
end_pos = (WIDTH - 50, HEIGHT - 30)       # End symbol position
game_end_time = None
game_over = False
final_score_message = ""
paused = False

class Villager:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.alive = True
        self.last_throw_time = time.time()
        # Body dimensions
        self.head_radius = 10
        self.body_length = 25
        self.limb_length = 15
        self.animation_offset = 0
        self.animation_speed = 0.1

    def draw(self):
        if self.alive:
            # Animate limbs for walking effect
            self.animation_offset = math.sin(time.time() * self.animation_speed) * 5

            # Draw head with skin color
            midpoint_circle(self.x, self.y + self.head_radius, self.head_radius, (0.9, 0.7, 0.5))
            
            # Draw facial features
            glColor3f(0.0, 0.0, 0.0)  # Black for features
            glBegin(GL_POINTS)
            # Eyes
            plot_point(self.x - 3, self.y + self.head_radius + 2)
            plot_point(self.x + 3, self.y + self.head_radius + 2)
            # Mouth
            for x in range(-2, 3):
                plot_point(self.x + x, self.y + self.head_radius - 3)
            glEnd()

            # Draw body with shirt color
            glColor3f(0.2, 0.4, 0.8)  # Blue shirt
            glBegin(GL_POINTS)
            
            # Draw body using midpoint line (thicker)
            body_points = midpoint_line(self.x, self.y, self.x, self.y - self.body_length)
            for px, py in body_points:
                plot_point(px, py)
                plot_point(px + 1, py)  # Make body thicker
                plot_point(px - 1, py)

            # Draw legs with animation and pants color
            leg_start_y = self.y - self.body_length
            glColor3f(0.3, 0.2, 0.1)  # Brown pants
            # Left leg
            left_leg_end_x = self.x - self.limb_length * 0.7 + self.animation_offset * 0.3
            left_leg_end_y = leg_start_y - self.limb_length * 0.7
            leg_points = midpoint_line(self.x, leg_start_y, int(left_leg_end_x), int(left_leg_end_y))
            for px, py in leg_points:
                plot_point(px, py)
                plot_point(px + 1, py)  # Make legs thicker

            # Right leg
            right_leg_end_x = self.x + self.limb_length * 0.7 - self.animation_offset * 0.3
            right_leg_end_y = leg_start_y - self.limb_length * 0.7
            leg_points = midpoint_line(self.x, leg_start_y, int(right_leg_end_x), int(right_leg_end_y))
            for px, py in leg_points:
                plot_point(px, py)
                plot_point(px - 1, py)  # Make legs thicker

            # Draw arms with animation and skin color
            arm_start_y = self.y - self.body_length // 3
            glColor3f(0.9, 0.7, 0.5)  # Skin color for arms
            # Left arm
            left_arm_end_x = self.x - self.limb_length * 0.7 - self.animation_offset * 0.2
            left_arm_end_y = arm_start_y + self.limb_length * 0.3
            arm_points = midpoint_line(self.x, arm_start_y, int(left_arm_end_x), int(left_arm_end_y))
            for px, py in arm_points:
                plot_point(px, py)
                plot_point(px + 1, py)  # Make arms thicker

            # Right arm
            right_arm_end_x = self.x + self.limb_length * 0.7 + self.animation_offset * 0.2
            right_arm_end_y = arm_start_y + self.limb_length * 0.3
            arm_points = midpoint_line(self.x, arm_start_y, int(right_arm_end_x), int(right_arm_end_y))
            for px, py in arm_points:
                plot_point(px, py)
                plot_point(px - 1, py)  # Make arms thicker

            glEnd()

    def check_collision_with_axe(self, axe):
        # Check head collision
        head_dist = math.hypot(self.x - axe.x, (self.y + self.head_radius) - axe.y)
        if head_dist < self.head_radius + axe.handle_width/2:
            return True

        # Check body collision (vertical line)
        for dy in range(0, self.body_length):
            body_point_y = self.y - dy
            if axe.check_collision(self.x, body_point_y, 2):  # 2 is body thickness
                return True

        # Check legs collision
        leg_start_y = self.y - self.body_length
        # Check both legs
        for i in range(self.limb_length):
            # Left leg
            x_left = int(self.x - i * 0.7)
            y = int(leg_start_y - i * 0.7)
            if axe.check_collision(x_left, y, 2):
                return True
            # Right leg
            x_right = int(self.x + i * 0.7)
            if axe.check_collision(x_right, y, 2):
                return True

        # Check arms collision
        arm_start_y = self.y - self.body_length // 3
        # Check both arms
        for i in range(self.limb_length):
            # Left arm
            x_left = int(self.x - i * 0.7)
            y = int(arm_start_y + i * 0.3)
            if axe.check_collision(x_left, y, 2):
                return True
            # Right arm
            x_right = int(self.x + i * 0.7)
            if axe.check_collision(x_right, y, 2):
                return True

        return False

    def throw_stone(self, target_x, target_y):
        current_time = time.time()
        if self.alive and current_time - self.last_throw_time >= STONE_THROW_DELAY:
            self.last_throw_time = current_time
            return Stone(self.x, self.y + self.head_radius, target_x, target_y)
        return None

class Axe:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.speed = 4
        # Axe dimensions
        self.handle_width = 6
        self.handle_height = 40
        self.blade_width = 30
        self.blade_height = 35
        self.blade_curve = 15
        self.facing_right = True
        # Store the head position separately
        self.head_x = x
        self.head_y = y + self.handle_height/2  # Head is now on top

    def draw(self):
        glColor3f(0.7, 0.7, 0.7)  # Gray color for axe
        glBegin(GL_POINTS)
        
        # Draw handle (vertical line)
        for y in range(int(self.y), int(self.y + self.handle_height)):  # Changed to draw upward
            plot_point(int(self.x), y)
        
        # Draw blade
        blade_center_y = self.y + self.handle_height  # Blade at top of handle
        blade_top = blade_center_y + self.blade_height//2
        blade_bottom = blade_center_y - self.blade_height//2
        
        if self.facing_right:
            # Right-facing blade
            for y in range(int(blade_bottom), int(blade_top)):
                for x in range(int(self.x), int(self.x + self.blade_width)):
                    # Add curve to the blade
                    dist_from_center = abs(y - blade_center_y)
                    max_x = self.x + self.blade_width - (dist_from_center * self.blade_curve / self.blade_height)
                    if x <= max_x:
                        plot_point(x, y)
        else:
            # Left-facing blade
            for y in range(int(blade_bottom), int(blade_top)):
                for x in range(int(self.x - self.blade_width), int(self.x)):
                    # Add curve to the blade
                    dist_from_center = abs(y - blade_center_y)
                    min_x = self.x - self.blade_width + (dist_from_center * self.blade_curve / self.blade_height)
                    if x >= min_x:
                        plot_point(x, y)
        
        glEnd()

    def move(self):
        old_x = self.x
        old_y = self.y
        
        if key_state.get(b'w', False) and self.y < HEIGHT - self.handle_height:  # Changed direction for W
            self.y += self.speed  # Move up
        if key_state.get(b's', False) and self.y > self.handle_height:  # Changed direction for S
            self.y -= self.speed  # Move down
        if key_state.get(b'a', False) and self.x > self.blade_width:
            self.x -= self.speed
            self.facing_right = False
        if key_state.get(b'd', False) and self.x < WIDTH - self.blade_width:
            self.x += self.speed
            self.facing_right = True
        
        # Keep the head position fixed relative to the handle
        dx = self.x - old_x
        dy = self.y - old_y
        self.head_x += dx
        self.head_y += dy

    def check_collision(self, x, y, radius):
        # Check collision with handle
        if abs(x - self.x) < (self.handle_width + radius):
            if self.y <= y <= self.y + self.handle_height:
                return True
        
        # Check collision with blade
        blade_center_y = self.y + self.handle_height
        blade_top = blade_center_y + self.blade_height//2
        blade_bottom = blade_center_y - self.blade_height//2
        
        if blade_bottom - radius <= y <= blade_top + radius:
            if self.facing_right:
                if self.x - radius <= x <= self.x + self.blade_width + radius:
                    return True
            else:
                if self.x - self.blade_width - radius <= x <= self.x + radius:
                    return True
        
        return False

class Stone:
    def __init__(self, x, y, target_x, target_y):
        self.x = x
        self.y = y
        angle = math.atan2(target_y - y, target_x - x)
        self.dx = math.cos(angle) * 2
        self.dy = math.sin(angle) * 2

    def move(self):
        self.x += self.dx
        self.y += self.dy

    def draw(self):
        # Draw stone using midpoint circle algorithm
        midpoint_circle(int(self.x), int(self.y), STONE_RADIUS, (0, 0, 1))

def midpoint_circle(xc, yc, radius, color):
    glColor3f(*color)
    glBegin(GL_POINTS)
    
    x = radius
    y = 0
    p = 1 - radius

    # Plot initial points
    def plot_circle_points(x, y):
        plot_point(xc + x, yc + y)
        plot_point(xc - x, yc + y)
        plot_point(xc + x, yc - y)
        plot_point(xc - x, yc - y)
        plot_point(xc + y, yc + x)
        plot_point(xc - y, yc + x)
        plot_point(xc + y, yc - x)
        plot_point(xc - y, yc - x)

    # Midpoint circle algorithm
    plot_circle_points(x, y)
    while x > y:
        y += 1
        if p <= 0:
            p = p + 2 * y + 1
        else:
            x -= 1
            p = p + 2 * y - 2 * x + 1
        plot_circle_points(x, y)
    glEnd()

def midpoint_line(x1, y1, x2, y2):
    # Initialize points
    points = []
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    x = x1
    y = y1
    
    # Determine direction
    x_inc = 1 if x2 > x1 else -1
    y_inc = 1 if y2 > y1 else -1
    
    # Decide which coordinate to drive the line
    if dx > dy:
        # Drive line using x coordinate
        decision = dx / 2
        while x != x2:
            points.append((x, y))
            decision -= dy
            if decision < 0:
                y += y_inc
                decision += dx
            x += x_inc
    else:
        # Drive line using y coordinate
        decision = dy / 2
        while y != y2:
            points.append((x, y))
            decision -= dx
            if decision < 0:
                x += x_inc
                decision += dy
            y += y_inc
    
    points.append((x2, y2))  # Add the end point
    return points

def fill_circle(cx, cy, radius, color):
    glColor3f(*color)
    glBegin(GL_POINTS)
    for y in range(-radius, radius + 1):
        x_max = int(math.sqrt(radius * radius - y * y))
        for x in range(-x_max, x_max + 1):
            plot_point(int(cx + x), int(cy + y))
    glEnd()

def plot_point(x, y):
    glVertex2i(int(x), int(y))

def fill_rectangle(x, y, width, height, color):
    glColor3f(*color)
    glBegin(GL_POINTS)
    # Convert dimensions to integers
    half_width = int(width / 2)
    half_height = int(height / 2)
    for dy in range(-half_height, half_height + 1):
        for dx in range(-half_width, half_width + 1):
            plot_point(int(x + dx), int(y + dy))
    glEnd()

def fill_triangle(x1, y1, x2, y2, x3, y3, color):
    glColor3f(*color)
    glBegin(GL_POINTS)
    
    # Find bounding box
    min_x = min(x1, x2, x3)
    max_x = max(x1, x2, x3)
    min_y = min(y1, y2, y3)
    max_y = max(y1, y2, y3)
    
    # Check each point in bounding box
    for y in range(int(min_y), int(max_y) + 1):
        for x in range(int(min_x), int(max_x) + 1):
            # Barycentric coordinates
            d = (y2 - y3) * (x1 - x3) + (x3 - x2) * (y1 - y3)
            if d != 0:
                a = ((y2 - y3) * (x - x3) + (x3 - x2) * (y - y3)) / d
                b = ((y3 - y1) * (x - x3) + (x1 - x3) * (y - y3)) / d
                c = 1 - a - b
                if 0 <= a <= 1 and 0 <= b <= 1 and 0 <= c <= 1:
                    plot_point(x, y)
    glEnd()

def keyboard(key, x, y):
    global key_state
    key_state[key] = True
    
    if key == b'\x1b':  # ESC key
        glutLeaveMainLoop()

def key_released(key, x, y):
    global key_state
    key_state[key] = False

def mouse_func(button, state, x, y):
    global game_paused, game_over, score, villagers, stones
    
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        # Convert window coordinates to OpenGL coordinates
        y = HEIGHT - y
        
        # Check restart button (only works when paused)
        if abs(x - restart_pos[0]) < button_size and abs(y - restart_pos[1]) < button_size:
            if game_paused or game_over:
                # Reset game state
                game_over = False
                score = 0
                villagers = []
                stones = []
                game_paused = False
        
        # Check pause button
        elif abs(x - pause_pos[0]) < button_size and abs(y - pause_pos[1]) < button_size:
            game_paused = not game_paused
        
        # Check end button
        elif abs(x - end_pos[0]) < button_size and abs(y - end_pos[1]) < button_size:
            glutLeaveMainLoop()

def init():
    global villagers, axe, stones, score, last_villager_generation_time
    
    # Initialize game state
    glClearColor(0.0, 0.0, 0.0, 0.0)
    gluOrtho2D(0, WIDTH, 0, HEIGHT)
    
    # Initialize game objects
    villagers = [Villager(random.randint(200, WIDTH - 200), random.randint(100, HEIGHT - 100)) for _ in range(10)]
    axe = Axe(WIDTH // 2, HEIGHT // 2)
    stones = []
    score = 0
    last_villager_generation_time = time.time()

def animate(value):
    global last_villager_generation_time, game_over, game_end_time
    
    if not game_paused and not game_over:
        current_time = time.time()
        
        # Update axe position
        axe.move()
        
        # Generate new villager
        if current_time - last_villager_generation_time > VILLAGER_GENERATION_DELAY:
            generate_villager()
            last_villager_generation_time = current_time
        
        # Update villagers and stones
        update_villagers()
        update_stones()
        
        # Check if all villagers are killed
        if all(not villager.alive for villager in villagers):
            game_over = True
            game_end_time = current_time
    
    # Check if 10 seconds have passed since game over
    if game_over and time.time() - game_end_time > 10:
        glutLeaveMainLoop()
    
    glutPostRedisplay()
    glutTimerFunc(16, animate, 0)

def display():
    glClear(GL_COLOR_BUFFER_BIT)
    
    if not game_over:
        # Draw game elements
        axe.draw()
        for villager in villagers:
            villager.draw()
        for stone in stones:
            stone.draw()
        
        # Draw buttons
        draw_restart_button()
        draw_pause_button()
        draw_end_button()
        
        # Draw score
        draw_text(10, HEIGHT - 30, f"Score: {score}", 1)
    else:
        # Draw final score message in the center of the screen
        scale = 2  # Double the size for final score
        message = "YOUR FINAL SCORE: " + str(score)
        text_width = len(message) * 8 * scale  # Adjusted width for larger text
        x = (WIDTH - text_width) // 2
        y = HEIGHT // 2
        
        # Draw larger background rectangle for bigger text
        glColor3f(0.0, 0.0, 0.0)  # Black background
        glBegin(GL_POINTS)
        for i in range(x - 20, x + text_width + 20):
            for j in range(y - 40, y + 40):
                plot_point(i, j)
        glEnd()
        
        # Draw text in green with larger scale
        glColor3f(0.0, 1.0, 0.0)  # Green color
        draw_text(x, y - 20, message, scale)  # Adjusted Y position for larger text
    
    glutSwapBuffers()

def draw_text(x, y, text, scale=1):  # Added scale parameter with default value
    glBegin(GL_POINTS)
    current_x = x
    for char in text.upper():  # Convert to uppercase
        if char.isdigit():
            draw_number(current_x, y, int(char), scale)
            current_x += 8 * scale  # Adjust spacing based on scale
        elif char == ':':
            # Draw colon
            for i in range(2):
                plot_point(current_x + 2 * scale, y + i*3 * scale + 1)
            current_x += 6 * scale  # Adjust spacing based on scale
        elif char == ' ':
            current_x += 6 * scale  # Space width adjusted for scale
        else:
            draw_letter(current_x, y, char, scale)
            current_x += 8 * scale  # Adjust spacing based on scale
    glEnd()

def draw_letter(x, y, letter, scale):
    # Simple point-based letter patterns
    patterns = {
        'A': [(1,4), (0,3), (2,3), (0,2), (1,2), (2,2), (0,1), (2,1), (0,0), (2,0)],
        'C': [(0,4), (1,4), (2,4), (0,3), (0,2), (0,1), (0,0), (1,0), (2,0)],
        'E': [(0,4), (1,4), (2,4), (0,3), (0,2), (1,2), (2,2), (0,1), (0,0), (1,0), (2,0)],
        'F': [(0,4), (1,4), (2,4), (0,3), (0,2), (1,2), (0,1), (0,0)],
        'I': [(0,4), (1,4), (2,4), (1,3), (1,2), (1,1), (0,0), (1,0), (2,0)],
        'L': [(0,4), (0,3), (0,2), (0,1), (0,0), (1,0), (2,0)],
        'N': [(0,4), (0,3), (0,2), (0,1), (0,0), (1,3), (2,2), (2,4), (2,3), (2,2), (2,1), (2,0)],
        'O': [(0,4), (1,4), (2,4), (0,3), (2,3), (0,2), (2,2), (0,1), (2,1), (0,0), (1,0), (2,0)],
        'P': [(0,4), (1,4), (2,4), (0,3), (2,3), (0,2), (1,2), (2,2), (0,1), (0,0)],
        'R': [(0,4), (1,4), (2,4), (0,3), (2,3), (0,2), (1,2), (0,1), (2,1), (0,0), (2,0)],
        'S': [(0,4), (1,4), (2,4), (0,3), (0,2), (1,2), (2,2), (2,1), (0,0), (1,0), (2,0)],
        'T': [(0,4), (1,4), (2,4), (1,3), (1,2), (1,1), (1,0)],
        'U': [(0,4), (2,4), (0,3), (2,3), (0,2), (2,2), (0,1), (2,1), (0,0), (1,0), (2,0)],
        'Y': [(0,4), (2,4), (0,3), (2,3), (1,2), (1,1), (1,0)],
        ' ': []  # Space character
    }
    if letter in patterns:
        for px, py in patterns[letter]:
            plot_point(x + px * scale, y + py * scale)

def draw_number(x, y, number, scale):
    # Number patterns (flipped Y coordinates)
    patterns = {
        0: [(0,4), (1,4), (2,4), (0,3), (2,3), (0,2), (2,2), (0,1), (2,1), (0,0), (1,0), (2,0)],
        1: [(1,4), (1,3), (1,2), (1,1), (1,0)],
        2: [(0,4), (1,4), (2,4), (2,3), (0,2), (1,2), (2,2), (0,1), (0,0), (1,0), (2,0)],
        3: [(0,4), (1,4), (2,4), (2,3), (1,2), (2,1), (0,0), (1,0), (2,0)],
        4: [(0,4), (2,4), (0,3), (2,3), (0,2), (1,2), (2,2), (2,1), (2,0)],
        5: [(0,4), (1,4), (2,4), (0,3), (0,2), (1,2), (2,2), (2,1), (0,0), (1,0), (2,0)],
        6: [(0,4), (1,4), (2,4), (0,3), (0,2), (1,2), (2,2), (0,1), (2,1), (0,0), (1,0), (2,0)],
        7: [(0,4), (1,4), (2,4), (2,3), (2,2), (1,1), (1,0)],
        8: [(0,4), (1,4), (2,4), (0,3), (2,3), (1,2), (0,1), (2,1), (0,0), (1,0), (2,0)],
        9: [(0,4), (1,4), (2,4), (0,3), (2,3), (0,2), (1,2), (2,2), (2,1), (0,0), (1,0), (2,0)]
    }
    if number in patterns:
        for px, py in patterns[number]:
            plot_point(x + px * scale, y + py * scale)

def draw_final_score():
    if game_over:
        # Draw black background
        glColor3f(0, 0, 0)
        glBegin(GL_POINTS)
        for y in range(HEIGHT//2 - 80, HEIGHT//2 + 80):
            for x in range(WIDTH//2 - 200, WIDTH//2 + 200):
                plot_point(x, y)
        glEnd()

        # Draw border
        glColor3f(1, 1, 1)
        glBegin(GL_POINTS)
        # Top and bottom borders
        for x in range(WIDTH//2 - 200, WIDTH//2 + 200):
            for y in range(-2, 3):  # Thickness of 5 pixels
                plot_point(x, HEIGHT//2 - 80 + y)  # Top border
                plot_point(x, HEIGHT//2 + 80 + y)  # Bottom border
        # Left and right borders
        for y in range(HEIGHT//2 - 80, HEIGHT//2 + 80):
            for x in range(-2, 3):  # Thickness of 5 pixels
                plot_point(WIDTH//2 - 200 + x, y)  # Left border
                plot_point(WIDTH//2 + 200 + x, y)  # Right border
        glEnd()

        # Draw text
        glColor3f(1, 1, 1)
        glBegin(GL_POINTS)
        scale = 3  # Larger scale for better visibility
        
        # Draw "YOUR FINAL SCORE:" text
        title_text = "YOUR FINAL SCORE:"
        x_pos = WIDTH//2 - (len(title_text) * 8 * scale)//2  # Center text horizontally
        y_pos = HEIGHT//2 + 20
        
        for char in title_text:
            if char in '0123456789':
                draw_number(x_pos, y_pos, int(char), scale)
            elif char == ':':
                draw_colon(x_pos, y_pos, scale)
            elif char == ' ':
                pass  # Skip spaces
            else:
                draw_letter(x_pos, y_pos, char, scale)
            x_pos += 8 * scale  # Spacing between characters
        
        # Draw the score number
        score_text = str(score)
        x_pos = WIDTH//2 - (len(score_text) * 12 * scale)//2  # Center score
        y_pos = HEIGHT//2 - 20
        
        for char in score_text:
            draw_number(x_pos, y_pos, int(char), scale)
            x_pos += 12 * scale
        
        glEnd()

def display_final_score():
    global game_end_time, game_over, final_score_message
    game_end_time = time.time()
    game_over = True
    final_score_message = f"Game Over! Final Score: {score}"

def generate_villager():
    villagers.append(Villager(random.randint(200, WIDTH - 200), random.randint(100, HEIGHT - 100)))

def update_villagers():
    for villager in villagers:
        if villager.alive:
            new_stone = villager.throw_stone(axe.x, axe.y)
            if new_stone:
                stones.append(new_stone)
            if villager.check_collision_with_axe(axe):
                villager.alive = False
                global score
                score += 10

def update_stones():
    for stone in stones[:]:
        stone.move()
        if axe.check_collision(stone.x, stone.y, STONE_RADIUS):
            print(f"The villagers hit the axe! Final score: {score}")
            display_final_score()
            return

def draw_restart_button():
    # Draw restart arrow symbol using points
    color = (0.0, 1.0, 0.0) if game_paused else (0.5, 0.5, 0.5)  # Green if paused, gray if not
    glColor3f(*color)
    glBegin(GL_POINTS)
    # Draw circular arrow
    radius = button_size
    for angle in range(0, 300, 5):  # Draw 300 degrees of circle
        rad = math.radians(angle)
        x = restart_pos[0] + radius * math.cos(rad)
        y = restart_pos[1] + radius * math.sin(rad)
        plot_point(int(x), int(y))
    # Draw arrowhead
    arrow_angle = math.radians(300)
    tip_x = restart_pos[0] + radius * math.cos(arrow_angle)
    tip_y = restart_pos[1] + radius * math.sin(arrow_angle)
    for i in range(5):
        plot_point(int(tip_x + i), int(tip_y + i))
        plot_point(int(tip_x + i), int(tip_y - i))
    glEnd()

def draw_pause_button():
    # Draw pause/play symbol using points
    color = (1.0, 0.0, 0.0) if game_paused else (0.0, 1.0, 0.0)  # Red if paused, green if not
    glColor3f(*color)
    glBegin(GL_POINTS)
    if game_paused:
        # Draw play triangle
        for i in range(-button_size, button_size + 1):
            for j in range(-abs(i), abs(i) + 1):
                plot_point(pause_pos[0] + i, pause_pos[1] + j)
    else:
        # Draw pause bars
        for i in range(-button_size, -button_size//2):
            for j in range(-button_size, button_size + 1):
                plot_point(pause_pos[0] + i, pause_pos[1] + j)
        for i in range(button_size//2, button_size + 1):
            for j in range(-button_size, button_size + 1):
                plot_point(pause_pos[0] + i, pause_pos[1] + j)
    glEnd()

def draw_end_button():
    # Draw X symbol using points
    glColor3f(1.0, 0.0, 0.0)  # Red color
    glBegin(GL_POINTS)
    for i in range(-button_size, button_size + 1):
        for j in range(-2, 3):  # Thickness of the X
            plot_point(end_pos[0] + i + j, end_pos[1] + i)
            plot_point(end_pos[0] + i + j, end_pos[1] - i)
    glEnd()

if __name__ == "__main__":
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB)
    glutInitWindowSize(WIDTH, HEIGHT)
    glutCreateWindow(b"Killer Axe Game")
    
    init()  # Initialize game state
    
    # Register callbacks
    glutDisplayFunc(display)
    glutTimerFunc(0, animate, 0)
    glutKeyboardFunc(keyboard)
    glutKeyboardUpFunc(key_released)
    glutMouseFunc(mouse_func)
    
    glutMainLoop()
