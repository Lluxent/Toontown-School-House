from panda3d.core import *
from panda3d.toontown import *
from direct.distributed.ClockDelta import *
import math
import random
from direct.directnotify import DirectNotifyGlobal
from toontown.battle import SuitBattleGlobals
import SuitTimings
import SuitDNA
from toontown.toonbase import TTLocalizer
TIME_BUFFER_PER_WPT = 0.25
TIME_DIVISOR = 100
DISTRIBUTE_TASK_CREATION = 0

class SuitBase:
    notify = DirectNotifyGlobal.directNotify.newCategory('SuitBase')

    def __init__(self):
        self.dna = None
        self.level = 0
        self.maxHP = 10
        self.currHP = 10
        self.isSkelecog = 0
        return

    def delete(self):
        pass

    def getStyleName(self):
        if hasattr(self, 'dna') and self.dna:
            return self.dna.name
        else:
            self.notify.error('called getStyleName() before dna was set!')
            return 'unknown'

    def getStyleDept(self):
        if hasattr(self, 'dna') and self.dna:
            return SuitDNA.getDeptFullname(self.dna.dept)
        else:
            self.notify.error('called getStyleDept() before dna was set!')
            return 'unknown'

    def getLevel(self):
        return self.level

    def setLevel(self, level):
        self.level = level
        attributes = SuitBattleGlobals.SuitAttributes[self.dna.name]
        if attributes['level'] < 8: # IF NORMAL COG
            if level > attributes['level'] + len(attributes['hp']):
                self.level = len(attributes['hp']) - 1
            nameWLevel = TTLocalizer.SuitBaseNameWithLevel % {'name': self.name,
            'dept': self.getStyleDept(),
            'level': self.getActualLevel()}
            self.setDisplayName(nameWLevel)
            self.maxHP = attributes['hp'][self.level]
            self.currHP = self.maxHP
        else:
            if self.dna.name == 'ssb':
                self.level = level
                nameWLevel = TTLocalizer.SuitBaseNameWithLevelMgr % {'name': TTLocalizer.SuitShadow,
                'dept': self.getStyleDept(),
                'level': 10}
            else:
                self.level = attributes['level'] # don't subtract 1, assume the level is as-is from battleglobals
                nameWLevel = TTLocalizer.SuitBaseNameWithLevel % {'name': self.name,
                'dept': self.getStyleDept(),
                'level': self.getActualLevel()}

            self.setDisplayName(nameWLevel)
            if self.dna.name == 'ssb':
                self.maxHP = attributes['hp'][self.level]
                self.currHP = self.maxHP
            else:
                self.maxHP = attributes['hp'][0]
                self.currHP = self.maxHP

    def getSkelecog(self):
        return self.isSkelecog

    def setSkelecog(self, flag):
        self.isSkelecog = flag

    def getCurrentHealth(self):
        return self.currHP

    def getMaxHealth(self):
        return self.maxHP

    def getActualLevel(self):
        attributes = SuitBattleGlobals.SuitAttributes[self.dna.name]
        if attributes['level'] < 8:
            if hasattr(self, 'dna'):
                return SuitBattleGlobals.getActualFromRelativeLevel(self.getStyleName(), self.level) + 1
            else:
                self.notify.warning('called getActualLevel with no DNA, returning 1 for level')
                return 1
        else:
            return attributes['level']

    def setPath(self, path):
        self.path = path
        self.pathLength = self.path.getNumPoints()

    def getPath(self):
        return self.path

    def printPath(self):
        print '%d points in path' % self.pathLength
        for currPathPt in xrange(self.pathLength):
            indexVal = self.path.getPointIndex(currPathPt)
            print '\t', self.sp.dnaStore.getSuitPointWithIndex(indexVal)

    def makeLegList(self):
        self.legList = SuitLegList(self.path, self.sp.dnaStore, self.sp.suitWalkSpeed, SuitTimings.fromSky, SuitTimings.toSky, SuitTimings.fromSuitBuilding, SuitTimings.toSuitBuilding, SuitTimings.toToonBuilding)
