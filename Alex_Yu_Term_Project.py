import pygame
import sys
import wave
import aubio
import audiotools
import os
import numpy
import string
import copy
import random
#from numpy import median, diff

######################################################################
                            # GAME PART
######################################################################
######################################################################
    # Init Functions and Game
######################################################################

def termProject():
    width = 1200
    height = width/2
    rows, margin = 3, height/30 #top and bottom margin
    pygame.init() #initializes pygame module
    class Struct: pass
    data = Struct() #creates class for data
    data.rows, data.margin = rows, margin
    data.height, data.width = height, width
    termProjectInitFn(data)
    clock, screen = pygame.time.Clock(), pygame.display.set_mode((width,height))
    game = True
    pygame.display.set_caption('Term Project!')
    while game: #main loop for game, gets new events that occur
        if data.mode == 'menu': #when on menu screen
            menuSurface(data, screen) #draws menu surface
            for event in pygame.event.get(): #goes through all the events
                if event.type == pygame.MOUSEBUTTONDOWN:
                    termProjectMouseFn(event, data)
        elif data.mode == 'instructions': #when on instructions screen
            instructionsSurface(data, screen) #draws i nstruction surface
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    termProjectKeyFn(event, screen, data)
        elif data.mode == 'options': #when on options screen
            optionsSurface(data, screen) #draws option surface
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    termProjectKeyFn(event, screen, data)
                if event.type == pygame.MOUSEBUTTONDOWN:
                    termProjectMouseFn(event, data)
        elif data.mode == 'songInput': #when on input prompt screen
            question = 'Type in the song that you want to play with!'
            inputBoxSurface(data, screen, question, data.inputPhrase)
            for event in pygame.event.get():
                if event.type == pygame.MOUSEBUTTONDOWN:
                    termProjectMouseFn(event, data)
                elif event.type == pygame.KEYDOWN:
                    termProjectKeyFn(event, screen, data)
            #draws surface for inputting song name and gets song name
        elif data.mode == 'try again': #if user types in invalid file name
            question = 'Oops that song is not available. Try again!'
            inputBoxSurface(data, screen, question, data.inputPhrase)
            for event in pygame.event.get():
                if event.type == pygame.MOUSEBUTTONDOWN:
                    termProjectMouseFn(event, data)
                elif event.type == pygame.KEYDOWN:
                    termProjectKeyFn(event, screen, data)
        elif data.mode == 'play': #when playing game
            if data.init == 0:
                mainGameInitFn(data)
                sliceInitFn(data)
                data.songSlice = data.directory + 'song_0.000.wav'
                gameSliceInitFn(data) #init fn for the game
                data.init += 1
            if data.musicPlay == 0:
                pygame.mixer.music.load(data.song)
                pygame.mixer.music.play() #plays song while game is going
                data.musicPlay += 1
            elif pygame.mixer.music.get_pos() >= data.sliceN*data.duration*1000:
                actualTime = data.totalTime - data.totalTime/100
                if pygame.mixer.music.get_pos() >= actualTime*1000:
                #song is over, so game is over
                    data.mode = 'end'
                elif pygame.mixer.music.get_pos() >= data.duration*1000:
                    data.currentSlice += 1
                    sliceInitFn(data)
                    sliceN = data.sliceN*data.duration
                    data.songSlice = data.directory+data.songName +'_%d.000.wav'%sliceN 
                    gameSliceInitFn(data) #init fn for the game
                    #goes through the audio slices
            data.initNotes = int(round(float(data.sampleLength)/data.duration/data.FPS))
            #how many notes that need to be initialized per frame
            if data.initEnd + data.initNotes < (data.currentSlice+1)*data.sampleLength:
                data.initEnd += data.initNotes
                notesInitFn(data, data.initStart, data.initEnd)
                data.initStart += data.initNotes
            gameDrawFn(screen, data) #draws game surface
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN: #* FIX FOR BUG
                    termProjectKeyFn(event, screen, data)
            enemyCollision(data, screen) #test for collision with enemy
            removeDone(data) #removes notes from list that are passed
            if data.drawStart > 0: data.drawStart -= data.removed
            data.drawEnd -= data.removed
            if data.nextSlice: #if a new slice was analyzed
                if data.sliceN < (data.sliceNo-1): #as long as still have slices
                    data.sliceN += 1
                data.nextSlice = False
            data.frames += 1
            data.rating -= data.removed
            data.rating += data.hit
            if data.onRemoved == 0: #if no actual note was missed
                data.streak += data.onHit
                if data.streak > data.maxStreak: data.maxStreak = data.streak
            else: data.streak = 0 #resets streak if something was missed
            data.onHit = data.onRemoved = 0 #if hit or missed actual notes
        elif data.mode == 'end': #when game has finished
            if data.musicPlay == 1: #so won't play repeatedly
                pygame.mixer.music.play()
                data.musicPlay += 1
            endSurface(data, screen) #draws end game surface
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    termProjectKeyFn(event, screen, data)
        data.time += clock.tick(data.FPS)
        pygame.display.flip() #updates everything after done drawing
    pygame.quit()

def termProjectInitFn(data): #main init fn for menu screens
    data.time = 0
    data.inputPhrase = []
    data.musicPlay = data.init = 0
    data.score = data.total = 0 #total number of notes, used to calculate score
    data.difficulty, data.loss = "easy", 5 #rating lost from hitting enemy
    data.black, data.white, data.custom = (0,0,0), (255,255,255), (215,255,85)
    data.blue, data.gray = (0,0,255), (122,122,122)
    data.sliceN = data.currentSlice = 0 #which slice to analyze
    data.initStart = data.initEnd = data.drawStart = data.drawEnd = 0
    data.currentPitch = data.frames = 0 #number of frames that have passed
    data.nextSlice = False #signals when to move to next slice
    data.samplerate, data.winsize = 44100, 1024 # fft size
    data.hopsize = data.winsize/2 # hop size
    delay, interval = 100, 50
    data.menuObjects = []
    data.mode, data.FPS = 'menu', 30 #determines which surface to draw
    data.backInit = 0 #so background only initializes once
    data.menuInit = 0 #so menu objects only init once
    data.optionsInit = 0 #so option objects only init once
    data.enemy = False #whether or not there are enemies, default to no
    pygame.key.set_repeat(delay, interval) #recognizes held notes

def mainGameInitFn(data): #init fn for things in game that are init once
    File = audiotools.open(data.song)
    File.convert('song', audiotools.WaveAudio) #file name will = song
    data.song = '/Users/AlexYu/Documents/CMU/Freshman/112/Term Project/song'
    slicing(data, data.song) #slices file into smaller ones
    data.totalTime = getDuration(data, data.song)
    data.notes = [] #list of notes to draw
    data.pitches = []
    data.enemies = []
    data.powerups = []
    data.longStart = data.noteMove = 0 #controls when note becomes long note
    data.rating = 75 #starting rating, goes up and down depending on hit/miss
    data.powerUpsPos = [] #positions of powerups
    data.enemiesPos = [1] #positions of enemies
    powerUpNo, enemyNo = 20, 10 #number of powerups and enemies in game
    for i in xrange(powerUpNo):
        data.powerUpsPos += [random.randint(0, data.sliceNo)]
    for i in xrange(enemyNo):
        data.enemiesPos += [random.randint(0, data.sliceNo)]
    data.poweredUp = False
    data.startTime = 0 #time when powerup activates
    data.streak = data.maxStreak = 0 #current streak, longest streak
    data.hit = data.removed = 0 #total notes hit and notes removed
    data.onHit = data.onRemoved = 0 #onset notes hit and removed
    #used in calculating streaks
    data.rowHeight = int((data.height - 2*data.margin)/(data.rows + 0.5))
    data.statsRowHeight = data.rowHeight/2 #height of the stats displayed at the bottom
    playerImg = '/Users/AlexYu/Documents/CMU/Freshman/112/Term Project/run.png'
    data.player = Player(data, playerImg)

def gameSliceInitFn(data): #init fn for game part, once per sliced file
    File = audiotools.open(data.songSlice)
    sourceName = 'song%d' % data.currentSlice
    File.convert(sourceName, audiotools.WaveAudio)
    data.file = '/Users/AlexYu/Documents/CMU/Freshman/112/Term Project/' + sourceName
    data.pitches += pitchSampling(data, data.file)
    data.onsets = onset(data, data.file)
    if data.currentSlice == 0:
        data.firstNote = min(data.onsets) #index of first note played
    # data.noteFound = False
    # notesInitFn(data, data.noteStart)

def sliceInitFn(data): #init fn for values that need to be reset for each slice
    data.nextSlice = True
    data.songName = os.path.splitext(os.path.basename(data.song))[0]
    data.directory = '/Users/AlexYu/Documents/CMU/Freshman/112/Term Project/'

def pitchToLevel(data, pitch, maxPitch, minPitch): 
#converts pitch to corresponding row in game
    ranges = (maxPitch-minPitch)/data.rows
    if pitch == maxPitch: level = data.rows - 1 #accounts for edge case
    else: level = (pitch-minPitch)/ranges
    return int(level)

def notesInitFn(data, start, end): #initializes pitches as Note objects
    #data.epsilon determines how close pitch has to be to be considered same
    if data.difficulty == 'easy': 
        data.epsilon = 0.5
        data.loss = 5
    if data.difficulty == 'medium': 
        data.epsilon = 1
        data.loss = 10
    if data.difficulty == 'hard': 
        data.epsilon = 3
        data.loss = 15
    if data.difficulty == 'crazy': 
        data.epsilon = 5
        data.loss = 20
    outlier = 1000 #maximum pitch, anything higher is not counted
    pitches = copy.deepcopy(data.pitches[data.currentSlice*data.sampleLength:])
    dec = 0
    for i in xrange(len(pitches)-1):
        if pitches[i-dec] == 0.0 or pitches[i-dec] >= outlier:
            pitches.pop(i-dec)
            dec += 1
    maxPitch, minPitch = max(pitches), min(pitches)
    if data.sliceN > 0:
        if pygame.mixer.music.get_pos() >= data.sliceN*data.duration*1000:
            #account for lag in initEnd and initStart
            data.initEnd = end = data.sliceN * data.sampleLength
            data.initStart = end - data.initNotes #will correct on next frame
    for i in xrange(start, end):
        if i < data.firstNote: data.notes += [0] #before first onset is not note
        elif i in data.onsets:
            data.currentPitch, data.longStart = i, 0 
    #sets current pitch, value to make sure long note only for pitches in a row
            if data.pitches[i] == 0.0: level = 0
            elif data.pitches[i] >= maxPitch: level = data.rows - 1
            else: level = pitchToLevel(data, data.pitches[i], maxPitch, minPitch)
            data.notes += [Notes(data, level)]
        elif (almostEqual(data, data.pitches[data.currentPitch],data.pitches[i]) 
            and data.longStart == 0):
            #if pitch is similar and right after onset, should be long note
            if data.pitches[i] == 0.0: level = 0 #in case
            elif data.pitches[i] >= maxPitch: level = data.rows - 1 #in case
            else: level = pitchToLevel(data, data.pitches[i], maxPitch, minPitch)
            note = Notes(data, level, 'long')
            if i != start: note.x += note.image.get_width()/2 #so won't overlap
            data.notes += [note]
        elif (not almostEqual(data, data.pitches[data.currentPitch], 
            data.pitches[i]) or data.longStart > 0):
            #not a held note anymore
            data.longStart += 1
            data.notes += [0]

def enemiesInit(data): #init for enemies
    est = 75 #+/- for at what time to draw powerups
    for pos in data.enemiesPos:
        minTime = pos*data.duration*1000 - est
        maxTime = pos*data.duration*1000 + est
        if pygame.mixer.music.get_pos() > minTime: 
            if pygame.mixer.music.get_pos() < maxTime:
                #if get_pos() is somewhere close to pos
                level = random.randint(0, data.rows-1)
                data.enemies += [Enemy(data, level)]

def powerUpsInit(data): #init for powerups
    est = 75 #+/- for at what time to draw powerups
    if pygame.mixer.music.get_pos() > data.startTime + 2*data.duration*1000:
        #if powerup has lasted one duration
        if data.poweredUp:
            data.poweredUp = False #not powered up anymore
    for pos in data.powerUpsPos:
        minTime = pos*data.duration*1000 - est
        maxTime = pos*data.duration*1000 + est
        if pygame.mixer.music.get_pos() > minTime: 
            if pygame.mixer.music.get_pos() < maxTime:
                #if get_pos() is somewhere close to pos
                level = random.randint(0, data.rows-1)
                data.powerups += [Powerup(data, level)]

def almostEqual(data, d1, d2):
    return abs(d1 - d2) < (data.epsilon)

######################################################################
    # Creating objects
######################################################################

class Player(object): #creates class for character that the user moves
    def __init__(self, data, imgFile):
        self.file = imgFile
        img = pygame.image.load(imgFile)
        scale = (float(data.rowHeight-(data.rowHeight/5))/img.get_height())*0.75
        self.xSize = int(img.get_width()*scale)
        self.ySize = int(img.get_height()*scale)
        self.image = pygame.transform.scale(img, (self.xSize, self.ySize))
        self.x = data.width/16
        self.y = data.margin + data.rowHeight*0.25 + (data.rows-1)*data.rowHeight
        self.width = self.x + self.image.get_rect().size[0] #right x value
        self.height = self.y + self.image.get_rect().size[1] #bottom y value

    def __repr__(self):
        d = self.__dict__
        results = [self.__class__.__name__ + "("]
        for key in sorted(d.keys()):
            if (len(results) > 1): results.append(", ")
            results.append(key + "=" + repr(d[key]))
        results.append(")")
        return "".join(results)

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __hash__(self):
        return hash(repr(self)) # inefficient but simple

    def draw(self, data, screen, imgFile):
        img = pygame.image.load(imgFile)
        self.image = pygame.transform.scale(img, (self.xSize, self.ySize))
        if data.poweredUp: #if has power up
            for i in xrange(data.rows):
                self.y = data.margin + i*data.rowHeight + data.rowHeight*0.25
                screen.blit(self.image, (self.x, self.y))
        else: screen.blit(self.image, (self.x, self.y))

class Notes(object): #class for notes
    def __init__(self, data, level, kind = 'note'): #level is which row note goes in
        if kind == 'note':
        #images from http://s296.photobucket.com/user/worldrave6/media/Notes-2.png.html
            greenNote = '/Users/AlexYu/Documents/CMU/Freshman/112/Term Project/Green Note.png'
            redNote = '/Users/AlexYu/Documents/CMU/Freshman/112/Term Project/Red Note.png'
            yellowNote = '/Users/AlexYu/Documents/CMU/Freshman/112/Term Project/Yellow Note.png'
            data.blueNote = '/Users/AlexYu/Documents/CMU/Freshman/112/Term Project/Blue Note.png'
            orangeNote = '/Users/AlexYu/Documents/CMU/Freshman/112/Term Project/Orange Note.png'
        elif kind == 'long':
        #images from http://www.fretsonfire.net/forums/viewtopic.php?t=24943
            greenNote = '/Users/AlexYu/Documents/CMU/Freshman/112/Term Project/Green Long Note.png'
            redNote = '/Users/AlexYu/Documents/CMU/Freshman/112/Term Project/Red Long Note.png'
            yellowNote = '/Users/AlexYu/Documents/CMU/Freshman/112/Term Project/Yellow Long Note.png'
            data.blueNote = '/Users/AlexYu/Documents/CMU/Freshman/112/Term Project/Blue Long Note.png'
            orangeNote = '/Users/AlexYu/Documents/CMU/Freshman/112/Term Project/Orange Long Note.png'
        notePics = [greenNote, redNote, yellowNote, data.blueNote, orangeNote]
        self.refImg = pygame.image.load(notePics[0])
        self.img = pygame.image.load(notePics[level])
        self.kind = kind
        scale = (data.rowHeight/2)/float(self.refImg.get_height())
        xSize = int(self.refImg.get_width()*scale)
        ySize = int(self.refImg.get_height()*scale)
        self.image = pygame.transform.scale(self.img, (xSize, ySize))
        self.x = data.width
        self.y = data.margin + level*data.rowHeight + data.rowHeight/10
        self.width = self.x + self.image.get_rect().size[0] #right x value
        self.height = self.y + self.image.get_rect().size[1] #bottom y value

    def __repr__(self):
        d = self.__dict__
        results = [self.__class__.__name__ + "("]
        for key in sorted(d.keys()):
            if (len(results) > 1): results.append(", ")
            results.append(key + "=" + repr(d[key]))
        results.append(")")
        return "".join(results)

    def __eq__(self, other):
        if type(other) != Notes:
            return False
        else:
            return self.__dict__ == other.__dict__

    def __hash__(self):
        return hash(repr(self)) #inefficient but simple

    def draw(self, data, screen):
        screen.blit(self.image, (self.x, self.y))
        if data.currentSlice < 1:
            ##number of frames needed for notes to move
            data.noteMove = data.width/data.onsets[0]
        self.x -= data.noteMove

class MenuButton(object): #class for options on menu screen
    def __init__(self, data, name, font, fontSize, color, xPos, yPos):
        self.name = name
        self.x, self.y = xPos, yPos
        self.font, self.size, self.color = font, fontSize, color
        data.smallOptionSize = self.size #used to reset size after new click
        fontObj = pygame.font.Font(font, fontSize)
        self.text = makeText(self.name, fontObj, self.color)
        self.width = self.x + self.text.get_rect().size[0] #right x value
        self.height = self.y + self.text.get_rect().size[1] #bottom y value
    
    def draw(self, data, screen):
        fontObj = pygame.font.Font(self.font, self.size)
        self.text = makeText(self.name, fontObj, self.color)
        screen.blit(self.text, (self.x, self.y))

    def action(self, data): #what happens when button is clicked
        if self.name == 'Play': 
            data.mode = 'songInput'
            if data.clicked == True:
                self.size = self.size + self.size/5
        elif self.name == 'Instructions': 
            data.mode = 'instructions'
            if data.clicked == True:
                self.size = self.size + self.size/5
        elif self.name == 'Options': 
            data.mode = 'options'
            if data.clicked == True:
                self.size = self.size + self.size/5
        elif self.name == 'Easy': 
            data.difficulty = 'easy'
            if data.clicked == True:
                self.size = self.size + self.size/5
        elif self.name == 'Medium': 
            data.difficulty = 'medium'
            data.rows = 4
            if data.clicked == True:
                self.size = self.size + self.size/5
        elif self.name == 'Hard': 
            data.difficulty = 'hard'
            data.rows = 5
            if data.clicked == True:
                self.size = self.size + self.size/5
        elif self.name == 'CRAZY': 
            data.difficulty = 'crazy'
            data.rows = 5
            if data.clicked == True:
                self.size = self.size + self.size/5
        elif self.name == 'Yes': 
            data.enemy = True
            if data.clicked == True:
                self.size = self.size + self.size/5
        elif self.name == 'No':
            data.enemy = False
            if data.clicked == True:
                self.size = self.size + self.size/5
        elif self.name == 'BACK':
            data.mode = 'menu'
            if data.clicked == True:
                self.size = self.size + self.size/5

class Enemy(object): #class for enemies
    def __init__(self, data, level):
        self.file = '/Users/AlexYu/Documents/CMU/Freshman/112/Term Project/enemyLeft.png'
        self.img = pygame.image.load(self.file)
        scale = (float(data.rowHeight-(data.rowHeight/5))/self.img.get_height())*0.75
        self.xSize = int(self.img.get_width()*scale)
        self.ySize = int(self.img.get_height()*scale)
        self.image = pygame.transform.scale(self.img, (self.xSize, self.ySize))
        #from http://www.forwallpaper.com/wallpaper/skeleton-guitar-fire-rock-292893.html
        maxXDiff = data.width/10 #makes enemy pos more random
        xDiff = random.randint(0, maxXDiff)
        self.x = data.width + xDiff
        self.y = data.margin + data.rowHeight/10 + level*data.rowHeight
        self.width = self.x + self.image.get_width()
        self.height = self.y + self.image.get_height()
        self.leftMove, self.rightMove = data.width/100, -data.width/200
        self.move = self.leftMove
        self.dir, self.collide = 0, False

    def __repr__(self):
        d = self.__dict__
        results = [self.__class__.__name__ + "("]
        for key in sorted(d.keys()):
            if (len(results) > 1): results.append(", ")
            results.append(key + "=" + repr(d[key]))
        results.append(")")
        return "".join(results)

    def __eq__(self, other):
        if type(other) != Notes:
            return False
        else:
            return self.__dict__ == other.__dict__

    def __hash__(self):
        return hash(repr(self)) #inefficient but simple

    def draw(self, data, screen):
        if data.frames % data.FPS == 0:
            if (self.dir % 2) == 0: 
                self.move = self.leftMove
                self.file = '/Users/AlexYu/Documents/CMU/Freshman/112/Term Project/enemyLeft.png'
            else: 
                self.move = self.rightMove
                self.file = '/Users/AlexYu/Documents/CMU/Freshman/112/Term Project/enemyRight.png'
            self.dir += 1
        self.img = pygame.image.load(self.file)
        self.image = pygame.transform.scale(self.img, (self.xSize, self.ySize))
        screen.blit(self.image, (self.x, self.y))
        self.x -= self.move

    def hit(self, data, screen): #method to see if player runs into enemy
        error = self.width/2 #allows room for error b/c pygame moves by frames
        if data.player.width > self.x and data.player.width < self.width:
            if data.player.y > self.y and data.player.y < self.height:
                data.rating -= data.loss
                playerImg = '/Users/AlexYu/Documents/CMU/Freshman/112/Term Project/hurt.png'
                data.player.draw(data, screen, playerImg)
                self.collide = True

class Powerup(object): #class for powerups
    def __init__(self, data, level):
        imgFile = '/Users/AlexYu/Documents/CMU/Freshman/112/Term Project/powerup.png'
        self.image = pygame.image.load(imgFile)
        scale = self.image.get_height()/(float(data.rowHeight)/2)
        xSize = int(self.image.get_width()/scale)
        ySize = int(self.image.get_height()/scale)
        self.image = pygame.transform.scale(self.image, (xSize, ySize))
        #from https://aslanintelligence.files.wordpress.com/2012/01/chance.jpg
        maxXDiff = data.width/10 #makes powerup pos more random
        xDiff = random.randint(0, maxXDiff)
        height = self.image.get_height()
        self.y = data.margin + level*data.rowHeight + data.rowHeight/10
        self.x = data.width + xDiff
        self.width, self.height = self.x+self.image.get_width(), self.y+height

    def __repr__(self):
        d = self.__dict__
        results = [self.__class__.__name__ + "("]
        for key in sorted(d.keys()):
            if (len(results) > 1): results.append(", ")
            results.append(key + "=" + repr(d[key]))
        results.append(")")
        return "".join(results)

    def __eq__(self, other):
        if type(other) != Notes:
            return False
        else:
            return self.__dict__ == other.__dict__

    def __hash__(self):
        return hash(repr(self)) #inefficient but simple

    def draw(self, data, screen):
        screen.blit(self.image, (self.x, self.y))
        self.x -= data.noteMove

    def opened(self, data): #method to see if is picked up by player
        error = self.width/2 #allows room for error b/c pygame moves by frames
        if data.player.width > self.x and data.player.width < self.width+error:
            if data.player.y > self.y and data.player.y < self.height:
                data.poweredUp = True
                self.x = -data.width #removes power up box from screen
                data.startTime = pygame.mixer.music.get_pos()

######################################################################
    # Menu Screen
######################################################################

def menuSurface(data, screen): #display in menu
    if data.backInit == 0:
        backg = pygame.image.load('/Users/AlexYu/Documents/CMU/Freshman/112/Term Project/menu1.png')
        #from http://images4.alphacoders.com/246/246566.jpg
        data.menu = pygame.transform.scale(backg, (data.width, data.height))
        data.backInit += 1
    screen.blit(data.menu, (0, 0))
    scale1, scale2, = 20, 8
    smallSize, largeSize = data.width/scale1, data.width/scale2
    data.smallMenuSize = smallSize
    margin = smallSize/2
    font = 'freesansbold.ttf'
    #initializes font and size for smaller texts
    menu, menuColor = ["Play", "Instructions", "Options"], data.white #texts to draw
    titleX = titleY = data.width/scale1 #x and y pos for title text
    y = 2*titleY + largeSize #starting y position for menu options
    if data.menuInit == 0:
        data.menuOptions = []
        for button in menu:
            menuText = MenuButton(data, button, font, smallSize, menuColor, titleX, y)
            data.menuOptions += [menuText]
            y += smallSize + margin
        data.menuInit += 1
    for menuText in data.menuOptions:
        menuText.draw(data, screen)

def instructionsSurface(data, screen): #display in instructions menu
    #instructions on how to play the game
    screen.fill(data.black)
    size = data.width/50
    text1 = 'Welcome!' #will be centered
    text2 = ('At the menu screen, press Options to select a difficulty. You ' +
        'can also select whether or not you')
    text21 = ('want to be challenged, which will determine whether or not ' +
        'enemies will appear in the game.')
    text3 = ('At the menu screen, press Play to start the game. You will be ' + 
        'prompted to insert a song name so ') 
    text31 = ('type in the name of the sound file that you wish to play ' +
        'along to. Make sure that the file is in the') 
    text32 = ('"Songs" folder.')
    text4 = ('To move the player, press the up and down arrow keys to move ' +
        'your character up and down. To')
    text41 = ('hit the note, you must be on top of the note, and then hit ' +
       'the space bar. You can also press')
    text42 = ('Q at any time to exit the game and go back to the menu.')
    text5 = ('There are also power ups that you can collect to help you do ' +
        'better. Your score, current standing,')
    text51 = ('and time left are displayed at the bottom. If you ' +
        'run into enemies, or your standing is too low, you')
    text52 = ('will lose automatically.')
    text6 = 'Have fun!'
    lineSpace = size/4 #space between lines
    sectSpace = size #space between sections
    font, color = pygame.font.Font('freesansbold.ttf', size), data.gray
    text1Img, text2Img = makeText(text1,font,color), makeText(text2,font,color)
    text3Img, text4Img = makeText(text3,font,color), makeText(text4,font,color)
    text5Img, text6Img = makeText(text5,font,color), makeText(text6,font,color)
    text21Img =makeText(text21,font,color)
    text31Img,text32Img =makeText(text31,font,color),makeText(text32,font,color)
    text41Img,text42Img =makeText(text41,font,color),makeText(text42,font,color)
    text51Img,text52Img =makeText(text51,font,color),makeText(text52,font,color)
    height = text1Img.get_height() #height of font
    x1, y1 = data.width/2 - text1Img.get_width()/2, sectSpace
    x2 = x3 = x4 = x5 = x6 = sectSpace
    y2 = 2*sectSpace + height
    y21 = y2 + height + lineSpace
    y3 = y21 + height + sectSpace
    y31 = y3 + height + lineSpace
    y32 = y31 + height + lineSpace
    y4 = y32 + height + sectSpace
    y41 = y4 + height + lineSpace
    y42 = y41 + height + lineSpace
    y5 = y42 + height + sectSpace
    y51 = y5 + height + lineSpace
    y52 = y51 + height + lineSpace
    y6 = y52 + height + sectSpace
    screen.blit(text1Img, (x1, y1))
    screen.blit(text2Img, (x2, y2))
    screen.blit(text21Img, (x2, y21))
    screen.blit(text3Img, (x3, y3))
    screen.blit(text31Img, (x3, y31))
    screen.blit(text32Img, (x3, y32))
    screen.blit(text4Img, (x4, y4))
    screen.blit(text41Img, (x4, y41))
    screen.blit(text42Img, (x4, y42))
    screen.blit(text5Img, (x5, y5))
    screen.blit(text51Img, (x2, y51))
    screen.blit(text52Img, (x2, y52))
    screen.blit(text6Img, (x6, y6))

def optionsSurface(data, screen): #display in options menu
    screen.fill(data.black)
    diff = 'Difficulty:'
    chall = 'Challenge?'
    #for drawing, need data, name, font, color, xPos, yPos):
    difficulties = ['Easy', 'Medium', 'Hard', 'CRAZY']
    challResp = ['Yes', 'No'] #responses to challenge
    largeSize, smallSize = data.width/20, data.width/30
    margin = smallSize
    font = 'freesansbold.ttf'
    largeFont, color = pygame.font.Font('freesansbold.ttf', largeSize), data.gray
    diffImg = makeText(diff, largeFont, color)
    challImg = makeText(chall, largeFont, color)
    diffX = diffY = challY = margin #top left x and y values for diffImg
    #also top y val for challImg
    challX = data.width - margin - challImg.get_width()
    screen.blit(diffImg, (diffX, diffY))
    screen.blit(challImg, (challX, challY))
    y = diffY + diffImg.get_height() + 2*margin
    if data.optionsInit == 0:
        data.options = []
        for diff in difficulties: #creates object for each difficulty option
            diffText = MenuButton(data, diff, font, smallSize, color, diffX, y)
            data.options += [diffText]
            y += 2*margin
        y = challY + challImg.get_height() + 2*margin
        for response in challResp: #creates object for each response option
            respText = MenuButton(data, response, font, smallSize, color, challX, y)
            data.options += [respText]
            y += 2*margin
        data.optionsInit += 1
    for option in data.options:
        option.draw(data, screen)

def makeText(text, font, textColor): #renders text as image
    textSurface = font.render(text, True, textColor)
    return textSurface

######################################################################
    # Draw Functions
######################################################################

def gameDrawFn(screen, data): #main draw function
    if data.backInit == 2:
        stage0 = '/Users/AlexYu/Documents/CMU/Freshman/112/Term Project/stage0.png'
#from http://upload.wikimedia.org/wikipedia/en/6/6e/Gh3_stage_final.jpg
        stage1 = '/Users/AlexYu/Documents/CMU/Freshman/112/Term Project/stage1.png'
#from http://maxskansascity.com/classic/aerosmith/images/slideshow6/GH_02.jpg
        stage2 = '/Users/AlexYu/Documents/CMU/Freshman/112/Term Project/stage2.png'
#from http://s441.photobucket.com/user/Cleanmonk33/media/stage-1.png.html?t=1237475849
        stage3 = '/Users/AlexYu/Documents/CMU/Freshman/112/Term Project/stage3.png'
#from https://earlsblog.files.wordpress.com/2008/06/938225_20080530_screen001.jpg
        stage4 = '/Users/AlexYu/Documents/CMU/Freshman/112/Term Project/stage4.png'
#from http://static.gamesradar.com/images/mb/GamesRadar/us/Games/G/Guitar%20Hero
#     %20Aerosmith/Bulk%20viewer/Misc/2008-05-01/Guitar%20Hero%20Aerosmith%20-%
#     20On%20stage%20at%20the%20Orpheum--screenshot_viewer_medium.jpg
        stage5 = '/Users/AlexYu/Documents/CMU/Freshman/112/Term Project/stage5.png'
#from http://s441.photobucket.com/user/Cleanmonk33/media/default.png.html?t=1237475892
        stages = [stage0, stage1, stage2, stage3, stage4, stage5]
        i = random.randint(0, len(stages)-1)
        backg = pygame.image.load(stages[i])
        data.background = pygame.transform.scale(backg,(data.width,data.height))
        data.backInit += 1
    screen.blit(data.background, (0,0)) #fills screen with background image
    drawRows(screen, data) #draws rows for notes
    data.drawnNotes = int(round(float(data.sampleLength)/data.duration/data.FPS))
    #how many notes that need to be drawn per frame
    delay = data.sampleLength/data.duration
    if (data.frames % (data.FPS*data.duration)) == 0 and data.frames != 0:
        data.drawStart += data.sampleLength #increases start at new samples
        if data.currentSlice == 0:
            data.drawStart -= (data.sampleLength - data.drawEnd)
            #evens out decrease in start and end
        data.drawStart -= delay #allows notes to be drawn until passed
    data.drawEnd += data.drawnNotes
    if len(data.notes) > 0:
        for note in data.notes[data.drawStart:data.drawEnd]:
            if note != 0:
                note.draw(data, screen) #draws note
    if not pygame.key.get_pressed()[pygame.K_SPACE]:
        playerImg = '/Users/AlexYu/Documents/CMU/Freshman/112/Term Project/run.png'
        data.player.draw(data, screen, playerImg) #draws running player
    powerUpsInit(data) #initializes powerups
    if data.enemy:
        enemiesInit(data) #initializes enemies
    for powerup in data.powerups: #draws powerups if there are any
        powerup.draw(data, screen)
    for enemy in data.enemies: #draws enemies if there are any
        enemy.draw(data, screen)
    drawGameStats(screen, data) #draws stats at bottom of screen

def drawRows(screen, data): #draws rows for player to move along
    for row in xrange(data.rows + 1):
        x0, y0 = 0, data.margin + row*data.rowHeight
        x1, y1 = data.width, y0
        pygame.draw.line(screen, data.white, (x0, y0), (x1, y1), 5)

def drawGameStats(screen, data): #draws stats at bottom of screen
    time = pygame.mixer.music.get_pos()/1000
    timeLeft = data.totalTime - time
    data.minutes = timeLeft/60
    data.seconds = timeLeft % 60
    streak = 'Current Streak: ' + str(data.streak)
    if data.seconds < 10: secString = '0' + str(data.seconds)
    else: secString = str(data.seconds)
    timeTxt = 'Time: ' + str(data.minutes) + ':' + secString
    if data.rating < 10: #resulting rating based on data.rating value
        rating = 'BOOOO'
        ratColor = (255, 0, 0)
        data.mode = 'end'
    elif data.rating < 50: 
        rating = 'Bad'
        ratColor = (246, 51, 51)
    elif data.rating < 100: 
        rating = 'OK'
        ratColor = (250, 250, 22)
    elif data.rating < 200: 
        rating = 'Good'
        ratColor = (78, 255, 102)
    elif data.rating >= 300: 
        rating = 'AMAZING!'
        ratColor = (0, 255, 0)
        if data.sliceN not in data.powerUpsPos: data.powerUpsPos += [data.sliceN]
    size = data.width/30
    font = pygame.font.Font('freesansbold.ttf', size)
    streakText = makeText(streak, font, data.white)
    timeText = makeText(timeTxt, font, data.white)
    ratingText = makeText(rating, font, ratColor)
    margin = size/2
    height = data.height - data.statsRowHeight
    screen.blit(streakText, (margin, height))
    screen.blit(timeText, (data.width - margin - timeText.get_width(), height))
    ratingX = data.width/2 - ratingText.get_width()/2
    screen.blit(ratingText, (ratingX, height))

######################################################################
    # End Game Screen
######################################################################

def endSurface(data, screen): #screen for end of game with stats
    screen.fill(data.black)
    percent = 100*float(data.score)/data.total
    if percent < 60: rating = "BOOOOOO"
    elif percent < 70: rating = "BAD"
    elif percent < 80: rating = "MEH"
    elif percent < 90: rating = "GOOD"
    else: rating = "WOOOWWW"
    xScale, yScale, widthScale, heightScale = 3.0/8, 1.0/6, 1.0/4, 2.0/3
    xPos, yPos = data.width*xScale, data.height*yScale
    rectWidth, rectHeight = data.width*widthScale, data.height*heightScale
    outlineScale = 80
    outline = data.width/outlineScale #outline of box
    pygame.draw.rect(screen,data.gray,(xPos,yPos,rectWidth,rectHeight),outline)
    margin = outline #margin between text and outline of box
    drawStats(data,screen,int(percent),rating,xPos+margin,yPos+margin,margin)
    restart = 'Press ENTER to try again!'
    scale = 70
    size = data.width/scale #size of all of the text
    textFont, color = pygame.font.Font('freesansbold.ttf', size), data.gray
    restartText = makeText(restart, textFont, data.white)
    restartX = data.width/2 - restartText.get_width()/2
    restartY = yPos + rectHeight - margin - restartText.get_height()
    screen.blit(restartText, (restartX, restartY))

def drawStats(data, screen, percent, rating, xPos, yPos, margin):
    #displays the stats from the game and how to restart
    percent, streak = str(percent), str(data.maxStreak)
    per, rat, strk = 'PERCENTAGE:', 'RATING:', 'LONGEST STREAK:'
    scale = 70
    size = data.width/scale #size of all of the text
    textFont = pygame.font.Font('freesansbold.ttf', size)
    #creates the images
    perText = makeText(per, textFont, data.gray)
    ratText = makeText(rat, textFont, data.gray)
    strkText = makeText(strk, textFont, data.gray)
    percentText = makeText(percent, textFont, data.gray)
    ratingText = makeText(rating, textFont, data.gray)
    streakText = makeText(streak, textFont, data.gray)
    perX = ratX = strkX = xPos
    percentX = ratingX = streakX = data.width/2 + 3*margin
    perY = percentY = yPos
    strkY = streakY = perY + size + margin
    ratY = ratingY = strkY + size + margin
    screen.blit(perText, (perX, perY)) #renders image
    screen.blit(ratText, (ratX, ratY))
    screen.blit(strkText, (strkX, strkY))
    screen.blit(percentText, (percentX, percentY))
    screen.blit(ratingText, (ratingX, ratingY))
    screen.blit(streakText, (streakX, streakY))

######################################################################
    # Event Functions
######################################################################

def termProjectKeyFn(event, screen, data): #main key function
    if data.mode == 'instructions' or data.mode == 'options':
        menuKeyFn(event, data)
    elif data.mode == 'songInput':
        inputKeyFn(event, data)
    elif data.mode == 'try again':
        inputKeyFn(event, data)
    elif data.mode == 'play': #separates various stages of the program 
        playKeyFn(event, screen, data)
    elif data.mode == 'end': #restarts game
        endKeyFn(event, data)

def menuKeyFn(event, data):
    if event.key == pygame.K_BACKSPACE:
        data.mode = 'menu'

def inputKeyFn(event, data):
    if event.key == pygame.K_BACKSPACE:
        if len(data.inputPhrase) > 0: data.inputPhrase.pop(len(data.inputPhrase)-1)
    elif event.key == pygame.K_RETURN: 
        filename = findFile('Songs',string.join(data.inputPhrase,''), data)
        if filename != '':
            data.song = '/Users/AlexYu/Documents/CMU/Freshman/112/Term Project/' + filename
            data.mode = 'play'
        else: data.mode = 'try again'
    elif event.key == pygame.K_MINUS: data.inputPhrase.append("-")
    elif event.key <= 127: data.inputPhrase.append(chr(event.key))

def playKeyFn(event, screen, data):
    if event.key == pygame.K_UP: #moves player up
        if data.player.y > 4*data.margin:
            data.player.y -= data.rowHeight
    if event.key == pygame.K_DOWN: #moves player down
        if data.player.y < data.height - data.rowHeight - data.margin - data.statsRowHeight:
            data.player.y += data.rowHeight
    if event.key == pygame.K_q: #quits game
        termProjectInitFn(data)
        data.mode = 'menu'
        pygame.mixer.music.stop()
    if event.key == pygame.K_SPACE:
        (noteNo, success) = collisionTest(data)
        if success:
            showCollision(data, screen, noteNo)
    else: 
        playerImg = '/Users/AlexYu/Documents/CMU/Freshman/112/Term Project/run.png'
        data.player.draw(data, screen, playerImg) #draws running player

def endKeyFn(event, data):
    if event.key == pygame.K_RETURN:
        pygame.mixer.music.stop()
        termProjectInitFn(data)
        data.mode = 'menu'

def collisionTest(data): #tests if player hits note or not or power up
    data.hit = data.onHit = 0
    for powerup in data.powerups: #check if player hit powerup
        powerup.opened(data)
    for i in xrange(len(data.notes)-1):
        note = data.notes[i]
        if note != 0 and (data.player.width > note.x):
            if data.poweredUp:
                data.total += 1
                data.hit += 1
                if note.kind == 'note':
                    data.onHit += 1
                return (i, True)
            elif data.player.y > note.y and data.player.y < note.height:
                data.total += 1
                data.hit += 1
                if note.kind == 'note':
                    data.onHit += 1
                return (i, True)
    return (0, False)

def enemyCollision(data, screen): #checks if player hit enemy
    dec = 0
    for i in xrange(len(data.enemies)):
        enemy = data.enemies[i-dec]
        enemy.hit(data, screen)
        if enemy.collide: 
            data.enemies.pop(i-dec)
            dec += 1

def showCollision(data, screen, i): #shows that successfully hit the note
    note = data.notes[i]
    noteImg = '/Users/AlexYu/Documents/CMU/Freshman/112/Term Project/fire.png'
    note.image = pygame.image.load(noteImg)
    #image from http://vignette4.wikia.nocookie.net/guitarhero/images/0/04/GH2-cooperative.jpg/revision/latest?cb=20110204015503
    playerImg = '/Users/AlexYu/Documents/CMU/Freshman/112/Term Project/hit.png'
    data.player.draw(data, screen, playerImg)
    #image from http://i.ytimg.com/vi/k-oDTUr5ZpU/hqdefault.jpg
    scale = (float(data.rowHeight)/data.height)/3
    note.image = pygame.transform.scale(note.image, (int(data.width*scale), int(data.rowHeight*0.75)))
    data.score += 1

def removeDone(data): #removes any notes and powerups that are off screen
    data.removed = data.onRemoved = 0 #number of notes removed
    for i in xrange(len(data.notes)): #removes notes that have passed
        i -= data.removed
        note = data.notes[i]
        if note != 0:
            if note.x < 0:
                data.notes.pop(i)
                data.removed += 1
                data.total += 1
                if note.kind == 'note':
                    data.onRemoved += 1
    dec = 0
    for i in xrange(len(data.powerups)): #removes powerups that have passed
        powerup = data.powerups[i-dec]
        if powerup.x < 0:
            data.powerups.pop(i-dec)
            dec += 1
    dec = 0
    for i in xrange(len(data.enemies)): #removes enemies that have passed
        enemy = data.enemies[i-dec]
        if enemy.x < 0:
            data.enemies.pop(i-dec)
            dec += 1

def termProjectMouseFn(event, data): #main mouse function
    data.clicked = False #whether or not a button was clicked
    if data.mode == 'menu':
        menuMouseFn(event, data)
    elif data.mode == 'options':
        optionsMouseFn(event, data)
    elif data.mode == 'songInput':
        inputMouseFn(event, data)

def menuMouseFn(event, data):
     for i in xrange(len(data.menuOptions)):
        option = data.menuOptions[i]
        option.size = data.smallMenuSize
        mouseX, mouseY = pygame.mouse.get_pos()[0], pygame.mouse.get_pos()[1]
        if mouseX > option.x and mouseX < option.width: #checks x coordinates
            if mouseY > option.y and mouseY < option.height: #checks y coords
                data.clicked = True
                option.action(data)

def optionsMouseFn(event, data):
    for i in xrange(len(data.options)):
        option = data.options[i]
        option.size = data.smallOptionSize
        mouseX, mouseY = pygame.mouse.get_pos()[0], pygame.mouse.get_pos()[1]
        if mouseX > option.x and mouseX < option.width: #checks x coordinates
            if mouseY > option.y and mouseY < option.height: #checks y coords
                data.clicked = True
                option.action(data)

def inputMouseFn(event, data):
    option = data.back
    mouseX, mouseY = pygame.mouse.get_pos()[0], pygame.mouse.get_pos()[1]
    if mouseX > option.x and mouseX < option.width: #checks x coordinates
        if mouseY > option.y and mouseY < option.height: #checks y coords
            data.clicked = True
            option.action(data)

######################################################################
    # User Input Screen and File Searching
######################################################################
#FROM PYGAME CODE REPOSITORY: http://www.pygame.org/pcr/inputbox/inputbox.py
def getKey(): #gets key that was pressed
    keyPressed = False #whether or not a key has been pressed
    while not keyPressed:
        event = pygame.event.poll()
        if event.type == pygame.KEYDOWN: return event.key
        else: pass

def writeInput(data, screen, message): #shows what user is typing
    margin = size = screen.get_width()/20
    boxWidth, boxHeight = data.width/2 - margin, data.height/20 #width and height from halfway
    font = pygame.font.Font('freesansbold.ttf', size)
    if len(message) != 0:
        inputText = makeText(message, font, data.custom)
        screen.blit(inputText, (data.width/2 - boxWidth, data.height/2-boxHeight))

def inputBoxSurface(data, screen, question, inputPhrase): #displays box for input
    if data.backInit == 1:
        loading = '/Users/AlexYu/Documents/CMU/Freshman/112/Term Project/loading.png'
        #image from http://i37.tinypic.com/21ooj29.png
        loading = pygame.image.load(loading)
        data.loading = pygame.transform.scale(loading, (data.width, data.height))
        data.backInit += 1
    screen.blit(data.loading, (0, 0))
    size = data.width/25
    margin = data.width/20
    font = pygame.font.Font('freesansbold.ttf', size)
    boxWidth, boxHeight = data.width/2 - margin, data.height/20 #width and height from halfway
    pygame.draw.rect(screen, data.black, (data.width/2-boxWidth, 
        data.height/2-boxHeight, 2*boxWidth, 2*boxHeight), 3)
    prompt = makeText(question, font, data.custom)
    textWidth, textHeight = prompt.get_width(), prompt.get_height()
    screen.blit(prompt, (data.width/2 - textWidth/2, data.height/2 - boxHeight - 3.0*textHeight/2))
    writeInput(data, screen, string.join(data.inputPhrase,"")) #displays the key
    x = data.width/2 - size
    y = data.height/2 + boxHeight + margin
    backFont = 'freesansbold.ttf'
    data.back = MenuButton(data, 'BACK', backFont, size, data.custom, x, y)
    data.back.draw(data, screen)

def findFile(path, targetFile, data, foundFile = ''): 
#searches for the file name that was input
    if os.path.isdir(path) == False: #gets size if at file
        data.mode = 'play'
        return path
    else:
        for filename in os.listdir(path):
            actualPath = path + "/" + filename
            user = findFile(actualPath, targetFile, data)
            #gets size and path recursively if actualPath is folder
            folders = user.split("/")
            if os.path.splitext(folders[len(folders)-1].lower())[0] == targetFile:
                foundFile = user
        return foundFile

######################################################################
                        # SOUND ANALYSIS PART
######################################################################
######################################################################
    # Pitch Analysis
######################################################################

#FROM AUBIO DEMOS
def pitchSampling(data, filename): #calculates pitch at constant rate from input file
    winsize, hopsize = 4096, 512
    s = aubio.source(filename, data.samplerate, hopsize)
    data.samplerate = s.samplerate
    tolerance = 0.8
    pitch_o = aubio.pitch('yinfft', winsize, hopsize, data.samplerate)
    pitch_o.set_unit('freq')
    pitch_o.set_tolerance(tolerance)
    pitches = []
    confidences = []
    total_frames = 0 #total number of frames read
    while True:
        samples, read = s()
        pitch = pitch_o(samples)[0]
        confidence = pitch_o.get_confidence()
        pitches += [pitch]
        confidences += [confidence]
        total_frames += read
        if read < data.hopsize: break #breaks if finished with leftover part
    if 0: sys.exit(0)
    data.sampleLength = len(pitches) #number of pitches in each sample
    return pitches

######################################################################
    # Slicing of Sound File
######################################################################

#FROM AUBIO DEMOS
def slicing(data, filename): #slices file into pieces to analyze
    source_file = filename
    data.duration = 3 #length of each sample in seconds
    source_base_name, source_ext = os.path.splitext(os.path.basename(source_file))
    #splits name and extension
    hopsize = data.hopsize
    data.sliceNo, total_frames_written, read = 0, 0, hopsize #which slice, how many frames
    def new_sink_name(source_base_name, sliceNo, duration = data.duration): #creates name for sink
        return source_base_name + '_%02.3f' % (data.sliceNo*data.duration) + '.wav'
    f = aubio.source(source_file, 0, hopsize)
    samplerate = f.samplerate
    g = aubio.sink(new_sink_name(source_base_name, data.sliceNo), samplerate)
    while read == hopsize:
        vec, read = f()
        start_of_next_region = int(data.duration * samplerate * (data.sliceNo + 1))
        remaining = start_of_next_region - total_frames_written
        # number of samples remaining is less than what we got
        if remaining < read: # write remaining samples from current region
            if remaining != 0:
                g(vec[0:remaining], remaining)
            del g # close this file
            data.sliceNo += 1
            # create a new file for the new region
            g = aubio.sink(new_sink_name(source_base_name, data.sliceNo), samplerate)
            g(vec[remaining:read], read - remaining)
            # write the remaining samples in the new file
        else:
            if read != 0:
                g(vec[0:read], read)
        total_frames_written += read
    total_duration = total_frames_written / float(samplerate)
    data.sliceNo += 1
    del f, g # close source and sink files

######################################################################
    # Tempo Detection
######################################################################
#FROM AUBIO DEMOS
def getDuration(data, filename): #finds tempo of song being played
    winsize = data.winsize # fft size
    hopsize = winsize/2 # hop size
    samplerate = data.samplerate
    s = aubio.source(filename, samplerate, hopsize)
    samplerate = s.samplerate
    o = aubio.tempo('default', winsize, hopsize, samplerate)
    beats = [] # list of beats, at which sample
    total_frames = 0 # total number of frames read
    totalTime = 0 #keeps track of total length of song
    while True:
        samples, read = s()
        totalTime += len(samples)/float(samplerate) #time elapsed per iteration
        is_beat = o(samples)
        if is_beat:
            this_beat = int(total_frames + is_beat[0] * hopsize)
            beats.append(this_beat/float(samplerate))
        total_frames += read
        if read < hopsize: break #breaks if finished with leftover part
    return int(totalTime) + 1

######################################################################
    # Onset Detection
######################################################################

#FROM AUBIO DEMOS
def onset(data, filename): #finds times when new note is played
    winsize = data.winsize # fft size
    hopsize = winsize/2 # hop size
    samplerate = data.samplerate
    s = aubio.source(filename, samplerate, hopsize)
    samplerate = s.samplerate
    o = aubio.onset('default', winsize, hopsize, samplerate)
    onsets = [] # list of onsets, at what sample that it occurs
    total_frames = 0 # total number of frames read
    while True:
        samples, read = s()
        if o(samples):
            index = int(o.get_last()/float(read))
            index += data.currentSlice*data.sampleLength
            onsets.append(int(round(index))) #indexes for pitches list
        total_frames += read
        if read < hopsize: break
    return onsets

########################## FIN #########################
termProject()