import DistributedElevator
import DistributedBossElevator
from ElevatorConstants import *
from direct.directnotify import DirectNotifyGlobal
from toontown.toonbase import TTLocalizer

class DistributedSBMElevator(DistributedBossElevator.DistributedBossElevator):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedSBMElevator')

    def __init__(self, cr):
        DistributedBossElevator.DistributedBossElevator.__init__(self, cr)
        self.type = ELEVATOR_VP
        self.countdownTime = ElevatorData[self.type]['countdown']

    def setupElevator(self):
        self.elevatorModel = loader.loadModel('phase_9/models/cogHQ/cogHQ_elevator')
        icon = self.elevatorModel.find('**/big_frame/')
        icon.hide()
        self.leftDoor = self.elevatorModel.find('**/left-door')
        self.rightDoor = self.elevatorModel.find('**/right-door')
        geom = base.cr.playGame.hood.loader.geom
        locator = geom.find('**/miniboss_locator')
        self.elevatorModel.reparentTo(geom)
        self.elevatorModel.setPos(26.518, 5.229, 0.025)
        self.elevatorModel.setHpr(270, 0, 0)        
        DistributedElevator.DistributedElevator.setupElevator(self)

    def getDestName(self):
        return TTLocalizer.ElevatorSellBotMiniBoss
