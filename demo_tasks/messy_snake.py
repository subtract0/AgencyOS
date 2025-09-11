#!/usr/bin/env python3
import random
import sys

import pygame

pygame.init()

WIDTH = 800
HEIGHT = 600
FPS = 10
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
WHITE = (255, 255, 255)


def main():
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Messy Snake Game")
    clock = pygame.time.Clock()

    snake_x = WIDTH // 2
    snake_y = HEIGHT // 2
    snake_body = [(snake_x, snake_y)]
    direction = "RIGHT"

    food_x = random.randint(0, (WIDTH - 20) // 20) * 20
    food_y = random.randint(0, (HEIGHT - 20) // 20) * 20

    score = 0
    font = pygame.font.Font(None, 36)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP and direction != "DOWN":
                    direction = "UP"
                elif event.key == pygame.K_DOWN and direction != "UP":
                    direction = "DOWN"
                elif event.key == pygame.K_LEFT and direction != "RIGHT":
                    direction = "LEFT"
                elif event.key == pygame.K_RIGHT and direction != "LEFT":
                    direction = "RIGHT"

        head_x, head_y = snake_body[0]
        if direction == "UP":
            new_head = (head_x, head_y - 20)
        elif direction == "DOWN":
            new_head = (head_x, head_y + 20)
        elif direction == "LEFT":
            new_head = (head_x - 20, head_y)
        elif direction == "RIGHT":
            new_head = (head_x + 20, head_y)

        snake_body.insert(0, new_head)

        if new_head[0] == food_x and new_head[1] == food_y:
            score += 10
            food_x = random.randint(0, (WIDTH - 20) // 20) * 20
            food_y = random.randint(0, (HEIGHT - 20) // 20) * 20
        else:
            snake_body.pop()

        if (
            new_head[0] < 0
            or new_head[0] >= WIDTH
            or new_head[1] < 0
            or new_head[1] >= HEIGHT
        ):
            print(f"Game Over! Score: {score}")
            running = False

        if new_head in snake_body[1:]:
            print(f"Game Over! Score: {score}")
            running = False

        screen.fill(BLACK)

        for segment in snake_body:
            pygame.draw.rect(screen, GREEN, (segment[0], segment[1], 20, 20))

        pygame.draw.rect(screen, RED, (food_x, food_y, 20, 20))

        score_text = font.render(f"Score: {score}", True, WHITE)
        screen.blit(score_text, (10, 10))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
