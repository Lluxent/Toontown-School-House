from math import floor
from BattleBase import *
from DistributedBattleAI import *
from toontown.toonbase import ToontownBattleGlobals
from toontown.toonbase.ToontownBattleGlobals import *
import random
from toontown.suit import DistributedSuitBaseAI
import SuitBattleGlobals, BattleExperienceAI
from toontown.toon import NPCToons
from toontown.pets import PetTricks, DistributedPetProxyAI
from direct.showbase.PythonUtil import lerp

class BattleCalculatorAI:
    notify = DirectNotifyGlobal.directNotify.newCategory('BattleCalculatorAI')
    notify.setDebug(True)

    AccuracyBonuses = [
     0, 20, 40, 60]
    DamageBonuses = [
     0, 20, 20, 20]
    DropDamageBonuses = [0, 30, 40, 50]
    AttackExpPerTrack = [
     0, 10, 20, 30, 40, 50, 60]
    NumRoundsLured = ToontownBattleGlobals.AvLureRounds
    NumRoundsSoaked = ToontownBattleGlobals.AvSoakRounds
    TRAP_CONFLICT = -2
    APPLY_HEALTH_ADJUSTMENTS = 1
    TOONS_TAKE_NO_DAMAGE = 0
    CAP_HEALS = 1
    CLEAR_SUIT_ATTACKERS = 1
    SUITS_UNLURED_IMMEDIATELY = 1
    CLEAR_MULTIPLE_TRAPS = 0
    KBBONUS_LURED_FLAG = 0
    KBBONUS_TGT_LURED = 1
    toonsAlwaysHit = simbase.config.GetBool('toons-always-hit', 0)
    toonsAlwaysMiss = simbase.config.GetBool('toons-always-miss', 0)
    toonsAlways5050 = simbase.config.GetBool('toons-always-5050', 0)
    suitsAlwaysHit = simbase.config.GetBool('suits-always-hit', 0)
    suitsAlwaysMiss = simbase.config.GetBool('suits-always-miss', 0)
    immortalSuits = simbase.config.GetBool('immortal-suits', 0)

    def __init__(self, battle, tutorialFlag=0):
        self.battle = battle
        self.SuitAttackers = {}
        self.currentlyLuredSuits = {}
        self.successfulLures = {}
        self.toonAtkOrder = []
        self.toonHPAdjusts = {}
        self.toonSkillPtsGained = {}
        self.traps = {}
        self.npcTraps = {}
        self.suitAtkStats = {}
        self.__clearBonuses(hp=1)
        self.__clearBonuses(hp=0)
        self.delayedUnlures = []
        self.__skillCreditMultiplier = 1
        self.tutorialFlag = tutorialFlag
        self.trainTrapTriggered = False
        self.TurnsElapsed = 0
        self.TurnsSinceSummonWithOnlyOneCog = 0
        self.TurnsSinceSummon = 0
        self.numShadowsSummoned = 0

        # a dictionary of each toon's status conditions
        # 
        # each status is formatted this way
        # 'condition': {modifier, turnsRemaining}
        #
        # the dictionary holds all four toons, so a possible dictionary could be
        # { 10000000: { 'corruption': {'modifier': 2, 'turnsRemaining': -1} } }
        self.toonStatusConditions = {}

        self.suitStatusConditions = {}

    def toonHasCondition(self, toonId, condition):
        self.notify.debug('toonHasCondition() - checking for \'%s\' on toonId %i' % (condition, toonId))
        if toonId not in self.toonStatusConditions:
            self.notify.debug('toonHasCondition() - toon %i is not in the condition dictionary at all' % toonId)
            return False
        
        if condition in self.toonStatusConditions[toonId]:
            self.notify.debug('toonHasCondition() - toon %i has the \'%s\' condition' % (toonId, condition))
            return True
        else:
            self.notify.debug('toonHasCondition() - toon %i is in the dictionary, but does not have the \'%s\' condition' % (toonId, condition))
            return False

    def getToonConditionModifier(self, toonId, condition):
        if not self.toonHasCondition(toonId, condition):
            self.notify.warning('getToonConditionModifier() - method called, but toon %i did not have %s condition' % (toonId, condition))
            return 0
        return self.toonStatusConditions[toonId][condition]['modifier']

    def getToonConditionTurns(self, toonId, condition):
        if not self.toonHasCondition(toonId, condition):
            self.notify.warning('getToonConditionTurns() - method called, but toon %i did not have %s condition' % (toonId, condition))
            return 0
        return self.toonStatusConditions[toonId][condition]['turnsRemaining']

    def setToonCondition(self, toonId, condition, modifier, turns, mode = 'none'):
        # first, check if the toon is even in the dictionary
        if toonId not in self.toonStatusConditions:
            # if not, make them an entry
            self.toonStatusConditions[toonId] = {}

        # next, check if the toon has the condition already
        if condition not in self.toonStatusConditions[toonId]:
            # if not, add the condition, and we're done
            self.toonStatusConditions[toonId][condition] = {'modifier': modifier, 'turnsRemaining': turns}
            return
        else:
            # otherwise, increase the existing modifier appropriately
            newModifier = 0 # the variable we will set the modifier to
            newTurns = 0    # the variable we will set the turns to

            # modifier APPENDED, turns SET, used to change a buff/debuff's timer, but keep its potency 
            if mode is 'refreshTurns':
                newModifier = self.getToonConditionModifier(toonId, condition) + modifier
                newTurns = turns

            # modifer SET, turns APPENDED, used to modify a buff/debuff's potency, but change its duration
            if mode is 'refreshModifier':
                newModifier = modifier
                newTurns = self.getToonConditionTurns(toonId, condition) + turns
            
            # modifier APPENDED, turns APPENDED, used to change a buff/debuff's potency AND duration
            if mode is 'refreshBoth':
                newModifier = self.getToonConditionModifier(toonId, condition) + modifier        
                newTurns = self.getToonConditionTurns(toonId, condition) + turns

            # modifier SET, turns SET, used to explicitly set a modifier to a precise potency and duration
            if mode is 'setBoth':
                newModifier = modifier
                newTurns = turns

            if mode is 'alternateBoth':
                if modifier > self.toonStatusConditions[toonId][condition]['modifier']:
                    newModifier = self.toonStatusConditions[toonId][condition]
                else:
                    newModifier = modifier
                newTurns = turns

            self.notify.debug('setToonCondition() - gave toon %i modifier %s with modifier %i with %i turns remaining' % (toonId, modifier, newModifier, newTurns))
            self.toonStatusConditions[toonId][condition] = {'modifier': newModifier, 'turnsRemaining': newTurns}

    def suitHasCondition(self, suitId, condition):
        self.notify.debug('suitHasCondition() - checking for \'%s\' on suitId %i' % (condition, suitId.doId))
        if suitId not in self.suitStatusConditions:
            self.notify.debug('suitHasCondition() - suit %i is not in the condition dictionary at all' % suitId.doId)
            return False
        
        if condition in self.suitStatusConditions[suitId]:
            self.notify.debug('suitHasCondition() - suit %i has the \'%s\' condition' % (suitId.doId, condition))
            return True
        else:
            self.notify.debug('suitHasCondition() - suit %i is in the dictionary, but does not have the \'%s\' condition' % (suitId.doId, condition))
            return False

    def getSuitConditionModifier(self, suitId, condition):
        if not self.suitHasCondition(suitId, condition):
            self.notify.warning('getSuitConditionModifier() - method called, but suit %i did not have %s condition' % (suitId.doId, condition))
            return 0
        return self.suitStatusConditions[suitId][condition]['modifier']

    def getSuitConditionTurns(self, suitId, condition):
        if not self.suitHasCondition(suitId, condition):
            self.notify.warning('getSuitConditionTurns() - method called, but suit %i did not have %s condition' % (suitId.doId, condition))
            return 0
        return self.suitStatusConditions[suitId][condition]['turnsRemaining']

    def setSuitCondition(self, suitId, condition, modifier, turns, mode = 'none'):
        # first, check if the suit is even in the dictionary
        if suitId not in self.suitStatusConditions:
            # if not, make them an entry
            self.suitStatusConditions[suitId] = {}

        # next, check if the suit has the condition already
        if condition not in self.suitStatusConditions[suitId]:
            # if not, add the condition, and we're done
            self.suitStatusConditions[suitId][condition] = {'modifier': modifier, 'turnsRemaining': turns}
            return
        else:
            # otherwise, increase the existing modifier appropriately
            newModifier = 0 # the variable we will set the modifier to
            newTurns = 0    # the variable we will set the turns to

            # modifier APPENDED, turns SET, used to change a buff/debuff's timer, but keep its potency 
            if mode is 'refreshTurns':
                newModifier = self.getSuitConditionModifier(suitId, condition) + modifier
                newTurns = turns

            # modifer SET, turns APPENDED, used to modify a buff/debuff's potency, but change its duration
            if mode is 'refreshModifier':
                newModifier = modifier
                newTurns = self.getSuitConditionTurns(suitId, condition) + turns
            
            # modifier APPENDED, turns APPENDED, used to change a buff/debuff's potency AND duration
            if mode is 'refreshBoth':
                newModifier = self.getSuitConditionModifier(suitId, condition) + modifier        
                newTurns = self.getSuitConditionTurns(suitId, condition) + turns

            # modifier SET, turns SET, used to explicitly set a modifier to a precise potency and duration
            if mode is 'setBoth':
                newModifier = modifier
                newTurns = turns

            if mode is 'alternateBoth':
                if modifier > self.suitStatusConditions[suitId][condition]['modifier']:
                    newModifier = self.suitStatusConditions[suitId][condition]
                else:
                    newModifier = modifier
                newTurns = turns

            self.notify.debug('setSuitCondition() - gave suit %i modifier %s with modifier %i with %i turns remaining' % (suitId.doId, modifier, newModifier, newTurns))
            self.suitStatusConditions[suitId][condition] = {'modifier': newModifier, 'turnsRemaining': newTurns}

    def decrementConditionTurns(self):
        for toon in self.toonStatusConditions.keys():
            for condition in self.toonStatusConditions[toon].keys():
                if self.toonStatusConditions[toon][condition]['turnsRemaining'] >= 0:
                    self.notify.debug('decrementConditionTurns() - Decremented %s condition on toon %i (new turns: %i)' % (condition, toon, self.toonStatusConditions[toon][condition]['turnsRemaining'] - 1))
                    self.toonStatusConditions[toon][condition]['turnsRemaining'] -= 1

                if self.toonStatusConditions[toon][condition]['turnsRemaining'] == -1:
                    self.notify.debug('decrementConditionTurns() - %s condition on toon %i have reached end, removing.' % (condition, toon))
                    del self.toonStatusConditions[toon][condition]

        for suit in self.suitStatusConditions.keys():
            for condition in self.suitStatusConditions[suit].keys():
                if self.suitStatusConditions[suit][condition]['turnsRemaining'] >= 0:
                    self.notify.debug('decrementConditionTurns() - Decremented %s condition on suit %i (new turns: %i)' % (condition, suit.doId, self.suitStatusConditions[suit][condition]['turnsRemaining'] - 1))
                    self.suitStatusConditions[suit][condition]['turnsRemaining'] -= 1

                if self.suitStatusConditions[suit][condition]['turnsRemaining'] == -1:
                    self.notify.debug('decrementConditionTurns() - %s condition on suit %i have reached end, removing.' % (condition, suit.doId))
                    del self.suitStatusConditions[suit][condition]
                
    def printToonConditions(self):
        self.notify.debug('printToonConditions() *********************************************')
        self.notify.debug('printToonConditions(): Beginning Turn Readout')
        self.notify.debug('printToonConditions() *********************************************')
        for toon in self.toonStatusConditions:
            self.notify.debug('printToonConditions(): Toon %i has the following Conditions:' % toon)
            for condition in self.toonStatusConditions[toon]:
                self.notify.debug('printToonConditions(): %s x %i, with %i turns remaining' % (condition, self.toonStatusConditions[toon][condition]['modifier'], self.toonStatusConditions[toon][condition]['turnsRemaining']))
        self.notify.debug('printToonConditions() *********************************************')
        self.notify.debug('printToonConditions(): Ending Turn Readout')
        self.notify.debug('printToonConditions() *********************************************')

    def printSuitConditions(self):
        self.notify.debug('printSuitConditions() *********************************************')
        self.notify.debug('printSuitConditions(): Beginning Turn Readout')
        self.notify.debug('printSuitConditions() *********************************************')
        for suit in self.suitStatusConditions:
            self.notify.debug('printSuitConditions(): Suit %i has the following Conditions:' % suit.doId)
            for condition in self.suitStatusConditions[suit]:
                self.notify.debug('printSuitConditions(): %s x %i, with %i turns remaining' % (condition, self.suitStatusConditions[suit][condition]['modifier'], self.suitStatusConditions[suit][condition]['turnsRemaining']))
        self.notify.debug('printSuitConditions() *********************************************')
        self.notify.debug('printSuitConditions(): Ending Turn Readout')
        self.notify.debug('printSuitConditions() *********************************************')


    def setSkillCreditMultiplier(self, mult):
        self.__skillCreditMultiplier = mult

    def getSkillCreditMultiplier(self):
        return self.__skillCreditMultiplier

    def cleanup(self):
        self.battle = None
        return

    def __calcToonAtkHit(self, attackIndex, atkTargets):
        toon = self.battle.getToon(attackIndex)
        if len(atkTargets) == 0:
            return (0, 0)
        if toon.getInstaKill() or toon.getAlwaysHitSuits():
            return (1, 95)
        if self.tutorialFlag:
            return (1, 95)
        if self.toonsAlways5050:
            roll = random.randint(0, 99)
            if roll < 50:
                return (1, 95)
            else:
                return (0, 0)
        if self.toonsAlwaysHit:
            return (1, 95)
        elif self.toonsAlwaysMiss:
            return (0, 0)
        debug = self.notify.getDebug()
        attack = self.battle.toonAttacks[attackIndex]
        atkTrack, atkLevel = self.__getActualTrackLevel(attack)
        if atkTrack == NPCSOS:
            return (1, 95)
        if atkTrack == FIRE:
            return (1, 95)
        if atkTrack == TRAP:
            if debug:
                self.notify.debug('Attack is a trap, so it hits regardless')
            attack[TOON_ACCBONUS_COL] = 0
            return (1, 100)
        elif atkTrack == DROP and attack[TOON_TRACK_COL] == NPCSOS:
            unluredSuits = 0
            for tgt in atkTargets:
                if not self.__suitIsLured(tgt.getDoId()):
                    unluredSuits = 1

            if unluredSuits == 0:
                attack[TOON_ACCBONUS_COL] = 1
                return (0, 0)
        elif atkTrack == DROP:
            allLured = True
            for i in xrange(len(atkTargets)):
                if self.__suitIsLured(atkTargets[i].getDoId()):
                    pass
                else:
                    allLured = False

            if allLured:
                attack[TOON_ACCBONUS_COL] = 1
                return (0, 0)
        elif atkTrack == PETSOS:
            return self.__calculatePetTrickSuccess(attack)
        tgtDef = 0
        numLured = 0
        if atkTrack != HEAL:
            for currTarget in atkTargets:
                thisSuitDef = self.__targetDefense(currTarget, atkTrack)
                if debug:
                    self.notify.debug('Examining suit def for toon attack: ' + str(thisSuitDef))
                tgtDef = min(thisSuitDef, tgtDef)
                if self.__suitIsLured(currTarget.getDoId()):
                    numLured += 1

        trackExp = self.__toonTrackExp(attack[TOON_ID_COL], atkTrack)
        for currOtherAtk in self.toonAtkOrder:
            if currOtherAtk != attack[TOON_ID_COL]:
                nextAttack = self.battle.toonAttacks[currOtherAtk]
                nextAtkTrack = self.__getActualTrack(nextAttack)
                if atkTrack == nextAtkTrack and attack[TOON_TGT_COL] == nextAttack[TOON_TGT_COL]:
                    currTrackExp = self.__toonTrackExp(nextAttack[TOON_ID_COL], atkTrack)
                    if debug:
                        self.notify.debug('Examining toon track exp bonus: ' + str(currTrackExp))
                    trackExp = max(currTrackExp, trackExp)

        if debug:
            if atkTrack == HEAL:
                self.notify.debug('Toon attack is a heal, no target def used')
            else:
                self.notify.debug('Suit defense used for toon attack: ' + str(tgtDef))
            self.notify.debug('Toon track exp bonus used for toon attack: ' + str(trackExp))
        if attack[TOON_TRACK_COL] == NPCSOS:
            randChoice = 0
        else:
            randChoice = random.randint(0, 99)
        propAcc = AvPropAccuracy[atkTrack][atkLevel]
        attackAcc = propAcc + trackExp + tgtDef
        currAtk = self.toonAtkOrder.index(attackIndex)
        if currAtk > 0 and atkTrack != HEAL:
            prevAtkId = self.toonAtkOrder[currAtk - 1]
            prevAttack = self.battle.toonAttacks[prevAtkId]
            prevAtkTrack = self.__getActualTrack(prevAttack)
            lure = atkTrack == LURE and (not attackAffectsGroup(atkTrack, atkLevel, 
             attack[TOON_TRACK_COL]) and attack[TOON_TGT_COL] in self.successfulLures or attackAffectsGroup(atkTrack, atkLevel, attack[TOON_TRACK_COL]))
            if atkTrack == prevAtkTrack and (attack[TOON_TGT_COL] == prevAttack[TOON_TGT_COL] or lure):
                if prevAttack[TOON_ACCBONUS_COL] == 1:
                    if debug:
                        self.notify.debug('DODGE: Toon attack track dodged')
                elif prevAttack[TOON_ACCBONUS_COL] == 0:
                    if debug:
                        self.notify.debug('HIT: Toon attack track hit')
                attack[TOON_ACCBONUS_COL] = prevAttack[TOON_ACCBONUS_COL]
                return (not attack[TOON_ACCBONUS_COL], attackAcc)
        atkAccResult = attackAcc
        if debug:
            self.notify.debug('setting atkAccResult to %d' % atkAccResult)
        acc = attackAcc + self.__calcToonAccBonus(attackIndex)
        if atkTrack != LURE and atkTrack != HEAL:
            if atkTrack != DROP:
                if numLured == len(atkTargets):
                    if debug:
                        self.notify.debug('all targets are lured, attack hits')
                    attack[TOON_ACCBONUS_COL] = 0
                    return (1, 100)
                else:
                    luredRatio = float(numLured) / float(len(atkTargets))
                    accAdjust = 100 * luredRatio
                    if accAdjust > 0 and debug:
                        self.notify.debug(str(numLured) + ' out of ' + str(len(atkTargets)) + ' targets are lured, so adding ' + str(accAdjust) + ' to attack accuracy')
                    acc += accAdjust
            elif numLured == len(atkTargets):
                if debug:
                    self.notify.debug('all targets are lured, attack misses')
                attack[TOON_ACCBONUS_COL] = 0
                return (0, 0)
        if acc > MaxToonAcc:
            acc = MaxToonAcc
        if randChoice < acc:
            if debug:
                self.notify.debug('HIT: Toon attack rolled' + str(randChoice) + 'to hit with an accuracy of' + str(acc))
            attack[TOON_ACCBONUS_COL] = 0
        else:
            if debug:
                self.notify.debug('MISS: Toon attack rolled' + str(randChoice) + 'to hit with an accuracy of' + str(acc))
            attack[TOON_ACCBONUS_COL] = 1
        return (not attack[TOON_ACCBONUS_COL], atkAccResult)

    def __toonTrackExp(self, toonId, track):
        toon = self.battle.getToon(toonId)
        if toon != None:
            toonExpLvl = toon.experience.getExpLevel(track)
            exp = self.AttackExpPerTrack[toonExpLvl]
            if track == HEAL:
                exp = exp * 0.5
            self.notify.debug('Toon track exp: ' + str(toonExpLvl) + ' and resulting acc bonus: ' + str(exp))
            return exp
        else:
            return 0
        return

    def __targetDefense(self, suit, atkTrack):
        if atkTrack == HEAL:
            return 0
        if suit.getActualLevel() > 7:
            suitDef = SuitBattleGlobals.SuitAttributes[suit.dna.name]['def'][0]
        else:
            suitDef = SuitBattleGlobals.SuitAttributes[suit.dna.name]['def'][suit.getLevel()]

        if self.suitHasCondition(suit, 'soaked'):
            suitDef -= ToontownBattleGlobals.AvSoakDefReduction

        return -suitDef

    def __createToonTargetList(self, attackIndex):
        attack = self.battle.toonAttacks[attackIndex]
        atkTrack, atkLevel = self.__getActualTrackLevel(attack)
        targetList = []
        if atkTrack == NPCSOS:
            return targetList
        if not attackAffectsGroup(atkTrack, atkLevel, attack[TOON_TRACK_COL]):
            if atkTrack == HEAL:
                target = attack[TOON_TGT_COL]
            else:
                target = self.battle.findSuit(attack[TOON_TGT_COL])
            if target != None:
                targetList.append(target)
        else:
            if atkTrack == HEAL or atkTrack == PETSOS:
                if attack[TOON_TRACK_COL] == NPCSOS or atkTrack == PETSOS:
                    targetList = self.battle.activeToons
                else:
                    for currToon in self.battle.activeToons:
                        if attack[TOON_ID_COL] != currToon:
                            targetList.append(currToon)

            else:
                targetList = self.battle.activeSuits
        return targetList

    def __prevAtkTrack(self, attackerId, toon=1):
        if toon:
            prevAtkIdx = self.toonAtkOrder.index(attackerId) - 1
            if prevAtkIdx >= 0:
                prevAttackerId = self.toonAtkOrder[prevAtkIdx]
                attack = self.battle.toonAttacks[prevAttackerId]
                return self.__getActualTrack(attack)
            else:
                return NO_ATTACK

    def getSuitTrapType(self, suitId):
        if suitId in self.traps:
            if self.traps[suitId][0] == self.TRAP_CONFLICT:
                return NO_TRAP
            else:
                return self.traps[suitId][0]
        else:
            return NO_TRAP

    def __suitTrapDamage(self, suitId):
        if suitId in self.traps:
            return self.traps[suitId][2]
        else:
            return 0

    def addTrainTrapForJoiningSuit(self, suitId):
        self.notify.debug('addTrainTrapForJoiningSuit suit=%d self.traps=%s' % (suitId, self.traps))
        trapInfoToUse = None
        for trapInfo in self.traps.values():
            if trapInfo[0] == UBER_GAG_LEVEL_INDEX:
                trapInfoToUse = trapInfo
                break

        if trapInfoToUse:
            self.traps[suitId] = trapInfoToUse
        else:
            self.notify.warning('huh we did not find a train trap?')
        return

    def __addSuitGroupTrap(self, suitId, trapLvl, attackerId, allSuits, npcDamage=0):
        if npcDamage == 0:
            if suitId in self.traps:
                if self.traps[suitId][0] == self.TRAP_CONFLICT:
                    pass
                else:
                    self.traps[suitId][0] = self.TRAP_CONFLICT
                for suit in allSuits:
                    id = suit.doId
                    if id in self.traps:
                        self.traps[id][0] = self.TRAP_CONFLICT
                    else:
                        self.traps[id] = [
                         self.TRAP_CONFLICT, 0, 0]

            else:
                toon = self.battle.getToon(attackerId)
                suit = self.battle.findSuit(suitId)
                damage = getTrapDamage(trapLvl, toon, suit)
                if self.itemIsCredit(TRAP, trapLvl):
                    self.traps[suitId] = [
                     trapLvl, attackerId, damage]
                else:
                    self.traps[suitId] = [trapLvl, 0, damage]
                self.notify.debug('calling __addLuredSuitsDelayed')
                self.__addLuredSuitsDelayed(attackerId, targetId=-1, ignoreDamageCheck=True)
        else:
            if suitId in self.traps:
                if self.traps[suitId][0] == self.TRAP_CONFLICT:
                    self.traps[suitId] = [
                     trapLvl, 0, npcDamage]
            else:
                if not self.__suitIsLured(suitId):
                    self.traps[suitId] = [
                     trapLvl, 0, npcDamage]

    def __addSuitTrap(self, suitId, trapLvl, attackerId, npcDamage=0):
        if npcDamage == 0:
            if suitId in self.traps:
                if self.traps[suitId][0] == self.TRAP_CONFLICT:
                    pass
                else:
                    self.traps[suitId][0] = self.TRAP_CONFLICT
            else:
                toon = self.battle.getToon(attackerId)
                suit = self.battle.findSuit(suitId)
                damage = getTrapDamage(trapLvl, toon, suit)
                if self.itemIsCredit(TRAP, trapLvl):
                    self.traps[suitId] = [
                     trapLvl, attackerId, damage]
                else:
                    self.traps[suitId] = [trapLvl, 0, damage]
        else:
            if suitId in self.traps:
                if self.traps[suitId][0] == self.TRAP_CONFLICT:
                    self.traps[suitId] = [
                     trapLvl, 0, npcDamage]
            else:
                if not self.__suitIsLured(suitId):
                    self.traps[suitId] = [
                     trapLvl, 0, npcDamage]

    def __removeSuitTrap(self, suitId):
        if suitId in self.traps:
            del self.traps[suitId]

    def __clearTrapCreator(self, creatorId, suitId=None):
        if suitId == None:
            for currTrap in self.traps.keys():
                if creatorId == self.traps[currTrap][1]:
                    self.traps[currTrap][1] = 0

        elif suitId in self.traps:
            self.traps[suitId][1] = 0
        return

    def __trapCreator(self, suitId):
        if suitId in self.traps:
            return self.traps[suitId][1]
        else:
            return 0

    def __initTraps(self):
        self.trainTrapTriggered = False
        keysList = self.traps.keys()
        for currTrap in keysList:
            if self.traps[currTrap][0] == self.TRAP_CONFLICT:
                del self.traps[currTrap]

    def __calcToonAtkHp(self, toonId):
        attack = self.battle.toonAttacks[toonId]
        targetList = self.__createToonTargetList(toonId)
        atkHit, atkAcc = self.__calcToonAtkHit(toonId, targetList)
        atkTrack, atkLevel, atkHp = self.__getActualTrackLevelHp(attack)
        if not atkHit and atkTrack != HEAL:
            return
        validTargetAvail = 0
        lureDidDamage = 0
        currLureId = -1
        for currTarget in xrange(len(targetList)):
            attackLevel = -1
            attackTrack = None
            attackDamage = 0
            toonTarget = 0
            targetLured = 0
            if atkTrack == HEAL or atkTrack == PETSOS:
                targetId = targetList[currTarget]
                toonTarget = 1
            else:
                targetId = targetList[currTarget].getDoId()
            if atkTrack == LURE:
                if self.getSuitTrapType(targetId) == NO_TRAP:
                    if self.notify.getDebug():
                        self.notify.debug('Suit lured, but no trap exists')
                    if self.SUITS_UNLURED_IMMEDIATELY:
                        if not self.__suitIsLured(targetId, prevRound=1):
                            if not self.__combatantDead(targetId, toon=toonTarget):
                                validTargetAvail = 1
                            rounds = self.NumRoundsLured[atkLevel]
                            wakeupChance = 100 - atkAcc * 2
                            npcLurer = attack[TOON_TRACK_COL] == NPCSOS
                            currLureId = self.__addLuredSuitInfo(targetId, -1, rounds, wakeupChance, toonId, atkLevel, lureId=currLureId, npc=npcLurer)
                            if self.notify.getDebug():
                                self.notify.debug('Suit lured for ' + str(rounds) + ' rounds max with ' + str(wakeupChance) + '% chance to wake up each round')
                            targetLured = 1
                else:
                    attackTrack = TRAP
                    if targetId in self.traps:
                        trapInfo = self.traps[targetId]
                        attackLevel = trapInfo[0]
                    else:
                        attackLevel = NO_TRAP
                    attackDamage = self.__suitTrapDamage(targetId)
                    trapCreatorId = self.__trapCreator(targetId)
                    if trapCreatorId > 0:
                        self.notify.debug('Giving trap EXP to toon ' + str(trapCreatorId))
                        self.__addAttackExp(attack, track=TRAP, level=attackLevel, attackerId=trapCreatorId)
                    self.__clearTrapCreator(trapCreatorId, targetId)
                    lureDidDamage = 1
                    if self.notify.getDebug():
                        self.notify.debug('Suit lured right onto a trap! (' + str(AvProps[attackTrack][attackLevel]) + ',' + str(attackLevel) + ')')
                    if not self.__combatantDead(targetId, toon=toonTarget):
                        validTargetAvail = 1
                    targetLured = 1
                if not self.SUITS_UNLURED_IMMEDIATELY:
                    if not self.__suitIsLured(targetId, prevRound=1):
                        if not self.__combatantDead(targetId, toon=toonTarget):
                            validTargetAvail = 1
                        rounds = self.NumRoundsLured[atkLevel]
                        wakeupChance = 100 - atkAcc * 2
                        npcLurer = attack[TOON_TRACK_COL] == NPCSOS
                        currLureId = self.__addLuredSuitInfo(targetId, -1, rounds, wakeupChance, toonId, atkLevel, lureId=currLureId, npc=npcLurer)
                        if self.notify.getDebug():
                            self.notify.debug('Suit lured for ' + str(rounds) + ' rounds max with ' + str(wakeupChance) + '% chance to wake up each round')
                        targetLured = 1
                    if attackLevel != -1:
                        self.__addLuredSuitsDelayed(toonId, targetId)
                if targetLured and (targetId not in self.successfulLures or targetId in self.successfulLures and self.successfulLures[targetId][1] < atkLevel):
                    self.notify.debug('Adding target ' + str(targetId) + ' to successfulLures list')
                    self.successfulLures[targetId] = [
                     toonId, atkLevel, atkAcc, -1]
            else:
                if atkTrack == TRAP:
                    npcDamage = 0
                    if attack[TOON_TRACK_COL] == NPCSOS:
                        npcDamage = atkHp
                    if self.CLEAR_MULTIPLE_TRAPS:
                        if self.getSuitTrapType(targetId) != NO_TRAP:
                            self.__clearAttack(toonId)
                            return
                    if atkLevel == UBER_GAG_LEVEL_INDEX:
                        self.__addSuitGroupTrap(targetId, atkLevel, toonId, targetList, npcDamage)
                        if self.__suitIsLured(targetId):
                            self.notify.debug('Train Trap on lured suit %d, \n indicating with KBBONUS_COL flag' % targetId)
                            tgtPos = self.battle.activeSuits.index(targetList[currTarget])
                            attack[TOON_KBBONUS_COL][tgtPos] = self.KBBONUS_LURED_FLAG
                    else:
                        self.__addSuitTrap(targetId, atkLevel, toonId, npcDamage)
                elif self.__suitIsLured(targetId) and atkTrack == SOUND:
                    self.notify.debug('Sound on lured suit, ' + 'indicating with KBBONUS_COL flag')
                    tgtPos = self.battle.activeSuits.index(targetList[currTarget])
                    attack[TOON_KBBONUS_COL][tgtPos] = self.KBBONUS_LURED_FLAG
                attackLevel = atkLevel
                attackTrack = atkTrack
                toon = self.battle.getToon(toonId)
                if attack[TOON_TRACK_COL] == NPCSOS and lureDidDamage != 1 or attack[TOON_TRACK_COL] == PETSOS:
                    attackDamage = atkHp
                elif atkTrack == FIRE:
                    suit = self.battle.findSuit(targetId)
                    if suit:
                        costToFire = math.ceil(suit.getActualLevel() / 2.0)
                        abilityToFire = toon.getPinkSlips()
                        toon.removePinkSlips(costToFire)
                        if costToFire > abilityToFire:
                            commentStr = 'Toon attempting to fire a %s cost cog with %s pinkslips' % (costToFire, abilityToFire)
                            simbase.air.writeServerEvent('suspicious', toonId, commentStr)
                            dislId = toon.DISLid
                            simbase.air.banManager.ban(toonId, dislId, commentStr)
                            print 'Not enough PinkSlips to fire cog - print a warning here'
                        else:
                            suit.skeleRevives = 0
                            if suit.getManager():
                                attackDamage = 0
                            else:
                                attackDamage = suit.getHP()
                    else:
                        attackDamage = 0
                    bonus = 0
                elif atkTrack == SOUND:   # sound's prestige from clash
                    highestLevel = 1
                    for suit in self.battle.suits:
                        if suit.getActualLevel() > highestLevel:
                            highestLevel = suit.getActualLevel()
                    attackDamage = getAvPropDamage(attackTrack, attackLevel, toon.experience.getExp(attackTrack)) + math.ceil(highestLevel / 2.0)
                elif atkTrack == HEAL:
                    attackDamage = getAvPropDamage(attackTrack, attackLevel, toon.experience.getExp(attackTrack))
                    toon.toonUp(math.ceil(attackDamage / 2))
                elif atkTrack == SQUIRT:
                    suit = self.battle.findSuit(targetId)
                    self.setSuitCondition(suit, 'soaked', 1, self.NumRoundsSoaked[attackLevel], 'alternateBoth')
                    attackDamage = getAvPropDamage(attackTrack, attackLevel, toon.experience.getExp(attackTrack))
                else:
                    attackDamage = getAvPropDamage(attackTrack, attackLevel, toon.experience.getExp(attackTrack))
                if not self.__combatantDead(targetId, toon=toonTarget):
                    if self.__suitIsLured(targetId) and atkTrack == DROP:
                        self.notify.debug('not setting validTargetAvail, since drop on a lured suit')
                    else:
                        validTargetAvail = 1
            if attackLevel == -1 and not atkTrack == FIRE:
                result = LURE_SUCCEEDED
            elif atkTrack != TRAP:
                toon = self.battle.getToon(toonId)
                if toon and toon.getInstaKill() and atkTrack != HEAL:
                    targetSuit = self.battle.findSuit(targetId)
                    for target in targetList:
                        if target.getHP() > targetSuit.getHP():
                            targetSuit = target
                    attackDamage = targetSuit.getHP()
                result = attackDamage
                if atkTrack == HEAL:
                    if not self.__attackHasHit(attack, suit=0):
                        result = result * 0.2
                    if self.notify.getDebug():
                        self.notify.debug('toon does ' + str(result) + ' healing to toon(s)')
                else:
                    if self.__suitIsLured(targetId) and atkTrack == DROP:
                        result = 0
                        self.notify.debug('setting damage to 0, since drop on a lured suit')
                    if self.battle.findSuit(targetId).dna.name in ['hst', 'ssb'] and self.numShadowsSummoned > 0:
                        self.notify.debug('Shadow Count exceeds 1 (%i), processing attack damage' % self.numShadowsSummoned)
                        self.notify.debug('Multiplying toon damage by %f' % (1 + (self.numShadowsSummoned * ToontownBattleGlobals.HUSTLER_BONUS_DMG_PER_SHADOW)))
                        result *= (1 + (self.numShadowsSummoned * ToontownBattleGlobals.HUSTLER_BONUS_DMG_PER_SHADOW))
                        
                    
                    if self.notify.getDebug():
                        self.notify.debug('toon does ' + str(result) + ' damage to suit')
            else:
                result = 0
            if result != 0 or atkTrack == PETSOS:
                targets = self.__getToonTargets(attack)
                if targetList[currTarget] not in targets:
                    if self.notify.getDebug():
                        self.notify.debug('Target of toon is not accessible!')
                    continue
                targetIndex = targets.index(targetList[currTarget])
                if atkTrack == HEAL:
                    result = result / len(targetList)
                    if self.notify.getDebug():
                        self.notify.debug('Splitting heal among ' + str(len(targetList)) + ' targets')
                if targetId in self.successfulLures and atkTrack == LURE:
                    self.notify.debug('Updating lure damage to ' + str(result))
                    self.successfulLures[targetId][3] = result
                else:
                    attack[TOON_HP_COL][targetIndex] = result
                if result > 0 and atkTrack != HEAL and atkTrack != DROP and atkTrack != PETSOS:
                    attackTrack = LURE
                    lureInfos = self.__getLuredExpInfo(targetId)
                    for currInfo in lureInfos:
                        if currInfo[3]:
                            self.notify.debug('Giving lure EXP to toon ' + str(currInfo[0]))
                            self.__addAttackExp(attack, track=attackTrack, level=currInfo[1], attackerId=currInfo[0])
                        self.__clearLurer(currInfo[0], lureId=currInfo[2])

        if lureDidDamage:
            if self.itemIsCredit(atkTrack, atkLevel):
                self.notify.debug('Giving lure EXP to toon ' + str(toonId))
                self.__addAttackExp(attack)
        if not validTargetAvail and self.__prevAtkTrack(toonId) != atkTrack:
            self.__clearAttack(toonId)
        return

    def __getToonTargets(self, attack):
        track = self.__getActualTrack(attack)
        if track == HEAL or track == PETSOS:
            return self.battle.activeToons
        else:
            return self.battle.activeSuits

    def __attackHasHit(self, attack, suit=0):
        if suit == 1:
            for dmg in attack[SUIT_HP_COL]:
                if dmg > 0:
                    return 1

            return 0
        else:
            track = self.__getActualTrack(attack)
            return not attack[TOON_ACCBONUS_COL] and track != NO_ATTACK

    def __attackDamage(self, attack, suit=0):
        if suit:
            for dmg in attack[SUIT_HP_COL]:
                if dmg > 0:
                    return dmg

            return 0
        else:
            for dmg in attack[TOON_HP_COL]:
                if dmg > 0:
                    return dmg

            return 0

    def __attackDamageForTgt(self, attack, tgtPos, suit=0):
        if suit:
            return attack[SUIT_HP_COL][tgtPos]
        else:
            return attack[TOON_HP_COL][tgtPos]

    def __calcToonAccBonus(self, attackKey):
        numPrevHits = 0
        attackIdx = self.toonAtkOrder.index(attackKey)
        for currPrevAtk in xrange(attackIdx - 1, -1, -1):
            attack = self.battle.toonAttacks[attackKey]
            atkTrack, atkLevel = self.__getActualTrackLevel(attack)
            prevAttackKey = self.toonAtkOrder[currPrevAtk]
            prevAttack = self.battle.toonAttacks[prevAttackKey]
            prvAtkTrack, prvAtkLevel = self.__getActualTrackLevel(prevAttack)
            if self.__attackHasHit(prevAttack) and (attackAffectsGroup(prvAtkTrack, prvAtkLevel, prevAttack[TOON_TRACK_COL]) or attackAffectsGroup(atkTrack, atkLevel, attack[TOON_TRACK_COL]) or attack[TOON_TGT_COL] == prevAttack[TOON_TGT_COL]) and atkTrack != prvAtkTrack:
                numPrevHits += 1

        if numPrevHits > 0 and self.notify.getDebug():
            self.notify.debug('ACC BONUS: toon attack received accuracy ' + 'bonus of ' + str(self.AccuracyBonuses[numPrevHits]) + ' from previous attack by (' + str(attack[TOON_ID_COL]) + ') which hit')
        return self.AccuracyBonuses[numPrevHits]

    def __applyToonAttackDamages(self, toonId, hpbonus = 0, kbbonus = 0):
        totalDamages = 0
        if not self.APPLY_HEALTH_ADJUSTMENTS:
            return totalDamages
        attack = self.battle.toonAttacks[toonId]
        track = self.__getActualTrack(attack)
        if track != NO_ATTACK and track != SOS and track != TRAP and track != NPCSOS:
            targets = self.__getToonTargets(attack)
            for position in xrange(len(targets)):
                if hpbonus:
                    if targets[position] in self.__createToonTargetList(toonId):
                        damageDone = attack[TOON_HPBONUS_COL]
                    else:
                        damageDone = 0
                elif kbbonus:
                    if targets[position] in self.__createToonTargetList(toonId):
                        damageDone = attack[TOON_KBBONUS_COL][position]
                    else:
                        damageDone = 0
                else:
                    damageDone = attack[TOON_HP_COL][position]
                if damageDone <= 0 or self.immortalSuits:
                    continue
                if track == HEAL or track == PETSOS:
                    currTarget = targets[position]
                    if self.CAP_HEALS:
                        toonHp = self.__getToonHp(currTarget)
                        toonMaxHp = self.__getToonMaxHp(currTarget)
                        if toonHp + damageDone > toonMaxHp:
                            damageDone = toonMaxHp - toonHp
                            attack[TOON_HP_COL][position] = damageDone
                    self.toonHPAdjusts[currTarget] += damageDone
                    totalDamages = totalDamages + damageDone
                    continue
                currTarget = targets[position]
                currTarget.setHP(currTarget.getHP() - damageDone)
                targetId = currTarget.getDoId()
                if self.notify.getDebug():
                    if hpbonus:
                        self.notify.debug(str(targetId) + ': suit takes ' + str(damageDone) + ' damage from HP-Bonus')
                    elif kbbonus:
                        self.notify.debug(str(targetId) + ': suit takes ' + str(damageDone) + ' damage from KB-Bonus')
                    else:
                        self.notify.debug(str(targetId) + ': suit takes ' + str(damageDone) + ' damage')
                totalDamages = totalDamages + damageDone
                if currTarget.getHP() <= 0:
                    if currTarget.getSkeleRevives() >= 1:
                        currTarget.useSkeleRevive()
                        attack[SUIT_REVIVE_COL] = attack[SUIT_REVIVE_COL] | 1 << position
                    else:
                        self.suitLeftBattle(targetId)
                        attack[SUIT_DIED_COL] = attack[SUIT_DIED_COL] | 1 << position
                        if self.notify.getDebug():
                            self.notify.debug('Suit' + str(targetId) + 'bravely expired in combat')

        return totalDamages

    def __combatantDead(self, avId, toon):
        if toon:
            if self.__getToonHp(avId) <= 0:
                return 1
        else:
            suit = self.battle.findSuit(avId)
            if suit.getHP() <= 0:
                return 1
        return 0

    def __combatantJustRevived(self, avId):
        suit = self.battle.findSuit(avId)
        if suit.reviveCheckAndClear():
            return 1
        else:
            return 0

    def __addAttackExp(self, attack, track = -1, level = -1, attackerId = -1):
        trk = -1
        lvl = -1
        id = -1
        if track != -1 and level != -1 and attackerId != -1:
            trk = track
            lvl = level
            id = attackerId
        elif self.__attackHasHit(attack):
            if self.notify.getDebug():
                self.notify.debug('Attack ' + repr(attack) + ' has hit')
            trk = attack[TOON_TRACK_COL]
            lvl = attack[TOON_LVL_COL]
            id = attack[TOON_ID_COL]
        if trk != -1 and trk != NPCSOS and trk != PETSOS and lvl != -1 and id != -1:
            expList = self.toonSkillPtsGained.get(id, None)
            if expList == None:
                expList = [0,
                 0,
                 0,
                 0,
                 0,
                 0,
                 0]
                self.toonSkillPtsGained[id] = expList
            expList[trk] = min(ExperienceCap, expList[trk] + (lvl + 1) * self.__skillCreditMultiplier)
        return

    def __clearTgtDied(self, tgt, lastAtk, currAtk):
        position = self.battle.activeSuits.index(tgt)
        currAtkTrack = self.__getActualTrack(currAtk)
        lastAtkTrack = self.__getActualTrack(lastAtk)
        if currAtkTrack == lastAtkTrack and lastAtk[SUIT_DIED_COL] & 1 << position and self.__attackHasHit(currAtk, suit=0):
            if self.notify.getDebug():
                self.notify.debug('Clearing suit died for ' + str(tgt.getDoId()) + ' at position ' + str(position) + ' from toon attack ' + str(lastAtk[TOON_ID_COL]) + ' and setting it for ' + str(currAtk[TOON_ID_COL]))
            lastAtk[SUIT_DIED_COL] = lastAtk[SUIT_DIED_COL] ^ 1 << position
            self.suitLeftBattle(tgt.getDoId())
            currAtk[SUIT_DIED_COL] = currAtk[SUIT_DIED_COL] | 1 << position

    def __addDmgToBonuses(self, dmg, attackIndex, hp=1):
        toonId = self.toonAtkOrder[attackIndex]
        attack = self.battle.toonAttacks[toonId]
        atkTrack = self.__getActualTrack(attack)
        if atkTrack == HEAL or atkTrack == PETSOS:
            return
        tgts = self.__createToonTargetList(toonId)
        for currTgt in tgts:
            tgtPos = self.battle.suits.index(currTgt)
            attackerId = self.toonAtkOrder[attackIndex]
            attack = self.battle.toonAttacks[attackerId]
            track = self.__getActualTrack(attack)
            if hp:
                if track in self.hpBonuses[tgtPos]:
                    self.hpBonuses[tgtPos][track].append([attackIndex, dmg])
                else:
                    self.hpBonuses[tgtPos][track] = [
                     [
                      attackIndex, dmg]]
            elif self.__suitIsLured(currTgt.getDoId()):
                if track in self.kbBonuses[tgtPos]:
                    self.kbBonuses[tgtPos][track].append([attackIndex, dmg])
                else:
                    self.kbBonuses[tgtPos][track] = [
                     [
                      attackIndex, dmg]]

    def __clearBonuses(self, hp=1):
        if hp:
            self.hpBonuses = [{}, {}, {}, {}]
        else:
            self.kbBonuses = [{}, {}, {}, {}]

    def __bonusExists(self, tgtSuit, hp=1):
        tgtPos = self.activeSuits.index(tgtSuit)
        if hp:
            bonusLen = len(self.hpBonuses[tgtPos])
        else:
            bonusLen = len(self.kbBonuses[tgtPos])
        if bonusLen > 0:
            return 1
        return 0

    def __processBonuses(self, hp=1):
        if hp:
            bonusList = self.hpBonuses
            self.notify.debug('Processing hpBonuses: ' + repr(self.hpBonuses))
        else:
            bonusList = self.kbBonuses
            self.notify.debug('Processing kbBonuses: ' + repr(self.kbBonuses))
        tgtPos = 0
        for currTgt in bonusList:
            for currAtkType in currTgt.keys():
                if len(currTgt[currAtkType]) > 1 or not hp and len(currTgt[currAtkType]) > 0:
                    totalDmgs = 0
                    for currDmg in currTgt[currAtkType]:
                        totalDmgs += currDmg[1]

                    numDmgs = len(currTgt[currAtkType])
                    attackIdx = currTgt[currAtkType][numDmgs - 1][0]
                    attackerId = self.toonAtkOrder[attackIdx]
                    attack = self.battle.toonAttacks[attackerId]
                    if hp and currAtkType != 6:
                        attack[TOON_HPBONUS_COL] = math.ceil(totalDmgs * (self.DamageBonuses[numDmgs - 1] * 0.01))
                        if self.notify.getDebug():
                            self.notify.debug('Applying hp bonus to track ' + str(attack[TOON_TRACK_COL]) + ' of ' + str(attack[TOON_HPBONUS_COL]))
                    elif hp and currAtkType == 6:
                        attack[TOON_HPBONUS_COL] = math.ceil(totalDmgs * (self.DropDamageBonuses[numDmgs - 1] * 0.01))
                        if self.notify.getDebug():
                            self.notify.debug('Applying drop hp bonus to track ' + str(attack[TOON_TRACK_COL]) + ' of ' + str(attack[TOON_HPBONUS_COL]))                        
                    elif len(attack[TOON_KBBONUS_COL]) > tgtPos:
                        attack[TOON_KBBONUS_COL][tgtPos] = totalDmgs * ToontownBattleGlobals.LURE_KNOCKBACK_VALUE
                        if self.notify.getDebug():
                            self.notify.debug('Applying kb bonus to track ' + str(attack[TOON_TRACK_COL]) + ' of ' + str(attack[TOON_KBBONUS_COL][tgtPos]) + ' to target ' + str(tgtPos))
                    else:
                        self.notify.warning('invalid tgtPos for knock back bonus: %d' % tgtPos)

            tgtPos += 1

        if hp:
            self.__clearBonuses()
        else:
            self.__clearBonuses(hp=0)

    def __handleBonus(self, attackIdx, hp=1):
        attackerId = self.toonAtkOrder[attackIdx]
        attack = self.battle.toonAttacks[attackerId]
        atkDmg = self.__attackDamage(attack, suit=0)
        atkTrack = self.__getActualTrack(attack)
        if atkDmg > 0:
            if hp:
                if atkTrack != LURE:
                    self.notify.debug('Adding dmg of ' + str(atkDmg) + ' to hpBonuses list')
                    self.__addDmgToBonuses(atkDmg, attackIdx)
            elif self.__knockBackAtk(attackerId, toon=1):
                self.notify.debug('Adding dmg of ' + str(atkDmg) + ' to kbBonuses list')
                self.__addDmgToBonuses(atkDmg, attackIdx, hp=0)

    def __clearAttack(self, attackIdx, toon=1):
        if toon:
            if self.notify.getDebug():
                self.notify.debug('clearing out toon attack for toon ' + str(attackIdx) + '...')
            attack = self.battle.toonAttacks[attackIdx]
            self.battle.toonAttacks[attackIdx] = getToonAttack(attackIdx)
            longest = max(len(self.battle.activeToons), len(self.battle.activeSuits))
            taList = self.battle.toonAttacks
            for j in xrange(longest):
                taList[attackIdx][TOON_HP_COL].append(-1)
                taList[attackIdx][TOON_KBBONUS_COL].append(-1)

            if self.notify.getDebug():
                self.notify.debug('toon attack is now ' + repr(self.battle.toonAttacks[attackIdx]))
        else:
            self.notify.warning('__clearAttack not implemented for suits!')

    def __rememberToonAttack(self, suitId, toonId, damage):
        if suitId not in self.SuitAttackers:
            self.SuitAttackers[suitId] = {toonId: damage}
        else:
            if toonId not in self.SuitAttackers[suitId]:
                self.SuitAttackers[suitId][toonId] = damage
            else:
                if self.SuitAttackers[suitId][toonId] <= damage:
                    self.SuitAttackers[suitId] = [
                     toonId, damage]

    def __postProcessToonAttacks(self):
        self.notify.debug('__postProcessToonAttacks()')
        lastTrack = -1
        lastAttacks = []
        self.__clearBonuses()
        for currToonAttack in self.toonAtkOrder:
            if currToonAttack != -1:
                attack = self.battle.toonAttacks[currToonAttack]
                atkTrack, atkLevel = self.__getActualTrackLevel(attack)
                if atkTrack != HEAL and atkTrack != SOS and atkTrack != NO_ATTACK and atkTrack != NPCSOS and atkTrack != PETSOS:
                    targets = self.__createToonTargetList(currToonAttack)
                    allTargetsDead = 1
                    for currTgt in targets:
                        damageDone = self.__attackDamage(attack, suit=0)
                        if damageDone > 0:
                            self.__rememberToonAttack(currTgt.getDoId(), attack[TOON_ID_COL], damageDone)
                        if atkTrack == TRAP:
                            if currTgt.doId in self.traps:
                                trapInfo = self.traps[currTgt.doId]
                                currTgt.battleTrap = trapInfo[0]
                        targetDead = 0
                        if currTgt.getHP() > 0:
                            allTargetsDead = 0
                        else:
                            targetDead = 1
                            if atkTrack != LURE:
                                for currLastAtk in lastAttacks:
                                    self.__clearTgtDied(currTgt, currLastAtk, attack)

                        tgtId = currTgt.getDoId()
                        if tgtId in self.successfulLures and atkTrack == LURE:
                            lureInfo = self.successfulLures[tgtId]
                            self.notify.debug('applying lure data: ' + repr(lureInfo))
                            toonId = lureInfo[0]
                            lureAtk = self.battle.toonAttacks[toonId]
                            tgtPos = self.battle.activeSuits.index(currTgt)
                            if currTgt.doId in self.traps:
                                trapInfo = self.traps[currTgt.doId]
                                if trapInfo[0] == UBER_GAG_LEVEL_INDEX:
                                    self.notify.debug('train trap triggered for %d' % currTgt.doId)
                                    self.trainTrapTriggered = True
                            self.__removeSuitTrap(tgtId)
                            lureAtk[TOON_KBBONUS_COL][tgtPos] = self.KBBONUS_TGT_LURED
                            lureAtk[TOON_HP_COL][tgtPos] = lureInfo[3]
                        elif self.__suitIsLured(tgtId) and atkTrack == DROP:
                            self.notify.debug('Drop on lured suit, ' + 'indicating with KBBONUS_COL ' + 'flag')
                            tgtPos = self.battle.activeSuits.index(currTgt)
                            attack[TOON_KBBONUS_COL][tgtPos] = self.KBBONUS_LURED_FLAG
                        if targetDead and atkTrack != lastTrack:
                            tgtPos = self.battle.activeSuits.index(currTgt)
                            attack[TOON_HP_COL][tgtPos] = 0
                            attack[TOON_KBBONUS_COL][tgtPos] = -1

                    if allTargetsDead and atkTrack != lastTrack:
                        if self.notify.getDebug():
                            self.notify.debug('all targets of toon attack ' + str(currToonAttack) + ' are dead')
                        self.__clearAttack(currToonAttack, toon=1)
                        attack = self.battle.toonAttacks[currToonAttack]
                        atkTrack, atkLevel = self.__getActualTrackLevel(attack)
                damagesDone = self.__applyToonAttackDamages(currToonAttack)
                self.__applyToonAttackDamages(currToonAttack, hpbonus=1)
                if atkTrack != LURE and atkTrack != DROP and atkTrack != SOUND:
                    self.__applyToonAttackDamages(currToonAttack, kbbonus=1)
                if lastTrack != atkTrack:
                    lastAttacks = []
                    lastTrack = atkTrack
                lastAttacks.append(attack)
                if self.itemIsCredit(atkTrack, atkLevel):
                    if atkTrack == TRAP or atkTrack == LURE:
                        pass
                    elif atkTrack == HEAL:
                        if damagesDone != 0:
                            self.__addAttackExp(attack)
                    else:
                        self.__addAttackExp(attack)

        if self.trainTrapTriggered:
            for suit in self.battle.activeSuits:
                suitId = suit.doId
                self.__removeSuitTrap(suitId)
                suit.battleTrap = NO_TRAP
                self.notify.debug('train trap triggered, removing trap from %d' % suitId)

        if self.notify.getDebug():
            for currToonAttack in self.toonAtkOrder:
                attack = self.battle.toonAttacks[currToonAttack]
                self.notify.debug('Final Toon attack: ' + str(attack))

    def __allTargetsDead(self, attackIdx, toon=1):
        allTargetsDead = 1
        if toon:
            targets = self.__createToonTargetList(attackIdx)
            for currTgt in targets:
                if currTgt.getHp() > 0:
                    allTargetsDead = 0
                    break

        else:
            self.notify.warning('__allTargetsDead: suit ver. not implemented!')
        return allTargetsDead

    def __clearLuredSuitsByAttack(self, toonId, kbBonusReq = 0, targetId = -1):
        if self.notify.getDebug():
            self.notify.debug('__clearLuredSuitsByAttack')
        if targetId != -1 and self.__suitIsLured(t.getDoId()):
            self.__removeLured(t.getDoId())
        else:
            tgtList = self.__createToonTargetList(toonId)
            for t in tgtList:
                if self.__suitIsLured(t.getDoId()) and (not kbBonusReq or self.__bonusExists(t, hp=0)):
                    self.__removeLured(t.getDoId())
                    if self.notify.getDebug():
                        self.notify.debug('Suit %d stepping from lured spot' % t.getDoId())
                else:
                    self.notify.debug('Suit ' + str(t.getDoId()) + ' not found in currently lured suits')

    def __clearLuredSuitsDelayed(self):
        if self.notify.getDebug():
            self.notify.debug('__clearLuredSuitsDelayed')
        for t in self.delayedUnlures:
            if self.__suitIsLured(t):
                self.__removeLured(t)
                if self.notify.getDebug():
                    self.notify.debug('Suit %d stepping back from lured spot' % t)
            else:
                self.notify.debug('Suit ' + str(t) + ' not found in currently lured suits')

        self.delayedUnlures = []

    def __addLuredSuitsDelayed(self, toonId, targetId = -1, ignoreDamageCheck = False):
        if self.notify.getDebug():
            self.notify.debug('__addLuredSuitsDelayed')
        if targetId != -1:
            self.delayedUnlures.append(targetId)
        else:
            tgtList = self.__createToonTargetList(toonId)
            for t in tgtList:
                if self.__suitIsLured(t.getDoId()) and t.getDoId() not in self.delayedUnlures and (self.__attackDamageForTgt(self.battle.toonAttacks[toonId], self.battle.activeSuits.index(t), suit=0) > 0 or ignoreDamageCheck):
                    self.delayedUnlures.append(t.getDoId())

    def __calculateToonAttacks(self):
        self.notify.debug('__calculateToonAttacks()')
        self.__clearBonuses(hp=0)
        currTrack = None
        self.notify.debug('Traps: ' + str(self.traps))
        maxSuitLevel = 0
        for cog in self.battle.activeSuits:
            maxSuitLevel = max(maxSuitLevel, cog.getActualLevel())

        self.creditLevel = maxSuitLevel
        for toonId in self.toonAtkOrder:
            if self.__combatantDead(toonId, toon=1):
                if self.notify.getDebug():
                    self.notify.debug("Toon %d is dead and can't attack" % toonId)
                continue
            attack = self.battle.toonAttacks[toonId]
            atkTrack = self.__getActualTrack(attack)
            if atkTrack != NO_ATTACK and atkTrack != SOS and atkTrack != NPCSOS:
                if self.notify.getDebug():
                    self.notify.debug('Calculating attack for toon: %d' % toonId)
                if self.SUITS_UNLURED_IMMEDIATELY:
                    if currTrack and atkTrack != currTrack:
                        self.__clearLuredSuitsDelayed()
                currTrack = atkTrack
                self.__calcToonAtkHp(toonId)
                attackIdx = self.toonAtkOrder.index(toonId)
                self.__handleBonus(attackIdx, hp=0)
                self.__handleBonus(attackIdx, hp=1)
                lastAttack = self.toonAtkOrder.index(toonId) >= len(self.toonAtkOrder) - 1
                unlureAttack = self.__attackHasHit(attack, suit=0) and self.__unlureAtk(toonId, toon=1)
                if unlureAttack:
                    if lastAttack:
                        self.__clearLuredSuitsByAttack(toonId)
                    else:
                        self.__addLuredSuitsDelayed(toonId)
                if lastAttack:
                    self.__clearLuredSuitsDelayed()

        self.__processBonuses(hp=0)
        self.__processBonuses(hp=1)
        self.__postProcessToonAttacks()
        return

    def __knockBackAtk(self, attackIndex, toon=1):
        if toon and (self.battle.toonAttacks[attackIndex][TOON_TRACK_COL] == THROW or self.battle.toonAttacks[attackIndex][TOON_TRACK_COL] == SQUIRT):
            if self.notify.getDebug():
                self.notify.debug('attack is a knockback')
            return 1
        elif self.__getActualTrack(self.battle.toonAttacks[attackIndex]) in [THROW, SQUIRT]:
            return 1
        return 0

    def __unlureAtk(self, attackIndex, toon=1):
        attack = self.battle.toonAttacks[attackIndex]
        track = self.__getActualTrack(attack)
        if toon and (track == THROW or track == SQUIRT or track == SOUND):
            if self.notify.getDebug():
                self.notify.debug('attack is an unlure')
            return 1
        return 0

    def __calcSuitTarget(self, attackIndex):
        attack = self.battle.suitAttacks[attackIndex]
        suitId = attack[SUIT_ID_COL]
        if suitId in self.SuitAttackers and random.randint(0, 99) < 75:
            totalDamage = 0
            for currToon in self.SuitAttackers[suitId].keys():
                totalDamage += self.SuitAttackers[suitId][currToon]

            dmgs = []
            for currToon in self.SuitAttackers[suitId].keys():
                dmgs.append(self.SuitAttackers[suitId][currToon] / totalDamage * 100)

            dmgIdx = SuitBattleGlobals.pickFromFreqList(dmgs)
            if dmgIdx == None:
                toonId = self.__pickRandomToon(suitId)
            else:
                toonId = self.SuitAttackers[suitId].keys()[dmgIdx]
            if toonId == -1 or toonId not in self.battle.activeToons:
                return -1
            self.notify.debug('Suit attacking back at toon ' + str(toonId))
            return self.battle.activeToons.index(toonId)
        else:
            return self.__pickRandomToon(suitId)
        return

    def __pickRandomToon(self, suitId):
        liveToons = []
        for currToon in self.battle.activeToons:
            if not self.__combatantDead(currToon, toon=1):
                liveToons.append(self.battle.activeToons.index(currToon))

        if len(liveToons) == 0:
            self.notify.debug('No tgts avail. for suit ' + str(suitId))
            return -1
        chosen = random.choice(liveToons)
        self.notify.debug('Suit randomly attacking toon ' + str(self.battle.activeToons[chosen]))
        return chosen

    def __suitAtkHit(self, attackIndex):
        if self.suitsAlwaysHit:
            return 1
        else:
            if self.suitsAlwaysMiss:
                return 0
        theSuit = self.battle.activeSuits[attackIndex]
        atkType = self.battle.suitAttacks[attackIndex][SUIT_ATK_COL]
        atkInfo = SuitBattleGlobals.getSuitAttack(theSuit.dna.name, theSuit.getLevel(), atkType)
        atkAcc = atkInfo['acc']
        #suitAcc = SuitBattleGlobals.SuitAttributes[theSuit.dna.name]['acc'][theSuit.getLevel()]
        acc = atkAcc
        randChoice = random.randint(0, 99)
        if self.notify.getDebug():
            self.notify.debug('Suit attack rolled ' + str(randChoice) + ' to hit with an accuracy of ' + str(acc) + ' (attackAcc: ' + str(atkAcc) + ' suitAcc: N\\A')
        if randChoice < acc:
            return 1
        return 0

    def __suitAtkAffectsGroup(self, attack):
        atkType = attack[SUIT_ATK_COL]
        theSuit = self.battle.findSuit(attack[SUIT_ID_COL])
        atkInfo = SuitBattleGlobals.getSuitAttack(theSuit.dna.name, theSuit.getLevel(), atkType)
        return atkInfo['group'] != SuitBattleGlobals.ATK_TGT_SINGLE

    def __createSuitTargetList(self, attackIndex):
        attack = self.battle.suitAttacks[attackIndex]
        targetList = []
        if attack[SUIT_ATK_COL] == NO_ATTACK:
            self.notify.debug('No attack, no targets')
            return targetList
        debug = self.notify.getDebug()
        if not self.__suitAtkAffectsGroup(attack):
            targetList.append(self.battle.activeToons[attack[SUIT_TGT_COL]])
            if debug:
                self.notify.debug('Suit attack is single target')
        else:
            if debug:
                self.notify.debug('Suit attack is group target')
            for currToon in self.battle.activeToons:
                if debug:
                    self.notify.debug('Suit attack will target toon' + str(currToon))
                targetList.append(currToon)

        return targetList

    def __calcSuitAtkHp(self, attackIndex):
        targetList = self.__createSuitTargetList(attackIndex)
        attack = self.battle.suitAttacks[attackIndex]
        for currTarget in xrange(len(targetList)):
            toonId = targetList[currTarget]
            toon = self.battle.getToon(toonId)
            result = 0
            theSuit = self.battle.findSuit(attack[SUIT_ID_COL])
            atkType = attack[SUIT_ATK_COL]
            atkInfo = SuitBattleGlobals.getSuitAttack(theSuit.dna.name, theSuit.getLevel(), atkType)
            if toon and toon.immortalMode:
                result = 1
            elif self.TOONS_TAKE_NO_DAMAGE:
                result = 0
            elif self.__suitAtkHit(attackIndex):
                result = atkInfo['hp']
                if theSuit.getExecutive():
                    result = int(result * ToontownBattleGlobals.EXECUTIVE_DMG_MULT)
                if theSuit.getMaxSkeleRevives() > 0 and theSuit.getSkeleRevives() == 0: # if the suit WAS ALREADY V2, AND IS NOW A SKELECOG
                    result = int(result * ToontownBattleGlobals.V2_SKELECOG_DMG_MULT)
            targetIndex = self.battle.activeToons.index(toonId)
            if atkInfo['name'] == 'CompoundingInterest':
                attack[SUIT_HP_COL][targetIndex] = (12 + (self.TurnsElapsed * 3))
            elif atkInfo['name'] == 'Recarmdra':
                self.notify.debug('Recarmdra Cheat activated')
                attack[SUIT_HP_COL][targetIndex] = int(theSuit.currHP - 1)
                theSuit.setHP(1)
                managerTarget = None
                for suit in self.battle.suits:
                    if self.battle.findSuit(suit.doId).getManager():
                        managerTarget = suit
                        break
                managerTarget.setHP(managerTarget.getHP() + attack[SUIT_HP_COL][targetIndex])
            else:
                if atkInfo['name'] == 'Coalescence':
                    if toon.getHp() == 1:
                        attack[SUIT_HP_COL][targetIndex] = 1
                    else:
                        attack[SUIT_HP_COL][targetIndex] = toon.getHp() - 1
                    theSuit.setHP(int(theSuit.currHP + ToontownBattleGlobals.HUSTLER_COALESCENCE_HEAL_BASE + attack[SUIT_HP_COL][targetIndex] * ToontownBattleGlobals.HUSTLER_COALESCENCE_HEAL_AMP))    
                elif atkInfo['suitName'] == 'hst' and atkInfo['name'] == 'ShadowWave':
                    if self.toonHasCondition(toonId, 'corruption'):
                        attack[SUIT_HP_COL][targetIndex] = 7 + int(floor(self.getToonConditionModifier(toonId, 'corruption') / 4.0) * 7)
                    else:
                        attack[SUIT_HP_COL][targetIndex] = 7
                    theSuit.setHP(int(theSuit.currHP + attack[SUIT_HP_COL][targetIndex] * ToontownBattleGlobals.HUSTLER_SHADOW_WAVE_HEAL_AMP))
                elif self.toonHasCondition(toonId, 'corruption') and result > 0:
                    self.notify.debug('__calcSuitAtkHp - Target is Corrupt, dealing %i bonus damage' % self.getToonConditionModifier(toonId, 'corruption'))
                    attack[SUIT_HP_COL][targetIndex] = result + self.getToonConditionModifier(toonId, 'corruption')
                else:
                    self.notify.debug('__calcSuitAtkHp - Target is not corrupt, not doing any bonus here')
                    attack[SUIT_HP_COL][targetIndex] = result

    def __getToonHp(self, toonDoId):
        handle = self.battle.getToon(toonDoId)
        if handle != None and toonDoId in self.toonHPAdjusts:
            return handle.hp + self.toonHPAdjusts[toonDoId]
        else:
            return 0
        return

    def __getToonMaxHp(self, toonDoId):
        handle = self.battle.getToon(toonDoId)
        if handle != None:
            return handle.maxHp
        else:
            return 0
        return

    def __applySuitAttackDamages(self, attackIndex):
        attack = self.battle.suitAttacks[attackIndex]
        theSuit = self.battle.activeSuits[attackIndex]
        if self.APPLY_HEALTH_ADJUSTMENTS:
            for t in self.battle.activeToons:
                if self.TurnsElapsed % 3 == 0 and theSuit.dna.name == 'cmb' and self.__suitCanAttack(theSuit.doId) and not len(self.battle.activeSuits) < 2:
                    position = self.battle.activeToons.index(t)
                    damageToDeal = (12 + (self.TurnsElapsed * 3))
                    if damageToDeal <= 0:
                        continue
                    toonHp = self.__getToonHp(t)
                    if toonHp - damageToDeal <= 0:
                        if self.notify.getDebug():
                            self.notify.debug('Toon %d has died, removing' % t)
                        self.toonLeftBattle(t)
                        attack[TOON_DIED_COL] = attack[TOON_DIED_COL] | 1 << position
                    if self.notify.getDebug():
                        self.notify.debug('Toon ' + str(t) + ' takes ' + str(damageToDeal) + ' damage')
                    self.toonHPAdjusts[t] -= damageToDeal
                    self.notify.debug('Toon ' + str(t) + ' now has ' + str(self.__getToonHp(t)) + ' health')
                else:
                    position = self.battle.activeToons.index(t)
                    if attack[SUIT_HP_COL][position] <= 0:
                        continue
                    toonHp = self.__getToonHp(t)
                    if theSuit.dna.name == 'ssb':
                        if attack[SUIT_ATK_COL] in [0, 2]:
                            self.notify.debug('__applySuitAttackDamages - applying corruption on toon %s' % str(t))
                            self.setToonCondition(t, 'corruption', 2, -2, 'refreshTurns')
                            if attack[SUIT_ATK_COL] == 0:
                                self.notify.debug('__applySuitAttackDamages - applying corruption on toon %s two additional times' % str(t))
                                self.setToonCondition(t, 'corruption', 4, -2, 'refreshTurns')
                        else:
                            self.notify.debug('__applySuitAttackDamages - We are a shadow, but we did not use corruption, not corrupting.')
                            self.toonHPAdjusts[t] -= 0  # toons take no damage from this cheat
                            return
                    if theSuit.dna.name == 'hst' and attack[SUIT_ATK_COL] == 6:
                        self.notify.debug('__applySuitAttackDamages - applying corruption on toon %s four times' % str(t))
                        self.setToonCondition(t, 'corruption', 8, -2, 'refreshTurns')
                    if toonHp - attack[SUIT_HP_COL][position] <= 0:
                        if self.notify.getDebug():
                            self.notify.debug('Toon %d has died, removing' % t)
                        self.toonLeftBattle(t)
                        attack[TOON_DIED_COL] = attack[TOON_DIED_COL] | 1 << position
                    if self.notify.getDebug():
                        self.notify.debug('Toon ' + str(t) + ' takes ' + str(attack[SUIT_HP_COL][position]) + ' damage')
                        
                    self.toonHPAdjusts[t] -= attack[SUIT_HP_COL][position]
                    self.notify.debug('Toon ' + str(t) + ' now has ' + str(self.__getToonHp(t)) + ' health')

    def __suitCanAttack(self, suitId):
        if self.__combatantDead(suitId, toon=0) or self.__suitIsLured(suitId) or self.__combatantJustRevived(suitId):
            return 0
        return 1

    def __updateSuitAtkStat(self, toonId):
        if toonId in self.suitAtkStats:
            self.suitAtkStats[toonId] += 1
        else:
            self.suitAtkStats[toonId] = 1

    def __printSuitAtkStats(self):
        self.notify.debug('Suit Atk Stats:')
        for currTgt in self.suitAtkStats.keys():
            if currTgt not in self.battle.activeToons:
                continue
            tgtPos = self.battle.activeToons.index(currTgt)
            self.notify.debug('Toon ' + str(currTgt) + ' at position ' + str(tgtPos) + ' was attacked ' + str(self.suitAtkStats[currTgt]) + ' times')


    def __calculateSuitAttacks(self):
        for i in xrange(len(self.battle.suitAttacks)):
            if i < len(self.battle.activeSuits):
                suitId = self.battle.activeSuits[i].doId
                self.battle.suitAttacks[i][SUIT_ID_COL] = suitId
                if not self.__suitCanAttack(suitId):
                    if self.notify.getDebug():
                        self.notify.debug("Suit %d can't attack" % suitId)
                    continue
                if self.battle.pendingSuits.count(self.battle.activeSuits[i]) > 0 or self.battle.joiningSuits.count(self.battle.activeSuits[i]) > 0:
                    continue
                attack = self.battle.suitAttacks[i]
                attack[SUIT_ID_COL] = self.battle.activeSuits[i].doId
                attack[SUIT_ATK_COL] = self.__calcSuitAtkType(i)
                attack[SUIT_TGT_COL] = self.__calcSuitTarget(i)
                if attack[SUIT_TGT_COL] == -1:
                    self.battle.suitAttacks[i] = getDefaultSuitAttack()
                    attack = self.battle.suitAttacks[i]
                    self.notify.debug('clearing suit attack, no avail targets')
                self.__calcSuitAtkHp(i)
                if attack[SUIT_ATK_COL] != NO_ATTACK:
                    if self.__suitAtkAffectsGroup(attack):
                        for currTgt in self.battle.activeToons:
                            self.__updateSuitAtkStat(currTgt)

                    else:
                        tgtId = self.battle.activeToons[attack[SUIT_TGT_COL]]
                        self.__updateSuitAtkStat(tgtId)
                targets = self.__createSuitTargetList(i)
                allTargetsDead = 1
                for currTgt in targets:
                    if self.__getToonHp(currTgt) > 0:
                        allTargetsDead = 0
                        break

                if allTargetsDead:
                    self.battle.suitAttacks[i] = getDefaultSuitAttack()
                    if self.notify.getDebug():
                        self.notify.debug('clearing suit attack, targets dead')
                        self.notify.debug('suit attack is now ' + repr(self.battle.suitAttacks[i]))
                        self.notify.debug('all attacks: ' + repr(self.battle.suitAttacks))
                    attack = self.battle.suitAttacks[i]
                if self.__attackHasHit(attack, suit=1):
                    self.__applySuitAttackDamages(i)
                if self.notify.getDebug():
                    self.notify.debug('Suit attack: ' + str(self.battle.suitAttacks[i]))
                attack[SUIT_BEFORE_TOONS_COL] = 0

    def __updateLureTimeouts(self):
        if self.notify.getDebug():
            self.notify.debug('__updateLureTimeouts()')
            self.notify.debug('Lured suits: ' + str(self.currentlyLuredSuits))
        noLongerLured = []
        for currLuredSuit in self.currentlyLuredSuits.keys():
            self.__incLuredCurrRound(currLuredSuit)
            if self.__luredMaxRoundsReached(currLuredSuit) or self.__luredWakeupTime(currLuredSuit):
                noLongerLured.append(currLuredSuit)

        for currLuredSuit in noLongerLured:
            self.__removeLured(currLuredSuit)

        if self.notify.getDebug():
            self.notify.debug('Lured suits: ' + str(self.currentlyLuredSuits))

    def __initRound(self):
        if self.CLEAR_SUIT_ATTACKERS:
            self.SuitAttackers = {}
        self.toonAtkOrder = []
        attacks = findToonAttack(self.battle.activeToons, self.battle.toonAttacks, PETSOS)
        for atk in attacks:
            self.toonAtkOrder.append(atk[TOON_ID_COL])

        attacks = findToonAttack(self.battle.activeToons, self.battle.toonAttacks, FIRE)
        for atk in attacks:
            self.toonAtkOrder.append(atk[TOON_ID_COL])

        for track in xrange(HEAL, DROP + 1):
            attacks = findToonAttack(self.battle.activeToons, self.battle.toonAttacks, track)
            if track == TRAP:
                sortedTraps = []
                for atk in attacks:
                    if atk[TOON_TRACK_COL] == TRAP:
                        sortedTraps.append(atk)

                for atk in attacks:
                    if atk[TOON_TRACK_COL] == NPCSOS:
                        sortedTraps.append(atk)

                attacks = sortedTraps
            for atk in attacks:
                self.toonAtkOrder.append(atk[TOON_ID_COL])

        specials = findToonAttack(self.battle.activeToons, self.battle.toonAttacks, NPCSOS)
        toonsHit = 0
        cogsMiss = 0
        for special in specials:
            npc_track = NPCToons.getNPCTrack(special[TOON_TGT_COL])
            if npc_track == NPC_TOONS_HIT:
                BattleCalculatorAI.toonsAlwaysHit = 1
                toonsHit = 1
            elif npc_track == NPC_COGS_MISS:
                BattleCalculatorAI.suitsAlwaysMiss = 1
                cogsMiss = 1

        if self.notify.getDebug():
            self.notify.debug('Toon attack order: ' + str(self.toonAtkOrder))
            self.notify.debug('Active toons: ' + str(self.battle.activeToons))
            self.notify.debug('Toon attacks: ' + str(self.battle.toonAttacks))
            self.notify.debug('Active suits: ' + str(self.battle.activeSuits))
            self.notify.debug('Suit attacks: ' + str(self.battle.suitAttacks))
        self.toonHPAdjusts = {}
        for t in self.battle.activeToons:
            self.toonHPAdjusts[t] = 0

        self.__clearBonuses()
        self.__updateActiveToons()
        self.delayedUnlures = []
        self.__initTraps()
        self.successfulLures = {}
        return (
         toonsHit, cogsMiss)

    def calculateRound(self):
        longest = max(len(self.battle.activeToons), len(self.battle.activeSuits))
        for t in self.battle.activeToons:
            for j in xrange(longest):
                self.battle.toonAttacks[t][TOON_HP_COL].append(-1)
                self.battle.toonAttacks[t][TOON_KBBONUS_COL].append(-1)

        for i in xrange(4):
            for j in xrange(len(self.battle.activeToons)):
                self.battle.suitAttacks[i][SUIT_HP_COL].append(-1)

        toonsHit, cogsMiss = self.__initRound()
        for suit in self.battle.activeSuits:
            if suit.isGenerated():
                suit.b_setHP(suit.getHP())

        for suit in self.battle.activeSuits:
            if not hasattr(suit, 'dna'):
                self.notify.warning('a removed suit is in this battle!')
                return None

        self.__calculateToonAttacks()
        self.__updateLureTimeouts()
        self.__calculateSuitAttacks()
        if toonsHit == 1:
            BattleCalculatorAI.toonsAlwaysHit = 0
        if cogsMiss == 1:
            BattleCalculatorAI.suitsAlwaysMiss = 0
        if self.notify.getDebug():
            self.notify.debug('Toon skills gained after this round: ' + repr(self.toonSkillPtsGained))
            self.__printSuitAtkStats()
            self.decrementConditionTurns()
            if self.toonStatusConditions:
                self.printToonConditions()
            if self.suitStatusConditions:
                self.printSuitConditions()
        return None

    def __calculateFiredCogs():
        import pdb
        pdb.set_trace()

    def toonLeftBattle(self, toonId):
        if self.notify.getDebug():
            self.notify.debug('toonLeftBattle()' + str(toonId))
        if toonId in self.toonSkillPtsGained:
            del self.toonSkillPtsGained[toonId]
        if toonId in self.suitAtkStats:
            del self.suitAtkStats[toonId]
        if not self.CLEAR_SUIT_ATTACKERS:
            oldSuitIds = []
            for s in self.SuitAttackers.keys():
                if toonId in self.SuitAttackers[s]:
                    del self.SuitAttackers[s][toonId]
                    if len(self.SuitAttackers[s]) == 0:
                        oldSuitIds.append(s)

            for oldSuitId in oldSuitIds:
                del self.SuitAttackers[oldSuitId]

        self.__clearTrapCreator(toonId)
        self.__clearLurer(toonId)

    def suitLeftBattle(self, suitId):
        if self.notify.getDebug():
            self.notify.debug('suitLeftBattle(): ' + str(suitId))
        self.__removeLured(suitId)
        if suitId in self.SuitAttackers:
            del self.SuitAttackers[suitId]
        self.__removeSuitTrap(suitId)

    def __updateActiveToons(self):
        if self.notify.getDebug():
            self.notify.debug('updateActiveToons()')
        if not self.CLEAR_SUIT_ATTACKERS:
            oldSuitIds = []
            for s in self.SuitAttackers.keys():
                for t in self.SuitAttackers[s].keys():
                    if t not in self.battle.activeToons:
                        del self.SuitAttackers[s][t]
                        if len(self.SuitAttackers[s]) == 0:
                            oldSuitIds.append(s)

            for oldSuitId in oldSuitIds:
                del self.SuitAttackers[oldSuitId]

        for trap in self.traps.keys():
            if self.traps[trap][1] not in self.battle.activeToons:
                self.notify.debug('Trap for toon ' + str(self.traps[trap][1]) + ' will no longer give exp')
                self.traps[trap][1] = 0

    def getSkillGained(self, toonId, track):
        return BattleExperienceAI.getSkillGained(self.toonSkillPtsGained, toonId, track)

    def getLuredSuits(self):
        self.TurnsElapsed += 1
        self.notify.debug('Current Elapsed Turns: ' + str(self.TurnsElapsed))
        if len(self.battle.activeSuits) <= 2:
            self.TurnsSinceSummonWithOnlyOneCog += 1
        self.TurnsSinceSummon += 1
        self.notify.debug('Current Elapsed Turns Since Summon (Any): ' + str(self.TurnsSinceSummon))
        self.notify.debug('Current Elapsed Turns Since Summon (With One Cog): ' + str(self.TurnsSinceSummonWithOnlyOneCog))
        luredSuits = self.currentlyLuredSuits.keys()
        self.notify.debug('Lured suits reported to battle: ' + repr(luredSuits))
        return luredSuits

    def __suitIsLured(self, suitId, prevRound=0):
        inList = suitId in self.currentlyLuredSuits
        if prevRound:
            return inList and self.currentlyLuredSuits[suitId][0] != -1
        return inList

    def __findAvailLureId(self, lurerId):
        luredSuits = self.currentlyLuredSuits.keys()
        lureIds = []
        for currLured in luredSuits:
            lurerInfo = self.currentlyLuredSuits[currLured][3]
            lurers = lurerInfo.keys()
            for currLurer in lurers:
                currId = lurerInfo[currLurer][1]
                if currLurer == lurerId and currId not in lureIds:
                    lureIds.append(currId)

        lureIds.sort()
        currId = 1
        for currLureId in lureIds:
            if currLureId != currId:
                return currId
            currId += 1

        return currId

    def __addLuredSuitInfo(self, suitId, currRounds, maxRounds, wakeChance, lurer, lureLvl, lureId=-1, npc=0):
        if lureId == -1:
            availLureId = self.__findAvailLureId(lurer)
        else:
            availLureId = lureId
        if npc == 1:
            credit = 0
        else:
            credit = self.itemIsCredit(LURE, lureLvl)
        if suitId in self.currentlyLuredSuits:
            lureInfo = self.currentlyLuredSuits[suitId]
            if lurer not in lureInfo[3]:
                lureInfo[1] += maxRounds
                if wakeChance < lureInfo[2]:
                    lureInfo[2] = wakeChance
                lureInfo[3][lurer] = [
                 lureLvl, availLureId, credit]
        else:
            lurerInfo = {lurer: [lureLvl, availLureId, credit]}
            self.currentlyLuredSuits[suitId] = [
             currRounds, maxRounds, wakeChance, lurerInfo]
        self.notify.debug('__addLuredSuitInfo: currLuredSuits -> %s' % repr(self.currentlyLuredSuits))
        return availLureId

    def __getLurers(self, suitId):
        if self.__suitIsLured(suitId):
            return self.currentlyLuredSuits[suitId][3].keys()
        return []

    def __getLuredExpInfo(self, suitId):
        returnInfo = []
        lurers = self.__getLurers(suitId)
        if len(lurers) == 0:
            return returnInfo
        lurerInfo = self.currentlyLuredSuits[suitId][3]
        for currLurer in lurers:
            returnInfo.append([currLurer, lurerInfo[currLurer][0], lurerInfo[currLurer][1], lurerInfo[currLurer][2]])

        return returnInfo

    def __clearLurer(self, lurerId, lureId=-1):
        luredSuits = self.currentlyLuredSuits.keys()
        for currLured in luredSuits:
            lurerInfo = self.currentlyLuredSuits[currLured][3]
            lurers = lurerInfo.keys()
            for currLurer in lurers:
                if currLurer == lurerId and (lureId == -1 or lureId == lurerInfo[currLurer][1]):
                    del lurerInfo[currLurer]

    def __setLuredMaxRounds(self, suitId, rounds):
        if self.__suitIsLured(suitId):
            self.currentlyLuredSuits[suitId][1] = rounds

    def __setLuredWakeChance(self, suitId, chance):
        if self.__suitIsLured(suitId):
            self.currentlyLuredSuits[suitId][2] = chance

    def __incLuredCurrRound(self, suitId):
        if self.battle.findSuit(suitId).getManager() and self.currentlyLuredSuits[suitId][0] < 1:   # sets manager lure resistance to 2 rounds
            self.currentlyLuredSuits[suitId][0] = self.currentlyLuredSuits[suitId][1] - 2
        if self.__suitIsLured(suitId):
            self.currentlyLuredSuits[suitId][0] += 1

    def __removeLured(self, suitId):
        if self.__suitIsLured(suitId):
            del self.currentlyLuredSuits[suitId]

    def __luredMaxRoundsReached(self, suitId):
        return self.__suitIsLured(suitId) and self.currentlyLuredSuits[suitId][0] >= self.currentlyLuredSuits[suitId][1]

    def __luredWakeupTime(self, suitId):
        return self.__suitIsLured(suitId) and self.currentlyLuredSuits[suitId][0] > 0 and random.randint(0, 99) < self.currentlyLuredSuits[suitId][2]

    def itemIsCredit(self, track, level):
        if track == PETSOS:
            return 0
        return level < self.creditLevel

    def __getActualTrack(self, toonAttack):
        if toonAttack[TOON_TRACK_COL] == NPCSOS:
            track = NPCToons.getNPCTrack(toonAttack[TOON_TGT_COL])
            if track != None:
                return track
            else:
                self.notify.warning('No NPC with id: %d' % toonAttack[TOON_TGT_COL])
        return toonAttack[TOON_TRACK_COL]

    def __getActualTrackLevel(self, toonAttack):
        if toonAttack[TOON_TRACK_COL] == NPCSOS:
            track, level, hp = NPCToons.getNPCTrackLevelHp(toonAttack[TOON_TGT_COL])
            if track != None:
                return (track, level)
            else:
                self.notify.warning('No NPC with id: %d' % toonAttack[TOON_TGT_COL])
        return (
         toonAttack[TOON_TRACK_COL], toonAttack[TOON_LVL_COL])

    def __getActualTrackLevelHp(self, toonAttack):
        if toonAttack[TOON_TRACK_COL] == NPCSOS:
            track, level, hp = NPCToons.getNPCTrackLevelHp(toonAttack[TOON_TGT_COL])
            if track != None:
                return (track, level, hp)
            else:
                self.notify.warning('No NPC with id: %d' % toonAttack[TOON_TGT_COL])
        else:
            if toonAttack[TOON_TRACK_COL] == PETSOS:
                trick = toonAttack[TOON_LVL_COL]
                petProxyId = toonAttack[TOON_TGT_COL]
                trickId = toonAttack[TOON_LVL_COL]
                healRange = PetTricks.TrickHeals[trickId]
                hp = 0
                if petProxyId in simbase.air.doId2do:
                    petProxy = simbase.air.doId2do[petProxyId]
                    if trickId < len(petProxy.trickAptitudes):
                        aptitude = petProxy.trickAptitudes[trickId]
                        hp = int(lerp(healRange[0], healRange[1], aptitude))
                else:
                    self.notify.warning('pet proxy: %d not in doId2do!' % petProxyId)
                return (toonAttack[TOON_TRACK_COL], toonAttack[TOON_LVL_COL], hp)
        return (
         toonAttack[TOON_TRACK_COL], toonAttack[TOON_LVL_COL], 0)

    def __calculatePetTrickSuccess(self, toonAttack):
        petProxyId = toonAttack[TOON_TGT_COL]
        if petProxyId not in simbase.air.doId2do:
            self.notify.warning('pet proxy %d not in doId2do!' % petProxyId)
            toonAttack[TOON_ACCBONUS_COL] = 1
            return (0, 0)
        petProxy = simbase.air.doId2do[petProxyId]
        trickId = toonAttack[TOON_LVL_COL]
        toonAttack[TOON_ACCBONUS_COL] = petProxy.attemptBattleTrick(trickId)
        if toonAttack[TOON_ACCBONUS_COL] == 1:
            return (0, 0)
        else:
            return (1, 100)

    def __calcSuitAtkType(self, attackIndex):
        theSuit = self.battle.activeSuits[attackIndex]
        if theSuit.dna.name == 'cmb':
            from toontown.suit.DistributedCashbotBossMiniAI import DistributedCashbotBossMiniAI

            boss = None
            for do in simbase.air.doId2do.values():
                if isinstance(do, DistributedCashbotBossMiniAI):
                    for toon in self.battle.activeToons:
                        if toon in do.involvedToons:
                            boss = do
                            break

            if (len(self.battle.activeSuits) < 2 or self.TurnsSinceSummonWithOnlyOneCog > 2) and boss is not None:
                if self.TurnsSinceSummonWithOnlyOneCog > 2:
                    self.notify.debug("THIS MF TOON BEEN STALLING!!!!!!!, SUMMON MORE!!!!!!!!!!!!!!!!!!!!!!!")
                else:
                    boss.appendSuitsToBattle(boss.battleNumber, 'cmb', None)
                    self.notify.debug("Less than 2 Cogs, SUMMON MORE!!!!!!!!!!!!!!!!!!!!!!!")
                self.TurnsSinceSummonWithOnlyOneCog = 0

                boss.appendSuitsToBattle(boss.battleNumber, 'cmb', None)  
                boss.appendSuitsToBattle(boss.battleNumber, 'cmb', None)
                self.TurnsSinceSummon = 0
                return 4
            elif self.TurnsElapsed % 3 == 0:
                self.notify.debug("TURN IS MULTIPLE OF 3 (and we have suits), INCReASE THE POWAHHHHHHHHHHHH!!!!!!!!!!!!!!!!!!!!!!!")
                return 5
            elif 4 > len(self.currentlyLuredSuits) >= 2:
                self.notify.debug("THERE ARE TWO OR MORE LURED SUITS, and we are not using court fees, SO UNLURE THOSE MFS")
                for suit in self.currentlyLuredSuits.keys(): # this wouldn't work in python 3 :)
                    self.__removeLured(suit)
                return 6

        if theSuit.dna.name == 'hst':
            from toontown.suit.DistributedSellbotBossMiniAI import DistributedSellbotBossMiniAI

            boss = None
            for do in simbase.air.doId2do.values():
                if isinstance(do, DistributedSellbotBossMiniAI):
                    for toon in self.battle.activeToons:
                        if toon in do.involvedToons:
                            boss = do
                            break

            if self.TurnsSinceSummon > 3:
                self.TurnsSinceSummon = 0
                self.TurnsSinceSummonWithOnlyOneCog = 0
                return 7

            if self.TurnsSinceSummon > 2 and random.randint(0, 99) < 60:
                self.TurnsSinceSummon = 0
                self.TurnsSinceSummonWithOnlyOneCog = 0
                if boss is None:
                    return 6
                for i in range(0, 4 - len(self.battle.activeSuits)):
                    boss.appendSuitsToBattle(boss.battleNumber, 'hst2', self.numShadowsSummoned)
                    self.numShadowsSummoned += 1
                return 6

            if (len(self.battle.activeSuits) < 2 or self.TurnsSinceSummonWithOnlyOneCog > 2) and boss is not None:
                if self.TurnsSinceSummonWithOnlyOneCog > 2:
                    self.notify.debug("THIS MF TOON BEEN STALLING!!!!!!!, SUMMON MORE!!!!!!!!!!!!!!!!!!!!!!!")
                else:
                    self.notify.debug("Less than 2 Cogs, SUMMON MORE!!!!!!!!!!!!!!!!!!!!!!!")
                    boss.appendSuitsToBattle(boss.battleNumber, 'hst2', self.numShadowsSummoned)
                    self.numShadowsSummoned += 1
                theSuit.setHP(theSuit.currHP + 2500)    
                self.TurnsSinceSummonWithOnlyOneCog = 0
                self.TurnsSinceSummon = 0
                for i in range(2):
                    r = random.randint(1, 2)
                    boss.appendSuitsToBattle(boss.battleNumber, 'hst%i' % r, None if r == 1 else self.numShadowsSummoned)
                    if r == 2:
                        self.numShadowsSummoned += 1
                return 5

        if theSuit.dna.name == 'ssb':
            currentBossHealth = -1
            for s in self.battle.suits:
                if s.dna.name == 'hst':
                    currentBossHealth = s.currHP
            if currentBossHealth == -1:
                self.notify.warning('No manager found?')
                return random.choice([0, 2])
            if theSuit.getHP() == 1:
                return random.choice([0, 2])
            baseChance = 5.0
            roll = random.randint(0, 99)
            self.notify.debug('****************************************************')
            self.notify.debug('Building Recarmdra Cheat Roll:')
            self.notify.debug('Base Chance Inf.:\t%f\t\t->\t\t%f' % (baseChance, baseChance))
            self.notify.debug('Self HP Influence:\t(%i / 800) * 20\t\t->\t%f' % (theSuit.getHP(), (theSuit.getHP() / 800.0) * 40))
            self.notify.debug('Boss Manager HP Inf.:\t(5000 / %i) * %f * 2\t->\t%f' % (currentBossHealth, baseChance * 2, ((5000.0 / currentBossHealth) * baseChance * 2)))
            rollAgainst = baseChance + ((theSuit.getHP() / 800.0) * 40) + ((5000.0 / currentBossHealth) * baseChance * 2)
            self.notify.debug('Total Chance: %f' % rollAgainst)
            self.notify.debug('Roll this time: %i' % roll)
            if roll < rollAgainst:
                self.notify.debug('Success, choosing Recarmdra')
                self.notify.debug('****************************************************')
                return 1
            self.notify.debug('Roll failed, choosing Corruption')
            self.notify.debug('****************************************************')

        attacks = SuitBattleGlobals.SuitAttributes[theSuit.dna.name]['attacks']
        atk = SuitBattleGlobals.pickSuitAttack(attacks, theSuit.getLevel())
        return atk