import pygame
from random import randrange
import os
import neat
pygame.font.init()  # initialize font

WIN_WIDTH = 600
WIN_HEIGHT = 800

FLOOR = 730 # this is the maximum legal height of the bird
FONT = pygame.font.SysFont("arial", 50)

DRAW_LINES = False # this draws lines to see what each agent can see

WIN = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
pygame.display.set_caption("Flappy Bird")

pipe_img = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","pipe.png")).convert_alpha())
bg_img = pygame.transform.scale(pygame.image.load(os.path.join("imgs","bg.png")).convert_alpha(), (600, 900))
bird_images = [pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","bird" + str(x) + ".png"))) for x in range(1,4)]
base_img = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","base.png")).convert_alpha())

gen = 0 #initialising the first generation as 0

'''
The basic logic of this game is that there is a bird that must pass through pipes to survive.The birds x axis does not move,
rather the pipes and the base move towards it. The bird can either jump or choose to fall. If it collides with the ceiling or
pipes or the base/ground the game is reset.

'''


class Bird:
   #this is similar to the sprite class

    MAX_ROTATION = 25
    IMGS = bird_images
    ROT_VEL = 20
    ANIMATION_TIME = 5

    def __init__(self, x, y):
      
        self.x = x #this will stay constant during the entire game
        self.y = y
        #setting the x and y values as 250,350 no specific reason why tho

        self.tilt = 0  # degrees to tilt

        self.tick_count = 0 #this acts a the time compoment of the physics eqation 

        self.vel = 0 #this is reposible for jump of the bird
        self.height = self.y #the height of the bird is obviously the y coordinate of the class object

        self.img_count = 0 #this is the counter for the bird animation 
        self.img = self.IMGS[0]

    def jump(self):
      
        self.vel = -10.5 #changes the jump height of the bird by manipulating the physics equation
        self.tick_count = 0
        self.height = self.y

    def move(self):
        
        self.tick_count += 1

        # for downward acceleration
        displacement = self.vel*(self.tick_count) + 0.5*(3)*(self.tick_count)**2  # calculate displacement ut + 1/2at^2

        # terminal velocity makes sure that the birds dont fall too fast, makes gameplay smoother
        if displacement >= 16:
            displacement = (displacement/abs(displacement)) * 16

        if displacement < 0:
            displacement -= 2

        self.y = self.y + displacement #updates y axis value.

        if displacement < 0 or self.y < self.height + 50:  # tilt up
            if self.tilt < self.MAX_ROTATION:
                self.tilt = self.MAX_ROTATION
        else:  # tilt down
            if self.tilt > -90:
                self.tilt -= self.ROT_VEL

    def draw(self, win):
        
        self.img_count += 1

        # For animation of bird, loop through three images
        if self.img_count <= self.ANIMATION_TIME:
            self.img = self.IMGS[0]
        elif self.img_count <= self.ANIMATION_TIME*2:
            self.img = self.IMGS[1]
        elif self.img_count <= self.ANIMATION_TIME*3:
            self.img = self.IMGS[2]
        elif self.img_count <= self.ANIMATION_TIME*4:
            self.img = self.IMGS[1]
        elif self.img_count == self.ANIMATION_TIME*4 + 1:
            self.img = self.IMGS[0]
            self.img_count = 0

        # tilt the bird
        blitRotateCenter(win, self.img, (self.x, self.y), self.tilt)

    def get_mask(self):
        """
        gets the mask for the current image of the bird
        :return: None
        """
        return pygame.mask.from_surface(self.img)


class Pipe:
    
    GAP = 200 #this is the gap of the pipes
    VEL = 5 #speed of the pipes

    def __init__(self, x):
        
        self.x = x #we set this as 700, which is out of the game window as we want the birds to stabilize themselves upon creation
        self.height = 0

        # where the top and bottom of the pipe is , this is the x axis of the pipes which must be same
        self.top = 0
        self.bottom = 0

        self.PIPE_TOP = pygame.transform.flip(pipe_img, False, True)
        self.PIPE_BOTTOM = pipe_img

        self.passed = False #whether the bird has passed through the pipe or not

        self.set_height()

    def set_height(self):
       
       #sets the height of the pipes randomly
        self.height = randrange(50, 450)
        self.top = self.height - self.PIPE_TOP.get_height()
        self.bottom = self.height + self.GAP

    def move(self):
        #moves the pipe
        self.x -= self.VEL

    def draw(self, win):
        
        # draw top pipes
        win.blit(self.PIPE_TOP, (self.x, self.top))
        # draw bottom pipe
        win.blit(self.PIPE_BOTTOM, (self.x, self.bottom))


    def collide(self,bird,base):
       
        bird_mask = bird.get_mask()
        top_mask = pygame.mask.from_surface(self.PIPE_TOP)
        bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)
        base_mask = pygame.mask.from_surface(base.IMG)


        ba_offset = (bird.x,730-round(bird.y))
        top_offset = (self.x - bird.x, self.top - round(bird.y)) #round is used to round off a value
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))

        b_point = bird_mask.overlap(bottom_mask, bottom_offset) #check if bird collides wittom pipe
        t_point = bird_mask.overlap(top_mask,top_offset) #check if bird collides wittom pipe
        ba_point = bird_mask.overlap(base_mask,ba_offset)

        if b_point or t_point or ba_point:
            return True

        return False

class Base:
    #there are 2 images that are played one after the other giving the illusion of infinite base
   
    VEL = 5 #same as the pipes
    WIDTH = base_img.get_width()
    IMG = base_img

    def __init__(self, y):
        
        self.y = y
        self.x1 = 0 #one for 1st pic and one for the one after that pic
        self.x2 = self.WIDTH

    def move(self):
        #moves the floor and replaces with new pic
        self.x1 -= self.VEL
        self.x2 -= self.VEL
        if self.x1 + self.WIDTH < 0:
            self.x1 = self.x2 + self.WIDTH

        if self.x2 + self.WIDTH < 0:
            self.x2 = self.x1 + self.WIDTH

    def draw(self, win):

        win.blit(self.IMG, (self.x1, self.y))
        win.blit(self.IMG, (self.x2, self.y))


def blitRotateCenter(surf, image, topleft, angle):
  
    rotated_image = pygame.transform.rotate(image, angle)
    new_rect = rotated_image.get_rect(center = image.get_rect(topleft = topleft).center)

    surf.blit(rotated_image, new_rect.topleft)

def draw_window(win, birds, pipes, base, score, gen, pipe_ind):
   
    if gen == 0:
        gen = 1
    win.blit(bg_img, (0,0))

    for pipe in pipes:
        pipe.draw(win)

    base.draw(win)
    for bird in birds:
        # draw lines from bird to pipe
        if DRAW_LINES:
            try:
                #center of bird to center of pipe
                pygame.draw.line(win, (255,0,0), (bird.x+bird.img.get_width()/2, bird.y + bird.img.get_height()/2), (pipes[pipe_ind].x + pipes[pipe_ind].PIPE_TOP.get_width()/2, pipes[pipe_ind].height), 5)
                pygame.draw.line(win, (255,0,0), (bird.x+bird.img.get_width()/2, bird.y + bird.img.get_height()/2), (pipes[pipe_ind].x + pipes[pipe_ind].PIPE_BOTTOM.get_width()/2, pipes[pipe_ind].bottom), 5)
            except:
                pass

        # draw bird
        bird.draw(win)

    # display score
    score_label = FONT.render("Score: " + str(score),1,(255,255,255))
    win.blit(score_label, (WIN_WIDTH - score_label.get_width() - 15, 10))

    # displaygenerations
    score_label = FONT.render("Gens: " + str(gen-1),1,(255,255,255))
    win.blit(score_label, (10, 10))

    # display alive
    score_label = FONT.render("Alive: " + str(len(birds)),1,(255,255,255))
    win.blit(score_label, (10, 50))

    pygame.display.update()


def eval_genomes(genomes, config):
    #evaluates the different genomes and gives their fitness value

    global WIN, gen
    gen += 1

    # start by creating lists of the genome, nn and the bird 
    # the genome contains the structure and the parameters of the nn
    # bird object that uses the nn to play

    nets = []
    birds = []
    ge = []

    for genome_id, genome in genomes:
        genome.fitness = 0  # start with fitness level of 0
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        nets.append(net)
        birds.append(Bird(230,350))
        ge.append(genome)

    base = Base(FLOOR)
    pipes = [Pipe(700)]
    score = 0

    #clock controlls the speed of the game
    clock = pygame.time.Clock()

    run = True
    while run and len(birds) > 0:
        clock.tick(30)

        for event in pygame.event.get():
            #if we click the cross mark
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()
                break

        # determine whether to use the first or second as list output may be out of range
        pipe_ind = 0
        if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width(): 
            pipe_ind = 1            

        # give each bird a fitness of 0.1 for each frame it stays alive                                                     
        for x, bird in enumerate(birds):  
            ge[x].fitness += 0.1
            bird.move()

            # send bird location, top pipe location and bottom pipe location and determine from network whether to jump or not
            output = nets[birds.index(bird)].activate((bird.y, abs(bird.y - pipes[pipe_ind].height), abs(bird.y - pipes[pipe_ind].bottom)))

            if output[0] > 0.5:  # we use a tanh activation function so result will be between -1 and 1. if over 0.5 jump
                bird.jump()

        base.move()

        rem = []#removing the pipes
        add_pipe = False
        for pipe in pipes:
            pipe.move()
            # check for collision
            for bird in birds:
                if pipe.collide(bird,base):
                    ge[birds.index(bird)].fitness -= 1
                    nets.pop(birds.index(bird))
                    ge.pop(birds.index(bird))
                    birds.pop(birds.index(bird))

            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                rem.append(pipe)

            if not pipe.passed and pipe.x < bird.x:
                pipe.passed = True
                add_pipe = True

        if add_pipe:
            score += 1
            for genome in ge:
                genome.fitness += 5
            pipes.append(Pipe(WIN_WIDTH))

        for r in rem:
            pipes.remove(r)

        for bird in birds:
            if bird.y + bird.img.get_height() - 10 >= FLOOR or bird.y < -50:
                nets.pop(birds.index(bird))
                ge.pop(birds.index(bird))
                birds.pop(birds.index(bird))

        draw_window(WIN, birds, pipes, base, score, gen, pipe_ind)

def run(config_file):
    
    # this code runs the NEAT algorithm to train the nn to play flappy bird.
    
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                         neat.DefaultSpeciesSet, neat.DefaultStagnation,
                         config_file)

    # Create the population, which is the top-level object for a NEAT run.
    p = neat.Population(config)

    # Add a stdout reporter to show progress in the terminal.
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)
    #p.add_reporter(neat.Checkpointer(5))

    # Run for up to 50 generations.
    winner = p.run(eval_genomes, 50)

    # show final stats
    print('\nBest genome:\n{!s}'.format(winner))


if __name__ == '__main__':
    # Determine path to configuration file. This path manipulation is
    # here so that the script will run successfully regardless of the
    # current working directory.
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'config-feedforward.txt')
    run(config_path)
