import pygame

pygame.init()

screenWidth = 1200
screenHeight = 700



screen = pygame.display.set_mode((screenWidth, screenHeight), pygame.RESIZABLE)
pygame.display.set_caption("DodgeArrow Fighting")
clock = pygame.time.Clock()
fps = 60

# 이미지 가져오는 함수
def getImage(path: str, scale=0.8):
    originalImage = pygame.image.load(path).convert_alpha()
    newWidth = int(originalImage.get_width() * scale)
    newHeight = int(originalImage.get_height() * scale)
    return pygame.transform.scale(originalImage, (newWidth, newHeight))

# 배경
backgroundImage = getImage("./assets/background.png", scale=1.0)

# 캐릭터 1
char1Idle = getImage("./assets/player/1/idle.png")
char1Attack = [
    getImage(f"./assets/player/1/attack{i}.png") for i in range(2) 
]

# 캐릭터 2
char2Idle = getImage("./assets/player/2/idle.png")
char2Idle = pygame.transform.flip(char2Idle, True, False)  # ← 좌우 반전

char2Attack = [
    getImage(f"./assets/player/2/attack{i}.png") for i in range(2)
]
char2Attack = [
    pygame.transform.flip(img, True, False)  # ← 각 프레임 좌우 반전
    for img in char2Attack
]


# 보스
bossIdle = getImage("./assets/boss/idle.png")
bossHit = [
    getImage(f"./assets/boss/attack{i}.png") for i in range(3)
]

# 캐릭터 1
isAttackingChar1 = False
currentFrameChar1 = 0
animationCounterChar1 = 0

# 캐릭터 2
isAttackingChar2 = False
currentFrameChar2 = 0
animationCounterChar2 = 0

# 보스
bossFrame = 0
bossAnimationCounter = 0

# 애니메이션 속도
charAnimationSpeed = 8
bossAnimationSpeed = 10


# --- 3. 캐릭터 위치 설정 변수 ---
def setCharacterPosition():
    global backgroundImage, char1Pos, bossPos, char2Pos
    
    backgroundImage = pygame.transform.scale(backgroundImage, (screenWidth, screenHeight))
    
    char1_x = screenWidth * 1 // 4
    boss_x = screenWidth * 2 // 4
    char2_x = screenWidth * 3 // 4
    pos_y = screenHeight // 2
    
    char1_w, char1_h = char1Idle.get_size()
    boss_w, boss_h = bossIdle.get_size()
    char2_w, char2_h = char2Idle.get_size()
    
    char1Pos = (char1_x - char1_w // 2, pos_y)
    bossPos  = (boss_x - boss_w // 2, pos_y)
    char2Pos = (char2_x - char2_w // 2, pos_y)
    
setCharacterPosition()

isRun = True
while isRun:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            isRun = False
        
        elif event.type == pygame.VIDEORESIZE:
            newWidth = event.w
            newHeight = event.h
            screen = pygame.display.set_mode((newWidth, newHeight), pygame.RESIZABLE)
            screenWidth = newWidth
            screenHeight = newHeight
            setCharacterPosition()

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and not isAttackingChar1:
                isAttackingChar1 = True
                currentFrameChar1 = 0
                animationCounterChar1 = 0
            
            elif event.button == 3 and not isAttackingChar2:
                isAttackingChar2 = True
                currentFrameChar2 = 0
                animationCounterChar2 = 0

    # 캐릭터 1 애니메이션
    if isAttackingChar1:
        animationCounterChar1 += 1
        if animationCounterChar1 >= charAnimationSpeed:
            currentFrameChar1 += 1
            animationCounterChar1 = 0
            if currentFrameChar1 >= len(char1Attack): 
                isAttackingChar1 = False
                currentFrameChar1 = 0

    # 캐릭터 2 애니메이션
    if isAttackingChar2:
        animationCounterChar2 += 1
        if animationCounterChar2 >= charAnimationSpeed:
            currentFrameChar2 += 1
            animationCounterChar2 = 0
            if currentFrameChar2 >= len(char2Attack):
                isAttackingChar2 = False
                currentFrameChar2 = 0
    

    # 보스 애니메이션
    if isAttackingChar1 or isAttackingChar2:
        bossAnimationCounter += 1
        if bossAnimationCounter >= bossAnimationSpeed:
            bossFrame += 1
            bossAnimationCounter = 0
            
            # 인덱스 범위 넘으면 0으로
            if bossFrame >= len(bossHit):
                bossFrame = 0 
    else: # 공격이 없으면 초기화
        bossFrame = 0
        bossAnimationCounter = 0

        
    screen.blit(backgroundImage, (0, 0))
    
    # 보스 이미지 결정
    if isAttackingChar1 or isAttackingChar2:
        currentBossImage = bossHit[bossFrame] 
    else:
        currentBossImage = bossIdle

    # 캐릭터 1 이미지 결정
    if isAttackingChar1:
        currentPlayer1Image = char1Attack[currentFrameChar1]
    else:
        currentPlayer1Image = char1Idle
        
    # 캐릭터 2 이미지 결정
    if isAttackingChar2:
        currentPlayer2Image = char2Attack[currentFrameChar2]
    else:
        currentPlayer2Image = char2Idle
        
    # 배치
    screen.blit(currentPlayer1Image, char1Pos)
    screen.blit(currentBossImage, bossPos)
    screen.blit(currentPlayer2Image, char2Pos)
    
    pygame.display.update()
    clock.tick(fps)

pygame.quit()