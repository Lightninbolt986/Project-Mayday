import csv, math, pygame, pickle, serial 
try:
    ser = serial.Serial('COM3', 9600)
except:
    pass
ser.flush(); ser.flushInput(); ser.flushOutput()

print("loading data")
terrainFile = open("terrainDataHighRes.CSV") # swap this for terrainDataHighRes.CSV, prpgram will automatically detect and use higher resolution
terrain = list(csv.reader(terrainFile))
print("data has been loaded")
# test comit
framerate = 100 #frames per second
clock = pygame.time.Clock()
window = pygame.display.set_mode((800,500))
pygame.init()

latitudes = len(terrain)
longitudes = len(terrain[0])
resolution = longitudes/360 #1 to 10
height = 0
wind = (0,0)

def findTerrainHeight(la,lo): #latitude and longitude +for N -for S +for W -for E
    global resolution
    la *= -1
    la += 90
    lo *= -1
    lo += 180
    rla = round(la*resolution)/resolution #rounded latitude 
    rlo = round(lo*resolution)/resolution #rounded longitude
    x = (float(terrain[int(rla*resolution)][int(rlo*resolution)]))
    if x==99999:
        return 0
    else:
        return x

def startUp():
    f = open("airports.csv","r")
    reader = list(csv.reader(f))
    print("\n".join([f'{port[4]} : {port[1]}' for port in reader]))
    codes = [port[4] for port in reader]
    while True:
        userCode = input("Enter airport from the following:").upper()
        if userCode in codes:
            selected = codes.index(userCode)
            print("Simulation started")
            return float(reader[selected][2]), -float(reader[selected][3]), float(reader[selected][6])
        else: 
            print("Cannot recognise code, try again")

warning = "unknown"
allFlaps = [0,10,20,30]
class Plane:
    def __init__(self, la=0, lo=0, heading=0, height=0):
        self.la = la
        self.lo = lo
        self.heading = heading
        self.height = height #above sea in m
        self.speed = 0 #in knots
        self.pitch = 0
        self.roll = 0
        self.pitcht = 0 #degrees per second 
        self.rollt = 0
        self.yawt = 0
        self.thrustl = 0
        self.thrustr = 0
        self.flaps = 0
        self.state = "landed"
        self.headwind = 0
        self.crosswind = 0
    
    def pitchSpeedDropOG(self,speed,pitch): #uses old curve
        exponent = (pitch-90)/18
        return speed/(1+(math.e**exponent))
    
    def pitchSpeedDrop(self,speed,pitch):
        return (speed/(1+(math.e**(pitch/30))))+(speed/2)

    def physics(self):
        global i
        global warning, heightG
        self.roll += self.rollt/framerate
        self.heading += self.yawt/framerate
        self.pitch += self.pitcht/framerate

        self.speed = self.thrustl + self.thrustr
        self.speed = self.pitchSpeedDrop(self.speed,-self.pitch)
        self.yawt = (self.thrustl - self.thrustr)*0.01 #assymetry constant
        self.rollt = 0
        self.pitcht = 0
        self.airspeed = 0

        self.headwind = wind[0]*math.cos((wind[1]-self.heading)*math.pi/180)
        self.crosswind = -wind[0]*math.sin((wind[1]-self.heading)*math.pi/180)

        minSpeed = 400 - p.flaps*10
        if (minSpeed > p.speed+ + p.headwind) and p.state == "airborne":
            p.pitcht = 1
            warning = "underspeed"
        elif (minSpeed+100) < p.speed + p.headwind:
            p.pitcht = -1
            warning = "overspeed"
        else:
            warning = "none"
        
        if (heightG > 5) and i>5: #add crashed state here somehow
            p.state = "airborne"
    
    def resolveMotion(self):
        if self.state == "airborne":
            self.airspeed = self.speed + self.headwind
        else:
            self.airspeed = self.speed
        verticalSpeed = -(self.airspeed)*math.sin(self.pitch*(math.pi/180)) #degree per second convertor
        self.height += verticalSpeed*0.51444/framerate #knots to m/s
        horizontalSpeed = self.airspeed*math.cos(self.pitch*math.pi/180)/216000
        ycomp = horizontalSpeed*math.cos(self.heading*math.pi/180)
        xcomp = -horizontalSpeed*math.sin(self.heading*math.pi/180) 
        self.la += ycomp/framerate
        self.lo += xcomp/framerate

    def formatState(self):
        if self.la>=0:
            fla = str(round(self.la,3))+"°N"
        else:
            fla = str(round(-self.la,3))+"°S"
        if self.lo>=0:
            flo = str(round(self.lo,3))+"°W"
        else:
            flo = str(round(-self.lo,3)) +"°E"
        return [fla,flo,str(round(self.heading,2))+"°"]
    
    def balanceThrust(self):
        avThrust = (self.thrustl + self.thrustr) / 2
        self.thrustl = self.thrustr = avThrust
    
    def flapUp(self):
        if p.flaps!= allFlaps[-1]:
            p.flaps = allFlaps[allFlaps.index(p.flaps)+1]
    def flapDown(self):
        if p.flaps!= allFlaps[0]:
            p.flaps = allFlaps[allFlaps.index(p.flaps)-1]
    
    def getWind(self):
        with open('give.bat', 'wb') as f:
            pickle.dump((self.la,self.lo), f)
        try:
            with open("take.bat","rb") as f:
                return pickle.load(f)
        except FileNotFoundError:
            return(0,0)

#ui rendering
font = pygame.font.Font('freesansbold.ttf', 32)
sfont = pygame.font.Font('freesansbold.ttf', 12)
arthor = pygame.image.load('arthor.png')
miller = pygame.image.load('miller.png')
throtfront = pygame.image.load('throtfront.png')
throtback = pygame.image.load('throtback.png')

def rot_center(image, angle, x, y):
    
    rotated_image = pygame.transform.rotate(image, angle)
    new_rect = rotated_image.get_rect(center = image.get_rect(center = (x, y)).center)

    return rotated_image, new_rect

def renderUI():
    global xinput, yinput
    
    stateText = p.formatState()
    st1,st2,st3 = font.render(stateText[0], True, (255,255,255)),font.render(stateText[1], True, (255,255,255)),font.render(stateText[2], True, (255,255,255))
    
    window.fill((0,0,0))
    window.blit(st1,(0,0))
    window.blit(st2,(160,0))
    window.blit(st3,(320,0))

    donerkabab = rot_center(arthor,p.roll,550,250)
    window.blit(donerkabab[0],donerkabab[1])
    pitchoffset = (150/45)*p.pitch
    millerkabab = rot_center(miller,p.roll,550,250)
    window.blit(millerkabab[0],(millerkabab[1][0]+math.sin(p.roll*math.pi/180)*pitchoffset,millerkabab[1][1]+math.cos(p.roll*math.pi/180)*pitchoffset))

    rollNotice = sfont.render("Note: Roll effects of roll are not calculated in this version of the simulation",True, (255,255,0))
    if abs(p.roll) > 5:
        window.blit(rollNotice, (200,480))
    
    if warning != "none":
        warningText = sfont.render(warning, True, (255,50,0))
        window.blit(warningText, (525,420))

    t1 = font.render("h(grnd):"+str(round(heightG)), True, (220,220,220))
    t2 = font.render("h(sea):"+str(round(p.height)), True, (220,220,220))
    t3 = font.render("flaps:"+str(p.flaps), True, (220,220,220))
    window.blit(t1, (180,300))
    window.blit(t2, (180,340))
    window.blit(t3, (180,400))

    t4 = font.render("S(grnd):"+str(round(p.speed,1)),True,(230,230,200))
    t5 = font.render("S(air):"+str(round(p.airspeed,1)),True,(230,230,200))
    window.blit(t4,(320,450))
    window.blit(t5,(320,410))

    window.blit(throtback,(-100,100))
    window.blit(throtfront,(-100,300-p.thrustl))
    window.blit(throtfront,(-22,300-p.thrustr))

    #compas rose
    pygame.draw.circle(window,(200,200,100),(300,180),70)
    pygame.draw.circle(window,(80,80,250),(300,180),65)
    pygame.draw.line(window,(190,190,220),(300,180),(300+30*math.sin(wind[1]*math.pi/180),180-30*math.cos(wind[1]*math.pi/180)),2) #wind direction (replace 0 with wind direction in degrees)
    pygame.draw.line(window,(255,0,255),(300,180),(300-50*math.sin(p.heading*math.pi/180),180-50*math.cos(p.heading*math.pi/180)),5) #plane heading

    #input cross
    pygame.draw.rect(window,(50,50,50),(655,55,100,10)) #horizontal bar
    pygame.draw.rect(window,(50,50,50),(700,10,10,100)) #vertical bar
    pygame.draw.rect(window,(200,50,200),(xinput,55,4,10)) #horizonal mover
    pygame.draw.rect(window,(200,50,200),(700,yinput,10,4))#vertical mover

    pygame.display.update()

#initialising the plane
startLa, startLo, startHeading = startUp()
startHeight = findTerrainHeight(startLa,startLo)
p = Plane(startLa,startLo,startHeading, startHeight)

def arduinoStuff():
    global xinput, yinput
    deadzone = 100
    try:
        combined = int(float((ser.readline().decode('utf-8').rstrip())))
        valA = combined//1024 -512
        valB = combined%1024 -512
    except:
        valA, valB = 0,0
    if abs(valA) > deadzone:
        p.pitcht -= valA/75
    if abs(valB) > deadzone:
        p.rollt -= valB/75
    print(valA, valB)
    xinput = (valB *50/512)+705 -2
    yinput = (valA *50/512)+60 -2

i=0
active = True
while active:
    for event in pygame.event.get():
        if event.type==pygame.QUIT:
            active = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_x:
                p.flapUp()
            if event.key == pygame.K_c:
                p.flapDown()
    keys = pygame.key.get_pressed()
    if keys[pygame.K_z]:
        p.balanceThrust()
    if keys[pygame.K_q]:
        p.yawt = 10
    elif keys[pygame.K_w]:
        p.yawt = -10
    if keys[pygame.K_d]:
        if p.state == "airborne":
            p.pitcht = 10
    elif keys[pygame.K_e]:
        p.pitcht = -10
    if keys[pygame.K_a]:
        if p.state == "airborne":
            p.rollt = 10
    elif keys[pygame.K_s]:
        if p.state == "airborne":
            p.rollt = -10
    if keys[pygame.K_r]:
        p.thrustl += 30/framerate
    elif keys[pygame.K_f]:
        p.thrustl -= 30/framerate
    if keys[pygame.K_t]:
        p.thrustr += 30/framerate
    elif keys[pygame.K_g]:
        p.thrustr -= 30/framerate
    
    #main sim loop
    #mospos = pygame.mouse.get_pos()#nein
    #xinput = mospos[0]
    #yinput = mospos[1]
        
    heightG = p.height - height #height from ground = height from sea level - terrain height
    clock.tick(framerate)
    p.physics()
    p.resolveMotion()
    arduinoStuff()
    if i%framerate==0:
        height = findTerrainHeight(p.la,p.lo)
        wind = p.getWind()
    renderUI()
    i+=1
    
