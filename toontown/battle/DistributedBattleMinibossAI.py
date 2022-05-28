from direct.directnotify import DirectNotifyGlobal
from toontown.battle import DistributedBattleFinalAI
from toontown.toonbase import ToontownBattleGlobals

class DistributedBattleMinibossAI(DistributedBattleFinalAI.DistributedBattleFinalAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedBattleMinibossAI')

    def __init__(self, air, bossCog, roundCallback, finishCallback, battleSide):
        DistributedBattleFinalAI.DistributedBattleFinalAI.__init__(self, air, bossCog, roundCallback, finishCallback, battleSide)

    def startBattle(self, toonIds, suits):
        self.joinableFsm.request('Joinable')
        for toonId in toonIds:
            if self.addToon(toonId):
                self.activeToons.append(toonId)

        self.d_setMembers()
        for suit in suits:
            joined = self.suitRequestJoin(suit)

        self.d_setMembers()
        self.b_setState('ReservesJoining')

    def resume(self, joinedReserves):
        if len(joinedReserves) != 0:
            for info in joinedReserves:
                joined = self.suitRequestJoin(info)

            self.d_setMembers()
            self.b_setState('ReservesJoining')
        elif len(self.suits) == 0:
            battleMultiplier = ToontownBattleGlobals.getBossBattleCreditMultiplier(self.battleNumber)
            for toonId in self.activeToons:
                toon = self.getToon(toonId)
                if toon:
                    recovered, notRecovered = self.air.questManager.recoverItems(toon, self.suitsKilledThisBattle, self.zoneId)
                    self.toonItems[toonId][0].extend(recovered)
                    self.toonItems[toonId][1].extend(notRecovered)

            self.d_setMembers()
            self.d_setBattleExperience()
            self.b_setState('Reward')
        else:
            if self.resumeNeedUpdate == 1:
                self.d_setMembers()
                if len(self.resumeDeadSuits) > 0 and self.resumeLastActiveSuitDied == 0 or len(self.resumeDeadToons) > 0:
                    self.needAdjust = 1
            self.setState('WaitForJoin')
        self.resumeNeedUpdate = 0
        self.resumeDeadToons = []
        self.resumeDeadSuits = []
        self.resumeLastActiveSuitDied = 0