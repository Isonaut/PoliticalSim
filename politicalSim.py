
import direct.directbase.DirectStart
from panda3d.core import *
from direct.gui.DirectGui import *
from direct.gui.OnscreenText import OnscreenText
from direct.showbase.DirectObject import DirectObject
from direct.showbase.ShowBase import ShowBase
from direct.task.Task import Task
from direct.interval.IntervalGlobal import *
from pandac.PandaModules import WindowProperties
import sys

BLACK = Vec4(0, 0, 0, 1)
GRAY10 = Vec4(0.1, 0.1, 0.1, 1)
GRAY20 = Vec4(0.2, 0.2, 0.2, 1)
GRAY30 = Vec4(0.3, 0.3, 0.3, 1)
GRAY40 = Vec4(0.4, 0.4, 0.4, 1)
GRAY50 = Vec4(0.5, 0.5, 0.5, 1)
GRAY60 = Vec4(0.6, 0.6, 0.6, 1)
GRAY70 = Vec4(0.7, 0.7, 0.7, 1)
GRAY80 = Vec4(0.8, 0.8, 0.8, 1)
GRAY90 = Vec4(0.9, 0.9, 0.9, 1)
WHITE = Vec4(1, 1, 1, 1)

filter = [False, False, False]

def setClickState(button, state):
    clickState[button] = state
    
def setKeyState(key, state):
    keyState[key] = state
    
def scroll(direction):
    if mode == 4:
        for citizen in citizenIndex:
            citizen.move(citizen.getPosition()*(5+direction)/5)
            
    else:
        z = base.camera.getZ()
        if z+direction*5 > 0 and z+direction*5 < 400: base.camera.setZ(z+direction*10)
    
def getTarget():
    pickerVector = render.getRelativeVector(camera, pickerRay.getDirection())
    pickerPoint = render.getRelativePoint(camera, pickerRay.getOrigin())
    coordinates = base.camera.getPos()-VBase3(pickerVector*base.camera.getZ()/pickerVector.getZ())
    return coordinates

####################
#| Visualizations |#
####################

def setCubic():
    for citizen in citizenIndex:
        color = citizen.getColor()
        position = VBase3((color[0]-0.5)*50, (color[1]-0.5)*50, (color[2]-0.5)*50)
        citizen.glide(position)
    global mode
    mode = 4
    #base.camera.setPos(VBase3(0, -50, 0))
    LerpPosInterval(base.camera, 1, VBase3(0, -100, 0), fluid = 1).start()
    LerpHprInterval(base.camera, 1, VBase3(0, 0, 0), fluid = 1).start()
    #base.camera.lookAt((0, 0, 0))
    props = WindowProperties()
    props.setCursorHidden(True)
    base.win.requestProperties(props)
    
def setPlanar():
    for citizen in citizenIndex:
        location = citizen.getLocation()
        citizen.glide(location)
    global mode
    mode = 1
    LerpPosInterval(base.camera, 1, VBase3(0, 0, 75), fluid = 1).start()
    LerpHprInterval(base.camera, 1, VBase3(0, -90, 0), fluid = 1).start()
    #base.camera.setPosHpr(0, 0, 75, 0, -90, 0)
    props = WindowProperties()
    props.setCursorHidden(False)
    base.win.requestProperties(props)

###########
#| Modes |#
###########

def idle():
    if keyState[0]: base.camera.setY(base.camera.getY()+1)
    if keyState[1]: base.camera.setY(base.camera.getY()-1)
    if keyState[2]: base.camera.setX(base.camera.getX()-1)
    if keyState[3]: base.camera.setX(base.camera.getX()+1)
    
    global targeting
    traverser.traverse(render)
    if handler.getNumEntries() > 0:
        handler.sortEntries()
        targeting = citizenIndex[int(handler.getEntry(0).getIntoNode().getParent(0).getTag("index"))]
    else: targeting = False

def cube():
    if keyState[0]:
        cameraNode.setPos(VBase3(0, 1, 0))
        base.camera.setPos(cameraNode.getPos(render))
    if keyState[1]:
        cameraNode.setPos(VBase3(0, -1, 0))
        base.camera.setPos(cameraNode.getPos(render))
    if keyState[2]:
        cameraNode.setPos(VBase3(-1, 0, 0))
        base.camera.setPos(cameraNode.getPos(render))
    if keyState[3]:
        cameraNode.setPos(VBase3(1, 0, 0))
        base.camera.setPos(cameraNode.getPos(render))
    
    md = base.win.getPointer(0) 
    x = md.getX() 
    y = md.getY() 
    if base.win.movePointer(0, base.win.getXSize()/2, base.win.getYSize()/2): 
        base.camera.setH(base.camera.getH() -  (x - base.win.getXSize()/2)*0.1) 
        base.camera.setP(base.camera.getP() - (y - base.win.getYSize()/2)*0.1) 

def point():
    if not pointToolbar.editing:
        if targeting:
            pointToolbar.setPaintColor(targeting.getColor())
            pointToolbar.candidacyButtons[targeting.getCandidate()].setProp('relief', 'sunken')
            pointToolbar.candidacyButtons[not targeting.getCandidate()].setProp('relief', 'raised')
            pointToolbar.name.set(str(targeting.getName()))
        else:
            pointToolbar.setPaintColor(GRAY50)
            pointToolbar.candidacyButtons[0].setProp('relief', 'raised')
            pointToolbar.candidacyButtons[1].setProp('relief', 'raised')
            pointToolbar.name.set('')
        
        if clickState[0] and targeting:
            targeting.setPosition(getTarget())
        elif clickState[2] and targeting:
            pointToolbar.edit(targeting)
            clickState[2] = 0
        else: idle()

def sculpt():
    if clickState[0]: direction = -1
    elif clickState[2]: direction = 1
    else: idle(); return
    target = getTarget()
    for citizen in citizenIndex:
        relative = citizen.getPosition()-target
        distance = (relative[0]**2+relative[1]**2)**0.5
        ratio = 1+direction/(distance+sculptToolbar.size)**sculptToolbar.falloff
        citizen.setPosition(target+relative*ratio)
        
def paint():
    if clickState[0]:
        target = getTarget()
        average = Vec4(0, 0, 0, 0)
        for citizen in citizenIndex:
            relative = citizen.getPosition()-target
            distance = (relative[0]**2+relative[1]**2)**0.5
            ratio = 1-1/(distance+paintToolbar.size)**paintToolbar.falloff
            color = (citizen.getColor()-paintToolbar.paintColor)*ratio+paintToolbar.paintColor
            citizen.setColor(color)
            average += color
        base.setBackgroundColor(average/len(citizenIndex))
    elif clickState[2] and targeting: paintToolbar.setPaintColor(targeting.getColor())
    else: idle()
    
modes = [idle, paint, sculpt, point, cube]

def mainTask(task):
    if base.mouseWatcherNode.hasMouse():
        mousePosition = base.mouseWatcherNode.getMouse()
        pickerRay.setFromLens(base.camNode, mousePosition.getX(), mousePosition.getY())

    modes[mode]()
    return task.cont

##############
#| Citizens |#
##############

class Citizen():
    def __init__(self, position, color):
        self.citizen = loader.loadModel("Models/ball")
        self.citizen.setPos(position)
        self.citizen.setScale(1)
        self.citizen.setColor(color)
        self.citizen.reparentTo(render)
        
        self.citizenIndex = len(citizenIndex)
        self.isCandidate = 0
        self.position = position
        self.location = position
        self.scale = 2
        self.color = color
        self.filteredColor = paintToolbar.applyFilter(color)
        self.name = "Voter #"+str(self.citizenIndex+1)
        
        self.citizen.getChild(0).setTag('index', str(self.citizenIndex))
        
    def remove(self): self.citizen.removeNode()
    def updateFilter(self):
        color = Vec4(0.5, 0.5, 0.5, 1)
        for i in range(3):
            if not filter[i]:
                color[i] = self.color[i]
        self.citizen.setColor(color)
                
    def getPosition(self): return self.position
    def getLocation(self): return self.location
    def getScale(self): return self.scale
    def getColor(self): return self.color
    def getName(self): return self.name
    def getCandidate(self): return self.isCandidate
    def getNodePath(self): return self.citizen
    
    def setPosition(self, position): self.position = position; self.citizen.setPos(position)
    def setLocation(self, location): self.location = location
    def setScale(self, scale): self.scale *= scale; self.citizen.setScale(self.scale)
    def setName(self, name): self.name = name
    def setColor(self, color):
        for i in range(3):
            if not filter[i]:
                self.color[i] = color[i]
        self.updateFilter()
    def setCandidate(self, value):
        if value == self.isCandidate: return
        global candidateIndex
        self.citizen.remove()
        if value == 1: self.citizen = loader.loadModel('Models/queen'); candidateIndex.append(self.citizenIndex); self.citizen.setScale(3)
        elif value == 0: self.citizen = loader.loadModel('Models/ball'); candidateIndex.remove(self.citizenIndex); self.citizen.setScale(1)
        self.citizen.setPos(self.position)
        self.citizen.setColor(self.color)
        self.citizen.reparentTo(render)
        self.citizen.getChild(0).setTag('index', str(self.citizenIndex))
        self.isCandidate = value
    def glide(self, position):
        self.position = position
        LerpPosInterval(self.citizen, 1, position, fluid = 1).start()
    def move(self, position):
        self.position = position
        LerpPosInterval(self.citizen, 1, position, fluid = 0).start()

citizenIndex = []
candidateIndex = []

        
##############
#| Toolbars |#
##############

class VisualizationToolbar():
    def __init__(self):
        self.frame = DirectFrame(sortOrder = 2, pos = (0, 0, 0.88), frameSize = (-0.22, 0.22, -0.12, 0.12), frameColor = GRAY10, borderWidth = (0.02, 0.02), relief = 'ridge')

        self.political = DirectButton(parent = self.frame, sortOrder = 2, pos = (-0.1, 0, 0), frameSize = (-0.1, 0.1, -0.1, 0.1), frameColor = GRAY30, borderWidth = (0.02, 0.02), relief = 'raised', text = 'Political', text_scale = 0.04, command = setPolitical)
        self.geographic = DirectButton(parent = self.frame, sortOrder = 2, pos = (0.1, 0, 0), frameSize = (-0.1, 0.1, -0.1, 0.1), frameColor = GRAY30, borderWidth = (0.02, 0.02), relief = 'raised', text = 'Geographic', text_scale = 0.04, command = setGeographic)
        
class PaintToolbar():
    def __init__(self):
        self.frame = DirectFrame(sortOrder = 2, pos = (0, 0, -1.12), frameSize = (-0.52, 0.52, -0.12, 0.12), frameColor = GRAY10, borderWidth = (0.02, 0.02), relief = 'ridge')
        self.sizeFrame = DirectFrame(parent = self.frame, sortOrder = 3, pos = (-0.425, 0, 0), frameSize = (-0.075, 0.075, -0.1, 0.1), frameColor = GRAY20, borderWidth = (0.02, 0.02), relief = 'ridge')
        self.falloffFrame = DirectFrame(parent = self.frame, sortOrder = 3, pos = (-0.275, 0, 0), frameSize = (-0.075, 0.075, -0.1, 0.1), frameColor = GRAY20, borderWidth = (0.02, 0.02), relief = 'ridge')
        
        self.sizeLarge = DirectButton(parent = self.sizeFrame, sortOrder = 3, pos = (0, 0, 0.04), frameSize = (-0.05, 0.05, -0.04, 0.04), frameColor = GRAY30, borderWidth = (0.01, 0.01), relief = 'sunken', text = 'Large', text_pos = (0, 0.005), text_scale = 0.03, command = self.setSize, extraArgs = [1])
        self.sizeSmall = DirectButton(parent = self.sizeFrame, sortOrder = 3, pos = (0, 0, -0.04), frameSize = (-0.05, 0.05, -0.04, 0.04), frameColor = GRAY30, borderWidth = (0.01, 0.01), relief = 'raised', text = 'Small', text_pos = (0, 0.005), text_scale = 0.03, command = self.setSize, extraArgs = [0])
        self.sizeButtons = [self.sizeSmall, self.sizeLarge]
        
        self.falloffSoft = DirectButton(parent = self.falloffFrame, sortOrder = 3, pos = (0, 0, 0.04), frameSize = (-0.05, 0.05, -0.04, 0.04), frameColor = GRAY30, borderWidth = (0.01, 0.01), relief = 'sunken', text = 'Soft', text_pos = (0, 0.005), text_scale = 0.03, command = self.setFalloff, extraArgs = [0])
        self.falloffHard = DirectButton(parent = self.falloffFrame, sortOrder = 3, pos = (0, 0, -0.04), frameSize = (-0.05, 0.05, -0.04, 0.04), frameColor = GRAY30, borderWidth = (0.01, 0.01), relief = 'raised', text = 'Hard', text_pos = (0, 0.005), text_scale = 0.03, command = self.setFalloff, extraArgs = [1])
        self.falloffButtons = [self.falloffSoft, self.falloffHard]
        
        self.sliderRed = DirectSlider(parent = self.frame, sortOrder = 3, range = (0, 1), value = 0.5, pageSize = 1, pos = (0, 0, 0.2/3), frameSize = (-0.2, 0.2, -0.1/3, 0.1/3), frameVisibleScale = (1, 1), frameColor = GRAY30, borderWidth = (0.02, 0.02), relief = 'ridge', command = self.updatePaint)
        self.sliderGreen = DirectSlider(parent = self.frame, sortOrder = 3, range = (0, 1), value = 0.5, pageSize = 1, pos = (0, 0, 0), frameSize = (-0.2, 0.2, -0.1/3, 0.1/3), frameVisibleScale = (1, 1), frameColor = GRAY30, borderWidth = (0.02, 0.02), relief = 'ridge', command = self.updatePaint)
        self.sliderBlue = DirectSlider(parent = self.frame, sortOrder = 3, range = (0, 1), value = 0.5, pageSize = 1, pos = (0, 0, -0.2/3), frameSize = (-0.2, 0.2, -0.1/3, 0.1/3), frameVisibleScale = (1, 1), frameColor = GRAY30, borderWidth = (0.02, 0.02), relief = 'ridge', command = self.updatePaint)
        self.sliders = [self.sliderRed, self.sliderGreen, self.sliderBlue]
        
        self.buttonRed = DirectButton(parent = self.frame, sortOrder = 3, pos = (0.25, 0, 0.2/3), frameSize = (-0.05, 0.05, -0.1/3, 0.1/3), frameColor = GRAY50, borderWidth = (0.01, 0.01), relief = 'sunken', command = self.setFilter, extraArgs = [0])
        self.buttonGreen = DirectButton(parent = self.frame, sortOrder = 3, pos = (0.25, 0, 0), frameSize = (-0.05, 0.05, -0.1/3, 0.1/3), frameColor = GRAY50, borderWidth = (0.01, 0.01), relief = 'sunken', command = self.setFilter, extraArgs = [1])
        self.buttonBlue = DirectButton(parent = self.frame, sortOrder = 3, pos = (0.25, 0, -0.2/3), frameSize = (-0.05, 0.05, -0.1/3, 0.1/3), frameColor = GRAY50, borderWidth = (0.01, 0.01), relief = 'sunken', command = self.setFilter, extraArgs = [2])
        self.buttons = [self.buttonRed, self.buttonGreen, self.buttonBlue]
        
        self.exit = DirectButton(parent = self.frame, sortOrder = 3, pos = (0.4, 0, 0), frameSize = (-0.1, 0.1, -0.1, 0.1), frameColor = GRAY30, borderWidth = (0.02, 0.02), text = "Exit", text_scale = 0.05, command = self.deactivate)
        
        self.size = 1
        self.falloff = 1
        self.paintColor = Vec4(0.5, 0.5, 0.5, 1)
        
    def setPaintColor(self, color):
        for index in range(3):
            self.sliders[index].setProp('value', color[index])
        
    def updatePaint(self):
        color = Vec4(0.5, 0.5, 0.5, 1)
        for index in range(3):
            color[index] = self.sliders[index]['value']
        for index in range(3):
            if filter[index]: self.buttons[index].setProp('frameColor', GRAY50)
            else: self.buttons[index].setProp('frameColor', color)
        self.paintColor = color
        self.updateSliders()
        
    def setFilter(self, colorIndex):
        if filter[colorIndex]:
            filter[colorIndex] = False
            self.buttons[colorIndex].setProp('relief', 'sunken')
        else:
            filter[colorIndex] = True
            self.buttons[colorIndex].setProp('relief', 'raised')
        
        self.setPaintColor(self.applyFilter(self.paintColor))
        for citizen in citizenIndex: citizen.updateFilter()
        
    def applyFilter(self, color):
        if filter[0]: color[0] = 0.5
        if filter[1]: color[1] = 0.5
        if filter[2]: color[2] = 0.5
        return color
        
    def updateSliders(self):
        color = self.applyFilter(self.paintColor)
        for index in range(3):
            newColor = Vec4(0.5, 0.5, 0.5, 1)
            newColor[index] = color[index]
            self.sliders[index].setProp('frameColor', newColor)
            
    def setSize(self, value):
        self.size = (value+1)*2
        self.sizeButtons[value].setProp('relief', 'sunken')
        self.sizeButtons[not value].setProp('relief', 'raised')
        
    def setFalloff(self, value):
        self.falloff = value+1
        self.falloffButtons[value].setProp('relief', 'sunken')
        self.falloffButtons[not value].setProp('relief', 'raised')
        
    def activate(self):
        global mode
        mode = 1
        mainToolbar.deactivate()
        for citizen in citizenIndex: citizen.setScale(2)
        LerpPosInterval(self.frame, 0.2, (0, 0, -0.88), blendType = 'easeInOut').start()
        
    def deactivate(self):
        mainToolbar.activate()
        for citizen in citizenIndex: citizen.setScale(0.5)
        LerpPosInterval(self.frame, 0.2, (0, 0, -1.12), blendType = 'easeInOut').start()
        
class SculptToolbar():
    def __init__(self):
        self.frame = DirectFrame(sortOrder = 2, pos = (0, 0, -1.12), scale = 1, frameSize = (-0.27, 0.27, -0.12, 0.12), frameColor = GRAY10, borderWidth = (0.02, 0.02), relief = 'ridge')
        self.sizeFrame = DirectFrame(parent = self.frame, sortOrder = 3, pos = (-0.175, 0, 0), frameSize = (-0.075, 0.075, -0.1, 0.1), frameColor = GRAY20, borderWidth = (0.02, 0.02), relief = 'ridge')
        self.falloffFrame = DirectFrame(parent = self.frame, sortOrder = 3, pos = (-0.025, 0, 0), frameSize = (-0.075, 0.075, -0.1, 0.1), frameColor = GRAY20, borderWidth = (0.02, 0.02), relief = 'ridge')
        
        self.sizeLarge = DirectButton(parent = self.sizeFrame, sortOrder = 3, pos = (0, 0, 0.04), frameSize = (-0.05, 0.05, -0.04, 0.04), frameColor = GRAY30, borderWidth = (0.01, 0.01), command = self.setSize, extraArgs = [1], relief = 'sunken', text = 'Large', text_scale = 0.03)
        self.sizeSmall = DirectButton(parent = self.sizeFrame, sortOrder = 3, pos = (0, 0, -0.04), frameSize = (-0.05, 0.05, -0.04, 0.04), frameColor = GRAY30, borderWidth = (0.01, 0.01), command = self.setSize, extraArgs = [0], relief = 'raised', text = 'Small', text_scale = 0.03)
        self.sizeButtons = [self.sizeSmall, self.sizeLarge]
        
        self.falloffSoft = DirectButton(parent = self.falloffFrame, sortOrder = 3, pos = (0, 0, 0.04), frameSize = (-0.05, 0.05, -0.04, 0.04), frameColor = GRAY30, borderWidth = (0.01, 0.01), command = self.setFalloff, extraArgs = [0], relief = 'sunken', text = 'Soft', text_scale = 0.03)
        self.falloffHard = DirectButton(parent = self.falloffFrame, sortOrder = 3, pos = (0, 0, -0.04), frameSize = (-0.05, 0.05, -0.04, 0.04), frameColor = GRAY30, borderWidth = (0.01, 0.01), command = self.setFalloff, extraArgs = [1], relief = 'raised', text = 'Hard', text_scale = 0.03)
        self.falloffButtons = [self.falloffSoft, self.falloffHard]
        
        self.exit = DirectButton(parent = self.frame, sortOrder = 3, pos = (0.15, 0, 0), frameSize = (-0.1, 0.1, -0.1, 0.1), frameColor = GRAY30, borderWidth = (0.02, 0.02), text = "Exit", text_scale = 0.05, command = self.deactivate)
        
        self.size = 1
        self.falloff = 1
        
    def setSize(self, value):
        self.size = (value+1)*2
        self.sizeButtons[value].setProp('relief', 'sunken')
        self.sizeButtons[not value].setProp('relief', 'raised')
        
    def setFalloff(self, value):
        self.falloff = value+1
        self.falloffButtons[value].setProp('relief', 'sunken')
        self.falloffButtons[not value].setProp('relief', 'raised')
        
    def activate(self):
        global mode
        mode = 2
        mainToolbar.deactivate()
        LerpPosInterval(self.frame, 0.2, (0, 0, -0.88), blendType = 'easeInOut').start()
        
    def deactivate(self):
        mainToolbar.activate()
        for citizen in citizenIndex: citizen.setScale(1)
        LerpPosInterval(self.frame, 0.2, (0, 0, -1.12), blendType = 'easeInOut').start()
        
class GridToolbar():
    def __init__(self):
        self.frame = DirectFrame(sortOrder = 2, pos = (0, 0, -1.12), scale = 1, frameSize = (-0.27, 0.27, -0.12, 0.12), frameColor = GRAY10, borderWidth = (0, 0.02), relief = 'ridge')
        
        self.populationSlider = DirectSlider(parent = self.frame, sortOrder = 3, range = (2, 30), value = 15, pageSize = 50, pos = (-0.2, 0, 0), frameSize = (-0.05, 0.05, -0.1, 0.1), frameVisibleScale = (1, 1), frameColor = GRAY30, orientation = 'vertical', borderWidth = (0.02, 0.02), relief = 'ridge', command = self.updateReadout)
        self.populationReadout = DirectLabel(parent = self.frame, sortOrder = 3, pos = (-0.05, 0, 0.05), frameSize = (-0.1, 0.1, -0.05, 0.05), frameColor = GRAY40, borderWidth = (0.015, 0.015), relief = 'ridge', text_pos = (0, 0, -0.04))
        self.populationButton = DirectButton(parent = self.frame, sortOrder = 3, pos = (-0.05, 0, -0.05), frameSize = (-0.1, 0.1, -0.05, 0.05), frameColor = GRAY40, borderWidth = (0.015, 0.015), text = 'Populate', text_scale = 0.04, command = self.generateGrid)

        self.exit = DirectButton(parent = self.frame, sortOrder = 3, pos = (0.15, 0, 0), frameSize = (-0.1, 0.1, -0.1, 0.1), frameColor = GRAY30, borderWidth = (0.02, 0.02), text = "Exit", text_scale = 0.05, command = self.deactivate)
        
    def generateGrid(self):
        size = self.populationSlider['value']
        for i in range(len(citizenIndex)):
            citizenIndex[0].remove()
            del citizenIndex[0]
        for y in range(size):
            for x in range(size): citizenIndex.append(Citizen(VBase3(x-size/2, y-size/2, 0), Vec4(.5, .5, .5, 1)))
        base.setBackgroundColor(Vec4(0.5, 0.5, 0.5, 1))
        
    def updateReadout(self):
        self.populationReadout.setProp('text', str(int(self.populationSlider['value'])**2))
        self.populationReadout.setProp('text_scale', 0.05)
        
    def activate(self):
        global mode
        mode = 0
        mainToolbar.deactivate()
        LerpPosInterval(self.frame, 0.2, (0, 0, -0.88), blendType = 'easeInOut').start()
        
    def deactivate(self):
        mainToolbar.activate()
        LerpPosInterval(self.frame, 0.2, (0, 0, -1.12), blendType = 'easeInOut').start()
        
class TallyToolbar():
    def __init__(self):
        self.frame = DirectFrame(sortOrder = 2, pos = (0, 0, -1.12), scale = 1, frameSize = (-0.52, 0.52, -0.12, 0.12), frameColor = GRAY10, borderWidth = (0.02, 0.02), relief = 'ridge')
        
        self.exit = DirectButton(parent = self.frame, sortOrder = 3, pos = (0.4, 0, 0), frameSize = (-0.1, 0.1, -0.1, 0.1), frameColor = GRAY30, borderWidth = (0.02, 0.02), text = "Exit", text_scale = 0.05, command = self.deactivate)
        
    def activate(self):
        global mode
        mode = 0
        mainToolbar.deactivate()
        LerpPosInterval(self.frame, 0.2, (0, 0, -0.88), blendType = 'easeInOut').start()
        
    def deactivate(self):
        mainToolbar.activate()
        LerpPosInterval(self.frame, 0.2, (0, 0, -1.12), blendType = 'easeInOut').start()
        
class PointToolbar():
    def __init__(self):
        self.frame = DirectFrame(sortOrder = 2, pos = (0, 0, -1.12), frameSize = (-0.52, 0.52, -0.12, 0.12), frameColor = GRAY10, borderWidth = (0.02, 0.02), relief = 'ridge')
        
        self.name = DirectEntry(parent = self.frame, sortOrder = 3, pos = (-0.3, 0, 0.05), frameSize = (-0.2, 0.2, -0.05, 0.05), frameColor = GRAY30, width = 7, borderWidth = (0.015, 0.015), relief = 'ridge', text_pos = (-0.18, -0.02), text_scale = 0.05)

        self.citizen = DirectButton(parent = self.frame, sortOrder = 3, pos = (-0.4, 0, -0.05), frameSize = (-0.1, 0.1, -0.05, 0.05), frameColor = GRAY20, borderWidth = (0.015, 0.015), pressEffect = 'disabled', relief = 'raised', text_scale = 0.035, text = 'Citizen', command = self.setCandidacy, extraArgs = [0])
        self.candidate = DirectButton(parent = self.frame, sortOrder = 3, pos = (-0.2, 0, -0.05), frameSize = (-0.1, 0.1, -0.05, 0.05), frameColor = GRAY20, borderWidth = (0.015, 0.015), pressEffect = 'disabled', relief = 'raised', text_scale = 0.035, text = 'Candidate', command = self.setCandidacy, extraArgs = [1])
        self.candidacyButtons = [self.citizen, self.candidate]

        self.sliderRed = DirectSlider(parent = self.frame, sortOrder = 3, range = (0, 1), value = 0.5, pos = (0.1, 0, 0.2/3), frameSize = (-0.2, 0.2, -0.1/3, 0.1/3), frameVisibleScale = (1, 1), frameColor = GRAY30, borderWidth = (0.02, 0.02), relief = 'ridge', command = self.updatePaint)
        self.sliderGreen = DirectSlider(parent = self.frame, sortOrder = 3, range = (0, 1), value = 0.5, pos = (0.1, 0, 0), frameSize = (-0.2, 0.2, -0.1/3, 0.1/3), frameVisibleScale = (1, 1), frameColor = GRAY30, borderWidth = (0.02, 0.02), relief = 'ridge', command = self.updatePaint)
        self.sliderBlue = DirectSlider(parent = self.frame, sortOrder = 3, range = (0, 1), value = 0.5, pos = (0.1, 0, -0.2/3), frameSize = (-0.2, 0.2, -0.1/3, 0.1/3), frameVisibleScale = (1, 1), frameColor = GRAY30, borderWidth = (0.02, 0.02), relief = 'ridge', command = self.updatePaint)
        self.sliders = [self.sliderRed, self.sliderGreen, self.sliderBlue]
        
        self.exit = DirectButton(parent = self.frame, sortOrder = 3, pos = (0.4, 0, 0), frameSize = (-0.1, 0.1, -0.1, 0.1), frameColor = GRAY30, borderWidth = (0.02, 0.02), text = "Exit", text_scale = 0.05, command = self.deactivate)
        
        self.editing = 0
        self.paintColor = Vec4(0.5, 0.5, 0.5, 1)
        
    def getPaintColor(self):
        return self.paintColor
    
    def edit(self, editing):
        self.editing = editing
        self.exit.setProp('text', 'Save')
        self.exit.setProp('command', self.save)
    
    def save(self):
        if self.citizen['relief'] == 'raised': candidacy = 1
        else: candidacy = 0
        self.editing.setCandidate(candidacy)
        self.editing.setName(str(self.name.get()))
        self.editing.setColor(self.paintColor)
        self.editing = 0
        self.exit.setProp('text', 'Exit')
        self.exit.setProp('command', self.deactivate)
        
    def setPaintColor(self, color):
        for index in range(3):
            self.sliders[index].setProp('value', color[index])
        
    def updatePaint(self):
        color = Vec4(0.5, 0.5, 0.5, 1)
        for index in range(3): color[index] = self.sliders[index]['value']
        self.paintColor = color
        self.updateSliders()
        
    def applyFilter(self, color):
        if filter[0]: color[0] = 0.5
        if filter[1]: color[1] = 0.5
        if filter[2]: color[2] = 0.5
        return color

    def updateSliders(self):
        color = self.applyFilter(self.paintColor)
        for index in range(3):
            newColor = Vec4(0.5, 0.5, 0.5, 1)
            newColor[index] = color[index]
            self.sliders[index].setProp('frameColor', newColor)
            
    def setCandidacy(self, value):
        self.candidate = value
        self.candidacyButtons[value].setProp('relief', 'sunken')
        self.candidacyButtons[not value].setProp('relief', 'raised')
        
    def activate(self):
        global mode
        mode = 3
        mainToolbar.deactivate()
        LerpPosInterval(self.frame, 0.2, (0, 0, -0.88), blendType = 'easeInOut').start()
        
    def deactivate(self):
        mainToolbar.activate()
        LerpPosInterval(self.frame, 0.2, (0, 0, -1.12), blendType = 'easeInOut').start()
        
class MainToolbar():
    def __init__(self):
        self.frame = DirectFrame(pos = (0, 0, -0.88), sortOrder = 0, frameSize = (-0.52, 0.52, -0.12, 0.12), frameColor = GRAY10, borderWidth = (0.02, 0.02), relief = 'ridge')
        
        self.sculptButton = DirectButton(parent = self.frame, sortOrder = 1, pos = (-0.4, 0, 0), scale = 1, command = sculptToolbar.activate, frameSize = (-0.1, 0.1, -0.1, 0.1), frameColor = GRAY30, borderWidth = (0.02, 0.02), relief = 'raised', text = 'Sculpt', text_scale = 0.04)
        self.paintButton = DirectButton(parent = self.frame, sortOrder = 1, pos = (-0.2, 0, 0), scale = 1, command = paintToolbar.activate, frameSize = (-0.1, 0.1, -0.1, 0.1), frameColor = GRAY30, borderWidth = (0.02, 0.02), relief = 'raised', text = 'Paint', text_scale = 0.04)
        self.tallyButton = DirectButton(parent = self.frame, sortOrder = 1, pos = (0, 0, 0), scale = 1, command = tallyToolbar.activate, frameSize = (-0.1, 0.1, -0.1, 0.1), frameColor = GRAY30, borderWidth = (0.02, 0.02), relief = 'raised', text = 'Tally', text_scale = 0.04)
        self.pointButton = DirectButton(parent = self.frame, sortOrder = 1, pos = (0.2, 0, 0), scale = 1, command = pointToolbar.activate, frameSize = (-0.1, 0.1, -0.1, 0.1), frameColor = GRAY30, borderWidth = (0.02, 0.02), relief = 'raised', text = 'Point', text_scale = 0.04)
        self.gridButton = DirectButton(parent = self.frame, sortOrder = 1, pos = (0.4, 0, 0), scale = 1, command = gridToolbar.activate, frameSize = (-0.1, 0.1, -0.1, 0.1), frameColor = GRAY30, borderWidth = (0.02, 0.02), relief = 'raised', text = 'Grid', text_scale = 0.04)
        
    def activate(self):
        global mode
        mode = 0
        LerpPosInterval(self.frame, 0.2, (0, 0, -0.88), blendType = 'easeInOut').start()
        
    def deactivate(self):
        LerpPosInterval(self.frame, 0.2, (0, 0, -1.12), blendType = 'easeInOut').start()
        
pointToolbar = PointToolbar()
tallyToolbar = TallyToolbar()
gridToolbar = GridToolbar()
sculptToolbar = SculptToolbar()
paintToolbar = PaintToolbar()
mainToolbar = MainToolbar()
toolbars = [mainToolbar, paintToolbar, sculptToolbar, gridToolbar, tallyToolbar, pointToolbar]


base.disableMouse()
base.camera.setPosHpr(0, 0, 75, 0, -90, 0)
cameraNode = base.camera.attachNewNode('CameraNode')

# Lighting Setup
ambientLight = AmbientLight('ambient')
ambientLight.setColor(VBase4(0.8, 0.8, 0.8, 1))
ambientLightNode = render.attachNewNode(ambientLight)
render.setLight(ambientLightNode)

# Collision Setup
traverser = CollisionTraverser()
handler = CollisionHandlerQueue()

pickerRay = CollisionRay()
pickerCollisionNode = CollisionNode('mouseRay')
pickerCollisionNode.setFromCollideMask(BitMask32.bit(1))
pickerCollisionNode.addSolid(pickerRay)
pickerCollisionNode.setIntoCollideMask(0)
pickerCollisionNode.setFromCollideMask(GeomNode.getDefaultCollideMask())
pickerNode = base.camera.attachNewNode(pickerCollisionNode)
traverser.addCollider(pickerNode, handler)

# Key Bindings
base.accept('escape', sys.exit)

base.accept('c', setCubic)
base.accept('v', setPlanar)

base.accept('mouse1', setClickState, [0, 1])
base.accept('mouse1-up', setClickState, [0, 0])

base.accept('mouse2', setClickState, [1, 1])
base.accept('mouse2-up', setClickState, [1, 0])

base.accept('mouse3', setClickState, [2, 1])
base.accept('mouse3-up', setClickState, [2, 0])

base.accept("wheel_down", scroll, [1])
base.accept("wheel_up", scroll, [-1])

base.accept("w", setKeyState, [0, 1])
base.accept("w-up", setKeyState, [0, 0])        

base.accept("s", setKeyState, [1, 1])
base.accept("s-up", setKeyState, [1, 0])

base.accept("a", setKeyState, [2, 1])
base.accept("a-up", setKeyState, [2, 0])

base.accept("d", setKeyState, [3, 1])
base.accept("d-up", setKeyState, [3, 0])

# Tracker Variables
targeting = False
mode = 0
clickState = [0, 0, 0]
keyState = [0, 0, 0, 0]

# Startup
mainTask = taskMgr.add(mainTask, 'mainTask')
run()