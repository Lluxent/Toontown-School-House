from BattleBase import *
import random
from direct.directnotify import DirectNotifyGlobal
from otp.otpbase import OTPLocalizer
from toontown.toonbase import TTLocalizer
notify = DirectNotifyGlobal.directNotify.newCategory('SuitBattleGlobals')
debugAttackSequence = {}

def pickFromFreqList(freqList):
    randNum = random.randint(0, 99)
    count = 0
    index = 0
    level = None
    for f in freqList:
        count = count + f
        if randNum < count:
            level = index
            break
        index = index + 1

    return level


def getActualFromRelativeLevel(name, relLevel):
    data = SuitAttributes[name]
    actualLevel = data['level'] + relLevel
    if actualLevel > data['level'] + len(data['hp']):
        actualLevel = len(data['hp']) - 1
    return actualLevel


def getSuitVitals(name, level = -1):
    data = SuitAttributes[name]
    if level == -1:
        level = pickFromFreqList(data['freq'])
    dict = {}
    dict['level'] = getActualFromRelativeLevel(name, level)
    if dict['level'] == 11:
        level = 0
    dict['hp'] = data['hp'][level]
    dict['def'] = data['def'][level]
    attacks = data['attacks']
    alist = []
    for a in attacks:
        adict = {}
        name = a[0]
        adict['name'] = name
        adict['animName'] = SuitAttacks[name][0]
        adict['hp'] = a[1][level]
        adict['acc'] = a[2][level]
        adict['freq'] = a[3][level]
        adict['group'] = SuitAttacks[name][1]
        alist.append(adict)

    dict['attacks'] = alist
    return dict


def pickSuitAttack(attacks, suitLevel):
    attackNum = None
    randNum = random.randint(0, 99)
    notify.debug('pickSuitAttack: rolled %d' % randNum)
    count = 0
    index = 0
    total = 0
    for c in attacks:
        attackIndexLen = len(c[3])
        if attackIndexLen == 1:
            suitLevel = 0
        total = total + c[3][suitLevel]

    for c in attacks:
        count = count + c[3][suitLevel]
        if randNum < count:
            attackNum = index
            notify.debug('picking attack %d' % attackNum)
            break
        index = index + 1

    configAttackName = simbase.config.GetString('attack-type', 'random')
    if configAttackName == 'random':
        return attackNum
    elif configAttackName == 'sequence':
        for i in xrange(len(attacks)):
            if attacks[i] not in debugAttackSequence:
                debugAttackSequence[attacks[i]] = 1
                return i

        return attackNum
    else:
        for i in xrange(len(attacks)):
            if attacks[i][0] == configAttackName:
                return i

        return attackNum
    return


def getSuitAttack(suitName, suitLevel, attackNum = -1):
    attackChoices = SuitAttributes[suitName]['attacks']
    if attackNum == -1:
        notify.debug('getSuitAttack: picking attacking for %s' % suitName)
        attackNum = pickSuitAttack(attackChoices, suitLevel)
    attack = attackChoices[attackNum]
    adict = {}
    adict['suitName'] = suitName
    name = attack[0]
    adict['name'] = name
    adict['id'] = SuitAttacks.keys().index(name)
    adict['animName'] = SuitAttacks[name][0]
    if len(attack[1]) == 1:
        suitLevel = 0
    adict['hp'] = attack[1][suitLevel]
    adict['acc'] = attack[2][suitLevel]
    adict['freq'] = attack[3][suitLevel]
    adict['group'] = SuitAttacks[name][1]
    return adict

SuitDefaultHealth = lambda level: int((level + 1) * (level + 2))

def SuitDefaultHPDict(minLevel, maxLevel):
    t = []
    for lv in range(minLevel, maxLevel + 1):
        t.append(SuitDefaultHealth(lv))
    return tuple(t)

SuitDefaultDefense = (2, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60)

def SuitDefaultDefDict(minLevel, maxLevel):
    t = []
    for lv in range(minLevel, maxLevel + 1):
        if lv >= 14:
            t.append(65)
        else:
            t.append(SuitDefaultDefense[lv - 1])
    return tuple(t)

SuitShadowHealth = lambda level: int(108 + (level * 72))

def SuitShadowHPDict(minLevel, maxLevel):
    t = []
    for lv in range(minLevel, maxLevel + 1):
        t.append(SuitShadowHealth(lv))
    return tuple(t)

SpecialCogDict = ('cmb','ssb','hst','ren')

# re-formatted by me :)
SuitAttributes = {
    'f': {
        'name':         TTLocalizer.SuitFlunky,     # cog name
        'singularname': TTLocalizer.SuitFlunkyS,    # cogs singular name, for tasks
        'pluralname':   TTLocalizer.SuitFlunkyP,    # cogs plural name, for tasks
        'level': 0,                         # level the cog starts at (level - 1)
        'hp':   SuitDefaultHPDict(1, 5),    # cogs hp (more numbers, more levels)
        'def':  SuitDefaultDefDict(1, 5),             # cogs defence (more numbers, more levels)
        'freq': (50,30,10,5,5),             # cogs level frequency
        'acc':  (35,40,45,50,55),           # cogs accuracy (more numbers, more levels)
        'attacks':  
                (('PoundKey',
                    (2, 2, 3, 4, 6),        # attack damage
                    (75, 75, 80, 80, 90),   # attack accuracy
                    (30, 35, 40, 45, 50)),  # move frequency (all move frequency of each attack must add up to 100, for example 30,10,60 from level 1 of each attack)
                ('Shred',
                    (3, 4, 5, 6, 7),
                    (50, 55, 60, 65, 70),
                    (10, 15, 20, 25, 30)),
                ('ClipOnTie',
                    (1, 1, 2, 2, 3),
                    (75, 80, 85, 90, 95),
                    (60, 50, 40, 30, 20)))},
 'p': {'name':          TTLocalizer.SuitPencilPusher,
       'singularname':  TTLocalizer.SuitPencilPusherS,
       'pluralname':    TTLocalizer.SuitPencilPusherP,
       'level': 1,
       'hp':    SuitDefaultHPDict(2, 6),
       'def':   SuitDefaultDefDict(2, 6),
       'freq':  (50,30,10,5,5),
       'acc':   (45,50,55,60,65),
       'attacks':
                (('FountainPen',
                    (2, 3, 4, 6, 9),
                    (75, 75, 75, 75, 75),
                    (20, 20, 20, 20, 20)),
                ('RubOut',
                    (4, 5, 6, 8, 12),
                    (75, 75, 75, 75, 75),
                    (20, 20, 20, 20, 20)),
                ('FingerWag',
                    (1, 2, 2, 3, 4),
                    (75, 75, 75, 75, 75),
                    (35, 30, 25, 20, 15)),
                ('WriteOff',
                    (4, 6, 8, 10, 12),
                    (75, 75, 75, 75, 75),
                    (5, 10, 15, 20, 25)),
                ('FillWithLead',
                    (3, 4, 5, 6, 7),
                    (75, 75, 75, 75, 75),
                    (20, 20, 20, 20, 20)))},
 'ym': {'name':         TTLocalizer.SuitYesman,
        'singularname': TTLocalizer.SuitYesmanS,
        'pluralname':   TTLocalizer.SuitYesmanP,
        'level': 2,
        'hp':   SuitDefaultHPDict(3, 7),
        'def':  SuitDefaultDefDict(3, 7),
        'freq': (50,30,10,5,5),
        'acc':  (65,70,75,80,85),
        'attacks':
                (('RubberStamp',
                    (2, 4, 6, 8, 10),
                    (75,75,75,75,75),
                    (35,35,35,35,35)),
                ('RazzleDazzle',
                    (7, 9, 11, 13, 15),
                    (50,50,50,50,50),
                    (25,20,15,10,5)),
                ('Synergy',
                    (4, 6, 8, 10, 12),
                    (50,60,70,80,90),
                    (5,10,15,20,25)),
                ('TeeOff',
                    (5, 7, 9, 11, 13),
                    (50,60,70,80,90),
                    (35,35,35,35,35)))},
 'mm': {'name':         TTLocalizer.SuitMicromanager,
        'singularname': TTLocalizer.SuitMicromanagerS,
        'pluralname':   TTLocalizer.SuitMicromanagerP,
        'level': 3,
        'hp':   SuitDefaultHPDict(4, 8),
        'def':  SuitDefaultDefDict(4, 8),
        'freq': (50,30,10,5,5),
        'acc':  (70,75,80,82,85),
        'attacks':
                (('Demotion',
                    (6,8,12,15,18),
                    (50,60,70,80,90),
                    (30,30,30,30,30)),
                ('FingerWag',
                    (4,6,9,12,15),
                    (50,60,70,80,90),
                    (10,10,10,10,10)),
                ('FountainPen',
                    (3,4,6,8,10),
                    (50,60,70,80,90),
                    (15,15,15,15,15)),
                ('BrainStorm',
                    (4,6,9,12,15),
                    (50,55,65,75,85),
                    (25,25,25,25,25)),
                ('BuzzWord',
                    (4,6,9,12,15),
                    (50,60,70,80,90),
                    (20,20,20,20,20)))},
 'ds': {'name':         TTLocalizer.SuitDownsizer,
        'singularname': TTLocalizer.SuitDownsizerS,
        'pluralname':   TTLocalizer.SuitDownsizerP,
        'level': 4,
        'hp':   SuitDefaultHPDict(5, 9),
        'def':  SuitDefaultDefDict(5, 9),
        'freq': (50,30,10,5,5),
        'acc':  (35,40,45,50,55),
        'attacks':
                (('Canned',
                    (6, 8, 9, 11, 13),
                    (60,75,80,85,90),
                    (25,25,25,25,25)),
                ('Downsize',
                    (10, 13, 15, 18, 20),
                    (50,65,70,75,80),
                    (35,35,35,35,35)),
                ('PinkSlip',
                    (9, 10, 11, 12, 13),
                    (60,65,75,80,85),
                    (25,25,25,25,25)),
                ('Sacked',
                    (5, 7, 9, 12, 14),
                    (50,50,50,50,50),
                    (15,15,15,15,15)))},
 'hh': {'name':         TTLocalizer.SuitHeadHunter,
        'singularname': TTLocalizer.SuitHeadHunterS,
        'pluralname':   TTLocalizer.SuitHeadHunterP,
        'level': 5,
        'hp':   SuitDefaultHPDict(6, 12),
        'def':  SuitDefaultDefDict(6, 12),
        'freq': (50,30,10,5,5,0,0),
        'acc':  (35,40,45,50,55,60,65),
        'attacks':
                (('FountainPen',
                    (5, 6, 8, 10, 12, 14, 16),
                    (60, 75, 80, 85, 90, 95, 95),
                    (15, 15, 15, 15, 15, 15, 15)),
                ('GlowerPower',
                    (7, 8, 10, 12, 14, 16, 18),
                    (50, 60, 70, 80, 90, 95, 95),
                    (20, 20, 20, 20, 20, 20, 20)),
                ('HalfWindsor',
                    (8, 10, 12, 14, 16, 18, 20),
                    (60, 65, 70, 75, 80, 85, 90),
                    (20, 20, 20, 20, 20, 20, 20)),
                ('HeadShrink',
                    (10, 12, 15, 18, 21, 22, 24),
                    (65, 75, 80, 85, 95, 95, 95),
                    (25, 25, 25, 25, 25, 25, 25)),
                ('Rolodex',
                    (6, 7, 8, 9, 10, 11, 12),
                    (60, 65, 70, 75, 80, 85, 90),
                    (20, 20, 20, 20, 20, 20, 20)))},
 'cr': {'name':         TTLocalizer.SuitCorporateRaider,
        'singularname': TTLocalizer.SuitCorporateRaiderS,
        'pluralname':   TTLocalizer.SuitCorporateRaiderP,
        'level': 6,
        'hp':   SuitDefaultHPDict(7, 15),
        'def':  SuitDefaultDefDict(7, 15),
        'freq': (50,30,10,5,5,0,0,0,0),
        'acc':  (35,40,45,50,55,60,65,70,75),
        'attacks':
            (('Canned',
                    (6, 7, 8, 9, 10, 11, 12, 13, 14),
                    (60, 75, 80, 85, 90, 95, 95, 95, 95),
                    (20, 20, 20, 20, 20, 20, 20, 20, 20)),
            ('EvilEye',
                    (12, 15, 18, 21, 24, 26, 28, 30, 32),
                    (60, 70, 75, 80, 90, 95, 95, 95, 95),
                    (20, 20, 20, 20, 20, 20, 20, 20, 20)),
            ('PickPocket',
                    (9, 12, 13, 14, 15, 17, 18, 20, 22),
                    (55, 65, 75, 85, 95, 95, 95, 95, 95),
                    (20, 20, 20, 20, 20, 20, 20, 20, 20)),
            ('PlayHardball',
                    (7, 8, 12, 15, 16, 18, 20, 22, 24),
                    (60, 65, 70, 75, 80, 85, 90, 95, 95),
                    (20, 20, 20, 20, 20, 20, 20, 20, 20)),
            ('PowerTie',
                    (10, 12, 14, 16, 18, 20, 22, 24, 26),
                    (65, 75, 80, 85, 95, 95, 95, 95, 95),
                    (20, 20, 20, 20, 20, 20, 20, 20, 20)))},
 'tbc': {'name':            TTLocalizer.SuitTheBigCheese,
         'singularname':    TTLocalizer.SuitTheBigCheeseS,
         'pluralname':      TTLocalizer.SuitTheBigCheeseP,
         'level': 7,
         'hp':      SuitDefaultHPDict(8, 50),
         'def':     SuitDefaultDefDict(8, 50),
         'freq':    (50,30,10,5,5),
         'acc':     (35,40,45,50,55),
         'attacks':
                (('CigarSmoke',
                    (10, 12, 15, 18, 20, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61),
                    (55, 65, 70, 75, 80, 85, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90),
                    (25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25)),
                ('PowerTrip',
                    (14, 15, 17, 19, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59),
                    (60, 65, 70, 75, 80, 85, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90),
                    (25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25)),
                ('GlowerPower',
                    (10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 50, 51, 52, 53, 54, 55, 56),
                    (55, 65, 70, 75, 85, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90),
                    (20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20)),
                ('TeeOff',
                    (8,  11, 14, 17, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58),
                    (55, 65, 70, 75, 80, 85, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90),
                    (30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30)))},
 'cc': {'name':         TTLocalizer.SuitColdCaller,
        'singularname': TTLocalizer.SuitColdCallerS,
        'pluralname':   TTLocalizer.SuitColdCallerP,
        'level': 0,
        'hp':   SuitDefaultHPDict(1, 5),
        'def':  SuitDefaultDefDict(1, 5),
        'freq': (50,30,10,5,5),
        'acc':  (35,40,45,50,55),
        'attacks':
                (('FreezeAssets',
                    (3,4,6,8,10),
                    (50,50,50,50,50),
                    (5,10,15,20,25)),
                ('PoundKey',
                    (2,2,3,4,5),
                    (75,80,85,90,95),
                    (25,25,25,25,25)),
                ('MumboJumbo',
                    (2,3,4,6,8),
                    (50,55,60,65,70),
                    (25,25,25,25,25)),
                ('HotAir',
                    (1,1,1,1,1),
                    (90,90,90,90,90),
                    (45,40,35,30,25)))},
 'tm': {'name':         TTLocalizer.SuitTelemarketer,
        'singularname': TTLocalizer.SuitTelemarketerS,
        'pluralname':   TTLocalizer.SuitTelemarketerP,
        'level': 1,
        'hp':   SuitDefaultHPDict(2, 6),
        'def':  SuitDefaultDefDict(2, 6),
        'freq': (50,30,10,5,5),
        'acc':  (45,50,55,60,65),
        'attacks':
                (('ClipOnTie',
                    (2,2,3,3,4),
                    (75,75,75,75,75),
                    (20,20,20,20,20)),
                ('FingerWag',
                    (4,5,7,9,10),
                    (60,65,70,75,80),
                    (20,20,20,20,20)),
                ('Rolodex',
                    (4,6,7,9,12),
                    (50,50,50,50,50),
                    (20,20,20,20,20)),
                ('PoundKey',
                    (3,4,5,6,7),
                    (55,65,70,75,80),
                    (20,20,20,20,20)),                    
                ('MumboJumbo',
                    (4,6,7,9,12),
                    (75,80,85,90,95),
                    (20,20,20,20,20)))},
 'nd': {'name':         TTLocalizer.SuitNameDropper,
        'singularname': TTLocalizer.SuitNameDropperS,
        'pluralname':   TTLocalizer.SuitNameDropperP,
        'level': 2,
        'hp':   SuitDefaultHPDict(3, 7),
        'def':  SuitDefaultDefDict(3, 7),
        'freq': (50,30,10,5,5),
        'acc':  (65,70,75,80,85),
        'attacks':
                (('RazzleDazzle',
                    (4,5,6,9,12),
                    (75,80,85,90,95),
                    (30,30,30,30,30)),
                ('Rolodex',
                    (5,6,7,10,14),
                    (95,95,95,95,95),
                    (40,40,40,40,40)),
                ('Synergy',
                    (3,4,6,9,12),
                    (50,50,50,50,50),
                    (15,15,15,15,15)),
                ('PickPocket',
                    (2,2,2,2,2),
                    (95,95,95,95,95),
                    (15,15,15,15,15)))},
 'gh': {'name': TTLocalizer.SuitGladHander,
        'singularname': TTLocalizer.SuitGladHanderS,
        'pluralname': TTLocalizer.SuitGladHanderP,
        'level': 3,
        'hp':   SuitDefaultHPDict(4, 8),
        'def':  SuitDefaultDefDict(4, 8),
        'freq': (50,30,10,5,5),
        'acc':  (70,75,80,82,85),
        'attacks':
                (('RubberStamp',
                    (4,3,2,1,1),
                    (90,70,50,30,10),
                    (40,30,20,10,5)),
                ('FountainPen',
                    (3,3,2,1,1),
                    (70,60,50,40,30),
                    (40,30,20,10,5)),
                ('Filibuster',
                    (4,6,9,12,15),
                    (30,40,50,60,70),
                    (10,20,30,40,45)),
                ('Schmooze',
                    (5,7,11,15,20),
                    (55,65,75,85,95),
                    (10,20,30,40,45)))},
 'ms': {'name':         TTLocalizer.SuitMoverShaker,
        'singularname': TTLocalizer.SuitMoverShakerS,
        'pluralname':   TTLocalizer.SuitMoverShakerP,
        'level': 4,
        'hp':   SuitDefaultHPDict(5, 9),
        'def':  SuitDefaultDefDict(5, 9),
        'freq': (50,30,10,5,5),
        'acc':  (35,40,45,50,55),
        'attacks':
                (('BrainStorm',
                    (5,6,8,10,12),
                    (60,75,80,85,90),
                    (15,15,15,15,15)),
                ('HalfWindsor',
                    (6,9,11,13,16),
                    (50,65,70,75,80),
                    (20,20,20,20,20)),
                ('Quake',
                    (9,12,15,18,21),
                    (60,65,75,80,85),
                    (20,20,20,20,20)),
                ('Shake',
                    (6,8,10,12,14),
                    (70,75,80,85,90),
                    (25,25,25,25,25)),
                ('Tremor',
                    (5,6,7,8,9),
                    (50,50,50,50,50),
                    (20,20,20,20,20)))},
 'tf': {'name': TTLocalizer.SuitTwoFace,
        'singularname': TTLocalizer.SuitTwoFaceS,
        'pluralname': TTLocalizer.SuitTwoFaceP,
        'level': 5,
        'hp':   SuitDefaultHPDict(6, 12),
        'def':  SuitDefaultDefDict(6, 12),
        'freq': (50,30,10,5,5),
        'acc':  (35,40,45,50,55),
        'attacks':
                (('EvilEye',
                    (10,12,14,16,18,20,22),
                    (60,75,80,85,90,90,90),
                    (25,25,25,25,25,25,25)),
                ('HangUp',
                    (7,8,10,12,13,15,17),
                    (50,60,70,80,90,90,90),
                    (15,15,15,15,15,15,15)),
                ('RazzleDazzle',
                    (8,10,12,14,16,18,20),
                    (60,65,70,75,80,85,90),
                    (25,25,25,25,25,25,25)),
                ('PowerTrip',
                    (8,9,11,13,15,17,19),
                    (65,75,80,85,90,95,95),
                    (15,15,15,15,15,15,15)),
                ('RedTape',
                    (6,7,8,9,10,11,12),
                    (60,65,75,85,90,95,95),
                    (20,20,20,20,20,20,20)))},
 'm': {'name':          TTLocalizer.SuitTheMingler,
       'singularname':  TTLocalizer.SuitTheMinglerS,
       'pluralname':    TTLocalizer.SuitTheMinglerP,
       'level': 6,
       'hp':    SuitDefaultHPDict(7, 15),
       'def':   SuitDefaultDefDict(7, 15),
       'freq':  (50,30,10,5,5),
       'acc':   (35,40,45,50,55),
       'attacks':
               (('BuzzWord',
                    (10,11,13,15,16,18,20,22,24),
                    (60,75,80,85,90,95,95,95,95),
                    (20,20,20,20,20,20,20,20,20)),
                ('ParadigmShift',
                    (10,13,14,15,18,20,22,24,26),
                    (60,70,75,80,90,90,90,90,90),
                    (25,25,25,25,25,25,25,25,25)),
                ('MumboJumbo',
                    (16,18,20,22,24,26,28,30,32),
                    (70,75,80,85,95,95,95,95,95),
                    (30,30,30,30,30,30,30,30,30)),
                ('Schmooze',
                    (7,8,12,15,16,17,18,19,20),
                    (55,65,75,85,95,95,95,95,95),
                    (15,15,15,15,15,15,15,15,15)),
                ('TeeOff',
                    (8,9,10,11,12,13,14,16,16),
                    (70,75,80,85,95,95,95,95,95),
                    (10,10,10,10,10,10,10,10,10)))},
 'mh': {'name':         TTLocalizer.SuitMrHollywood,
        'singularname': TTLocalizer.SuitMrHollywoodS,
        'pluralname':   TTLocalizer.SuitMrHollywoodP,
        'level': 7,
        'hp':   SuitDefaultHPDict(8, 50),
        'def':  SuitDefaultDefDict(8, 50),
        'freq': (50,30,10,5,5),
        'acc':  (35,40,45,50,55),
        'attacks':
                (('TeeOff',
                    (10,12,15,18,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58),
                    (55,65,75,80,85,90,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95),
                    (25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25)),
                ('SongAndDance',
                    (14,16,18,20,22,23,24,25,26,27,28,29,30,30,31,32,33,34,35,36,37,38,39,40,41,42,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60),
                    (45,50,55,60,65,70,75,80,85,90,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95),
                    (25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25)),
                ('Schmooze',
                    (16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58),
                    (55,65,75,80,85,90,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95),
                    (25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25)),
                ('RazzleDazzle',
                    (8,11,14,17,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58),
                    (70,75,70,75,90,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95),
                    (25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25)))},
 'sc': {'name':         TTLocalizer.SuitShortChange,
        'singularname': TTLocalizer.SuitShortChangeS,
        'pluralname':   TTLocalizer.SuitShortChangeP,
        'level': 0,
        'hp':   SuitDefaultHPDict(1, 5),
        'def':  SuitDefaultDefDict(1, 5),
        'freq': (50,30,10,5,5),
        'acc':  (35,40,45,50,55),
        'attacks':
                (('Watercooler',
                    (2,2,3,4,6),
                    (50,50,50,50,50),
                    (20,20,20,20,20)),
                ('BounceCheck',
                    (3,5,7,9,11),
                    (75,80,85,90,95),
                    (15,15,15,15,15)),
                ('ClipOnTie',
                    (1,1,2,2,3),
                    (50,50,50,50,50),
                    (25,25,25,25,25)),
                ('PickPocket',
                    (2,2,3,4,6),
                    (95,95,95,95,95),
                    (40,40,40,40,40)))},
 'pp': {'name':         TTLocalizer.SuitPennyPincher,
        'singularname': TTLocalizer.SuitPennyPincherS,
        'pluralname':   TTLocalizer.SuitPennyPincherP,
        'level': 1,
        'hp':   SuitDefaultHPDict(2, 6),
        'def':  SuitDefaultDefDict(2, 6),
        'freq': (50,30,10,5,5),
        'acc':  (45,50,55,60,65),
        'attacks':
                (('BounceCheck',
                    (4,5,6,8,12),
                    (75,75,75,75,75),
                    (45,45,45,45,45)),
                ('FreezeAssets',
                    (2,3,4,6,9),
                    (75,75,75,75,75),
                    (20,20,20,20,20)),
                ('FingerWag',
                    (1,2,3,4,6),
                    (50,50,50,50,50),
                    (35,35,35,35,35)))},
 'tw': {'name':         TTLocalizer.SuitTightwad,
        'singularname': TTLocalizer.SuitTightwadS,
        'pluralname':   TTLocalizer.SuitTightwadP,
        'level': 2,
        'hp':   SuitDefaultHPDict(3, 7),
        'def':  SuitDefaultDefDict(3, 7),
        'freq': (50,30,10,5,5),
        'acc':  (65,70,75,80,85),
        'attacks':
                (('Fired',
                    (3,4,5,5,6),
                    (75,75,75,75,75),
                    (75,5,5,5,5)),
                ('GlowerPower',
                    (3,4,6,9,12),
                    (95,95,95,95,95),
                    (10,15,20,25,30)),
                ('FingerWag',
                    (3,3,4,4,5),
                    (75,75,75,75,75),
                    (5,70,5,5,5)),
                ('FreezeAssets',
                    (3,4,6,9,12),
                    (75,75,75,75,75),
                    (5,5,65,5,30)),
                ('BounceCheck',
                    (5,6,9,13,18),
                    (75,75,75,75,75),
                    (5,5,5,60,30)))},
 'bc': {'name':         TTLocalizer.SuitBeanCounter,
        'singularname': TTLocalizer.SuitBeanCounterS,
        'pluralname':   TTLocalizer.SuitBeanCounterP,
        'level': 3,
        'hp':   SuitDefaultHPDict(4, 8),
        'def':  SuitDefaultDefDict(4, 8),
        'freq': (50,30,10,5,5),
        'acc':  (70,75,80,82,85),
        'attacks':
                (('Audit',
                    (4,6,9,12,15),
                    (95,95,95,95,95),
                    (20,20,20,20,20)),
                ('Calculate',
                    (4,6,9,12,15),
                    (75,75,75,75,75),
                    (25,25,25,25,25)),
                ('Tabulate',
                    (4,6,9,12,15),
                    (75,75,75,75,75),
                    (25,25,25,25,25)),
                ('WriteOff',
                    (4,6,9,12,15),
                    (95,95,95,95,95),
                    (30,30,30,30,30)))},
 'nc': {'name':         TTLocalizer.SuitNumberCruncher,
        'singularname': TTLocalizer.SuitNumberCruncherS,
        'pluralname':   TTLocalizer.SuitNumberCruncherP,
        'level': 4,
        'hp':   SuitDefaultHPDict(5, 9),
        'def':  SuitDefaultDefDict(5, 9),
        'freq': (50,30,10,5,5),
        'acc':  (35,40,45,50,55),
        'attacks':
                (('Audit',
                    (5,6,8,10,12),
                    (60,75,80,85,90),
                    (15,15,15,15,15)),
                ('Calculate',
                    (6,7,9,11,13),
                    (60,75,80,85,90),
                    (30,30,30,30,30)),
                ('Crunch',
                    (9,12,15,18,21),
                    (60,65,75,80,85),
                    (35,35,35,35,35)),
                ('Tabulate',
                    (8,9,10,11,12),
                    (90,90,90,90,90),
                    (20,20,20,20,20)))},
 'mb': {'name': TTLocalizer.SuitMoneyBags,
        'singularname': TTLocalizer.SuitMoneyBagsS,
        'pluralname': TTLocalizer.SuitMoneyBagsP,
        'level': 5,
        'hp':   SuitDefaultHPDict(6, 12),
        'def':  SuitDefaultDefDict(6, 12),
        'freq': (50,30,10,5,5),
        'acc':  (35,40,45,50,55),
        'attacks':
                (('Liquidate',
                    (10,12,14,16,18,20,22),
                    (60,75,80,85,90,95,95),
                    (30,30,30,30,30,30,30)),
                ('MarketCrash',
                    (8,10,12,14,16,18,20),
                    (60,65,70,75,80,85,90),
                    (45,45,45,45,45,45,45)),
                ('PowerTie',
                    (6,7,8,9,10,11,12),
                    (60,65,75,85,90,95,95),
                    (25,25,25,25,25,25,25)))},
 'ls': {'name':         TTLocalizer.SuitLoanShark,
        'singularname': TTLocalizer.SuitLoanSharkS,
        'pluralname':   TTLocalizer.SuitLoanSharkP,
        'level': 6,
        'hp':   SuitDefaultHPDict(7, 15),
        'def':  SuitDefaultDefDict(7, 15),
        'freq': (50,30,10,5,5),
        'acc':  (35,40,45,50,55),
        'attacks':
                (('Bite',
                    (10,11,13,15,16,18,20,22,24),
                    (60,75,80,85,90,95,95,95,95),
                    (30,30,30,30,30,30,30,30,30)),
                ('Chomp',
                    (12,15,18,21,24,26,28,30,32),
                    (60,70,75,80,90,95,95,95,95),
                    (35,35,35,35,35,35,35,35,35)),
                ('PlayHardball',
                    (9,11,13,15,17,19,21,23,25),
                    (55,65,75,85,90,90,90,90,90),
                    (20,20,20,20,20,20,20,20,20)),
                ('WriteOff',
                    (6,8,10,12,14,16,18,20,22),
                    (70,75,80,85,90,90,90,90,95),
                    (15,15,15,15,15,15,15,15,15)))},
 'rb': {'name':         TTLocalizer.SuitRobberBaron,
        'singularname': TTLocalizer.SuitRobberBaronS,
        'pluralname':   TTLocalizer.SuitRobberBaronP,
        'level': 7,
        'hp':   SuitDefaultHPDict(8, 50),
        'def':  SuitDefaultDefDict(8, 50),
        'freq': (50,30,10,5,5),
        'acc':  (35,40,45,50,55),
        'attacks':
                (('Synergy',
                    (11,14,16,18,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59),
                    (60,65,70,75,80,85,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90),
                    (25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25)),
                ('CigarSmoke',
                    (14,15,17,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58),
                    (60,65,70,75,80,85,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90),
                    (25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25)),
                ('PickPocket',
                    (8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50),
                    (55,65,70,75,80,85,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90),
                    (25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25)),
                ('TeeOff',
                    (10,12,14,16,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56),
                    (60,65,75,85,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90),
                    (25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25)))},

 'bf': {'name': TTLocalizer.SuitBottomFeeder,
        'singularname': TTLocalizer.SuitBottomFeederS,
        'pluralname': TTLocalizer.SuitBottomFeederP,
        'level': 0,
        'hp':   SuitDefaultHPDict(1, 5),
        'def':  SuitDefaultDefDict(1, 5),
        'freq': (50,30,10,5,5),
        'acc':  (35,40,45,50,55),
        'attacks':
                (('RubberStamp',
                    (2,3,4,5,6),
                    (75,80,85,90,95),
                    (20,20,20,20,20)),
                ('Shred',
                    (2,4,6,8,10),
                    (50,55,60,65,70),
                    (20,20,20,20,20)),
                ('Watercooler',
                    (3,4,5,6,7),
                    (95,95,95,95,95),
                    (10,10,10,10,10)),
                ('PickPocket',
                    (1,1,2,2,3),
                    (25,30,35,40,45),
                    (50,50,50,50,50)))},
 'b': {'name':          TTLocalizer.SuitBloodsucker,
       'singularname':  TTLocalizer.SuitBloodsuckerS,
       'pluralname':    TTLocalizer.SuitBloodsuckerP,
       'level': 1,
       'hp':   SuitDefaultHPDict(2, 6),
       'def':  SuitDefaultDefDict(2, 6),
       'freq':  (50,30,10,5,5),
       'acc':   (45,50,55,60,65),
       'attacks':
                (('EvictionNotice',
                    (1,2,3,3,4),
                    (75,75,75,75,75),
                    (20,20,20,20,20)),
                ('RedTape',
                    (2,3,4,6,9),
                    (75,75,75,75,75),
                    (20,20,20,20,20)),
                ('Withdrawal',
                    (6,8,10,12,14),
                    (95,95,95,95,95),
                    (10,10,10,10,10)),
                ('Bite',
                    (2,3,4,5,6),
                    (95,95,95,95,95),
                    (10,10,10,10,10)),
                ('Liquidate',
                    (2,3,4,6,9),
                    (50,60,70,80,90),
                    (40,40,40,40,40)))},
 'dt': {'name':         TTLocalizer.SuitDoubleTalker,
        'singularname': TTLocalizer.SuitDoubleTalkerS,
        'pluralname':   TTLocalizer.SuitDoubleTalkerP,
        'level': 2,
        'hp':   SuitDefaultHPDict(3, 7),
        'def':  SuitDefaultDefDict(3, 7),
        'freq': (50,30,10,5,5),
        'acc':  (65,70,75,80,85),
        'attacks':
                (('RubberStamp',
                    (1,1,1,1,1),
                    (50,60,70,80,90),
                    (5,5,5,5,5)),
                ('BounceCheck',
                    (1,1,1,1,1),
                    (50,60,70,80,90),
                    (5,5,5,5,5)),
                ('BuzzWord',
                    (1,2,3,5,6),
                    (50,60,70,80,90),
                    (20,20,20,20,20)),
                ('DoubleTalk',
                    (6,6,9,13,18),
                    (50,60,70,80,90),
                    (25,25,25,25,25)),
                ('Jargon',
                    (3,4,6,9,12),
                    (50,60,70,80,90),
                    (25,25,25,25,25)),
                ('MumboJumbo',
                    (3,4,6,9,12),
                    (50,60,70,80,90),
                    (20,20,20,20,20)))},
 'ac': {'name':         TTLocalizer.SuitAmbulanceChaser,
        'singularname': TTLocalizer.SuitAmbulanceChaserS,
        'pluralname':   TTLocalizer.SuitAmbulanceChaserP,
        'level': 3,
        'hp':   SuitDefaultHPDict(4, 8),
        'def':  SuitDefaultDefDict(4, 8),
        'freq': (50,30,10,5,5),
        'acc':  (65,70,75,80,85),
        'attacks':
                (('Shake',
                    (4,6,9,12,15),
                    (75,75,75,75,75),
                    (15,15,15,15,15)),
                ('RedTape',
                    (6,8,12,15,19),
                    (75,75,75,75,75),
                    (30,30,30,30,30)),
                ('Rolodex',
                    (3,4,5,6,7),
                    (75,75,75,75,75),
                    (20,20,20,20,20)),
                ('HangUp',
                    (2,3,4,5,6),
                    (75,75,75,75,75),
                    (35,35,35,35,35)))},
 'bs': {'name':         TTLocalizer.SuitBackStabber,
        'singularname': TTLocalizer.SuitBackStabberS,
        'pluralname':   TTLocalizer.SuitBackStabberP,
        'level': 4,
        'hp':   SuitDefaultHPDict(5, 9),
        'def':  SuitDefaultDefDict(5, 9),
        'freq': (50,30,10,5,5),
        'acc':  (35,40,45,50,55),
        'attacks':
                (('GuiltTrip',
                    (8,11,13,15,18),
                    (60,75,80,85,90),
                    (35,35,35,35,35)),
                ('RestrainingOrder',
                    (6,7,9,11,13),
                    (50,65,70,75,90),
                    (25,25,25,25,25)),
                ('PickPocket',
                    (10,12,15,18,20),
                    (55,65,80,85,95),
                    (15,15,15,15,15)),
                ('FingerWag',
                    (5,6,7,8,9),
                    (50,55,65,75,80),
                    (25,25,25,25,25)))},
 'sd': {'name':         TTLocalizer.SuitSpinDoctor,
        'singularname': TTLocalizer.SuitSpinDoctorS,
        'pluralname':   TTLocalizer.SuitSpinDoctorP,
        'level': 5,
        'hp':   SuitDefaultHPDict(6, 12),
        'def':  SuitDefaultDefDict(6, 12),
        'freq': (50,30,10,5,5),
        'acc':  (35,40,45,50,55),
        'attacks':
                (('ParadigmShift',
                    (9,10,13,16,17,18,20),
                    (60,75,80,85,90,95,95),
                    (30,30,30,30,30,30,30)),
                ('Quake',
                    (8,10,12,14,16,18,20),
                    (60,65,70,75,80,85,90),
                    (20,20,20,20,20,20,20)),
                ('Spin',
                    (10,12,15,18,20,22,24),
                    (70,75,80,85,90,95,95),
                    (35,35,35,35,35,35,35)),
                ('WriteOff',
                    (6,7,8,9,10,11,12),
                    (60,65,75,85,90,95,95),
                    (15,15,15,15,15,15,15)))},
 'le': {'name':         TTLocalizer.SuitLegalEagle,
        'singularname': TTLocalizer.SuitLegalEagleS,
        'pluralname':   TTLocalizer.SuitLegalEagleP,
        'level': 6,
        'hp':   SuitDefaultHPDict(7, 15),
        'def':  SuitDefaultDefDict(7, 15),
        'freq': (50,30,10,5,5),
        'acc':  (35,40,45,50,55),
        'attacks':
                (('EvilEye',
                    (10,11,13,15,16,18,20,22,24),
                    (60,75,80,85,90,95,95,95,95),
                    (20,20,20,20,20,20,20,20,20)),
                ('Jargon',
                    (7,9,11,13,15,17,19,21,22),
                    (60,70,75,80,90,95,95,95,95),
                    (15,15,15,15,15,15,15,15,15)),
                ('Legalese',
                    (11,12,13,15,17,19,21,23,25),
                    (55,65,75,85,95,95,95,95,95),
                    (35,35,35,35,35,30,30,30,30)),
                ('PeckingOrder',
                    (12,15,17,19,22,24,27,29,32),
                    (70,75,80,85,95,95,95,95,95),
                    (30,30,30,30,30,35,35,35,35)))},
 'bw': {'name':         TTLocalizer.SuitBigWig,
        'singularname': TTLocalizer.SuitBigWigS,
        'pluralname':   TTLocalizer.SuitBigWigP,
        'level': 7,
        'hp':   SuitDefaultHPDict(8, 50),
        'def':  SuitDefaultDefDict(8, 50),
        'freq': (50,30,10,5,5),
        'acc':  (35,40,45,50,55,60,65,70,70,70,70,70,70,70),
        'attacks':
                (('GuiltTrip',
                    (11,14,16,19,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59),
                    (70,75,80,85,90,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95),
                    (25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25)),
                ('ThrowBook',
                    (14,16,18,20,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60),
                    (70,75,80,85,90,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95),
                    (25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25)),
                ('CigarSmoke',
                    (10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52),
                    (70,75,80,85,90,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95),
                    (25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25)),
                ('FingerWag',
                    (13,15,17,19,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59),
                    (80,85,85,90,90,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95),
                    (25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25)))},
    'cmb': {
        'name':         TTLocalizer.SuitCMB,
        'singularname': TTLocalizer.SuitCMBS,
        'pluralname':   TTLocalizer.SuitCMBP,
        'level':    50,
        'hp':   (4500,),
        'def':  (80,),
        'freq': (0,),
        'acc':  (0,),
        'attacks':
        (
            ('PickPocket',
            (40,),
            (95,),
            (25,)),
            ('GlowerPower',
            (35,),
            (95,),
            (25,)),
            ('PowerTrip',
            (42,),
            (95,),
            (25,)),
            ('EvilEye',
            (48,),
            (95,),
            (25,)),
            ('JuryNotice',
            (0,),
            (0,),
            (0,)),
            ('CompoundingInterest',
            (1,),
            (100,),
            (0,)),
            ('BookKeeping',
            (0,),
            (0,),
            (0,)),
        )
    },
    'ssb': {
        'name':         TTLocalizer.SuitShadow,
        'singularname': TTLocalizer.SuitShadowS,
        'pluralname':   TTLocalizer.SuitShadowP,
        'level':    10,
        'hp':   SuitShadowHPDict(0, 50),
        'def':  (0,),
        'freq': (0,),
        'acc':  (0,),
        'attacks':
        (
            ('Corruption',
            (1,),
            (100,),
            (60,)),
            ('Recarmdra',
            (0,),
            (98,),
            (0,)),
            ('GroupCorruption',
            (1,),
            (100,),
            (40,)),
        )
    },
    'hst': {
        'name':         TTLocalizer.SuitHustler,
        'singularname': TTLocalizer.SuitHustlerS,
        'pluralname':   TTLocalizer.SuitHustlerP,
        'level':    40,
        'hp':   (5000,),
        'def':  (65,),
        'freq': (0,),
        'acc':  (0,),
        'attacks':
        (
            ('PowerTrip',
            (28,),
            (95,),
            (15,)),
            ('ParadigmShift',
            (36,),
            (95,),
            (15,)),
            ('CigarSmoke',
            (36,),
            (95,),
            (30,)),
            ('Demotion',
            (38,),
            (95,),
            (25,)),
            ('Fired',
            (42,),
            (95,),
            (15,)),
            ('ShadowMarketing',
            (0,),
            (0,),
            (0,)),
            ('ShadowWave',
            (1,),
            (100,),
            (0,)),
            ('Coalescence',
            (0,),
            (0,),
            (0,))
        )
    },
    'ren': {
        'name':         TTLocalizer.SuitRenegade,
        'singularname': TTLocalizer.SuitRenegadeS,
        'pluralname':   TTLocalizer.SuitRenegadeP,
        'level':    45,
        'hp':   (8500,),
        'def':  (65,),
        'freq': (0,),
        'acc':  (0,),
        'attacks':
        (
            ('GlowerPower',
            (48,),
            (95,),
            (20,)),
            ('RazzleDazzle',
            (43,),
            (95,),
            (25,)),
            ('PickPocket',
            (36,),
            (95,),
            (25,)),
            ('ParadigmShift',
            (38,),
            (90,),
            (15,)),
            ('PowerTrip',
            (34,),
            (90,),
            (15,)),
            ('Haymaker',
            (0,),
            (0,),
            (0,)),
            ('Detonate',
            (0,),
            (0,),
            (0,)),
            ('Detonate2',
            (0,),
            (0,),
            (0,)),
            ('Detonate3',
            (0,),
            (0,),
            (0,)),
            ('CrackUp',
            (0,),
            (98,),
            (0,)),   
            ('Flashbang',
            (42,),
            (100,),
            (0,)), 
        )
    },
}

ATK_TGT_UNKNOWN = 1
ATK_TGT_SINGLE = 2
ATK_TGT_GROUP = 3
SuitAttacks = {'Audit': ('phone', ATK_TGT_SINGLE),
 'Bite': ('throw-paper', ATK_TGT_SINGLE),
 'BounceCheck': ('throw-paper', ATK_TGT_SINGLE),
 'BrainStorm': ('effort', ATK_TGT_SINGLE),
 'BuzzWord': ('speak', ATK_TGT_SINGLE),
 'Calculate': ('phone', ATK_TGT_SINGLE),
 'Canned': ('throw-paper', ATK_TGT_SINGLE),
 'Chomp': ('throw-paper', ATK_TGT_SINGLE),
 'CigarSmoke': ('cigar-smoke', ATK_TGT_SINGLE),
 'ClipOnTie': ('throw-paper', ATK_TGT_SINGLE),
 'Crunch': ('throw-object', ATK_TGT_SINGLE),
 'Demotion': ('magic1', ATK_TGT_SINGLE),
 'DoubleTalk': ('speak', ATK_TGT_SINGLE),
 'Downsize': ('magic2', ATK_TGT_SINGLE),
 'EvictionNotice': ('throw-paper', ATK_TGT_SINGLE),
 'EvilEye': ('glower', ATK_TGT_SINGLE),
 'Filibuster': ('speak', ATK_TGT_SINGLE),
 'FillWithLead': ('pencil-sharpener', ATK_TGT_SINGLE),
 'FingerWag': ('finger-wag', ATK_TGT_SINGLE),
 'Fired': ('magic2', ATK_TGT_SINGLE),
 'FiveOClockShadow': ('glower', ATK_TGT_SINGLE),
 'FloodTheMarket': ('glower', ATK_TGT_SINGLE),
 'FountainPen': ('pen-squirt', ATK_TGT_SINGLE),
 'FreezeAssets': ('glower', ATK_TGT_SINGLE),
 'Gavel': ('gavel', ATK_TGT_SINGLE),
 'GlowerPower': ('glower', ATK_TGT_SINGLE),
 'GuiltTrip': ('magic1', ATK_TGT_GROUP),
 'HalfWindsor': ('throw-paper', ATK_TGT_SINGLE),
 'HangUp': ('phone', ATK_TGT_SINGLE),
 'HeadShrink': ('magic1', ATK_TGT_SINGLE),
 'HotAir': ('speak', ATK_TGT_SINGLE),
 'Jargon': ('speak', ATK_TGT_SINGLE),
 'Legalese': ('speak', ATK_TGT_SINGLE),
 'Liquidate': ('magic1', ATK_TGT_SINGLE),
 'MarketCrash': ('throw-paper', ATK_TGT_SINGLE),
 'MumboJumbo': ('speak', ATK_TGT_SINGLE),
 'ParadigmShift': ('magic2', ATK_TGT_GROUP),
 'PeckingOrder': ('throw-object', ATK_TGT_SINGLE),
 'PickPocket': ('pickpocket', ATK_TGT_SINGLE),
 'PinkSlip': ('throw-paper', ATK_TGT_SINGLE),
 'PlayHardball': ('throw-paper', ATK_TGT_SINGLE),
 'PoundKey': ('phone', ATK_TGT_SINGLE),
 'PowerTie': ('throw-paper', ATK_TGT_SINGLE),
 'PowerTrip': ('magic1', ATK_TGT_GROUP),
 'Quake': ('quick-jump', ATK_TGT_GROUP),
 'RazzleDazzle': ('smile', ATK_TGT_SINGLE),
 'RedTape': ('throw-object', ATK_TGT_SINGLE),
 'ReOrg': ('magic3', ATK_TGT_SINGLE),
 'RestrainingOrder': ('throw-paper', ATK_TGT_SINGLE),
 'Rolodex': ('roll-o-dex', ATK_TGT_SINGLE),
 'RubberStamp': ('rubber-stamp', ATK_TGT_SINGLE),
 'RubOut': ('hold-eraser', ATK_TGT_SINGLE),
 'Sacked': ('throw-paper', ATK_TGT_SINGLE),
 'SandTrap': ('golf-club-swing', ATK_TGT_SINGLE),
 'Schmooze': ('speak', ATK_TGT_SINGLE),
 'Shake': ('stomp', ATK_TGT_GROUP),
 'Shred': ('shredder', ATK_TGT_SINGLE),
 'SongAndDance': ('song-and-dance', ATK_TGT_GROUP),
 'Spin': ('magic3', ATK_TGT_SINGLE),
 'Synergy': ('magic3', ATK_TGT_GROUP),
 'Tabulate': ('phone', ATK_TGT_SINGLE),
 'TeeOff': ('golf-club-swing', ATK_TGT_SINGLE),
 'ThrowBook': ('throw-object', ATK_TGT_SINGLE),
 'Tremor': ('stomp', ATK_TGT_GROUP),
 'Watercooler': ('watercooler', ATK_TGT_SINGLE),
 'Withdrawal': ('magic1', ATK_TGT_SINGLE),
 'WriteOff': ('hold-pencil', ATK_TGT_SINGLE),
 'JuryNotice':  ('snap', ATK_TGT_GROUP),
 'CompoundingInterest':  ('magic3', ATK_TGT_GROUP),
 'BookKeeping':  ('cease', ATK_TGT_GROUP),
 'Corruption':  ('magic2', ATK_TGT_SINGLE),
 'GroupCorruption':  ('magic4', ATK_TGT_GROUP),
 'Recarmdra':   ('effort', ATK_TGT_GROUP),
 'ShadowMarketing': ('summon', ATK_TGT_GROUP),
 'ShadowWave': ('summon', ATK_TGT_GROUP),
 'Coalescence': ('summon', ATK_TGT_GROUP),
 'Haymaker': ('effort', ATK_TGT_SINGLE),
 'Detonate': ('effort', ATK_TGT_GROUP),
 'Detonate2': ('effort', ATK_TGT_GROUP),
 'Detonate3': ('effort', ATK_TGT_GROUP),
 'CrackUp': ('snap', ATK_TGT_GROUP),
 'Flashbang': ('snap', ATK_TGT_GROUP)
}
AUDIT = SuitAttacks.keys().index('Audit')
BITE = SuitAttacks.keys().index('Bite')
BOUNCE_CHECK = SuitAttacks.keys().index('BounceCheck')
BRAIN_STORM = SuitAttacks.keys().index('BrainStorm')
BUZZ_WORD = SuitAttacks.keys().index('BuzzWord')
CALCULATE = SuitAttacks.keys().index('Calculate')
CANNED = SuitAttacks.keys().index('Canned')
CHOMP = SuitAttacks.keys().index('Chomp')
CIGAR_SMOKE = SuitAttacks.keys().index('CigarSmoke')
CLIPON_TIE = SuitAttacks.keys().index('ClipOnTie')
CRUNCH = SuitAttacks.keys().index('Crunch')
DEMOTION = SuitAttacks.keys().index('Demotion')
DOWNSIZE = SuitAttacks.keys().index('Downsize')
DOUBLE_TALK = SuitAttacks.keys().index('DoubleTalk')
EVICTION_NOTICE = SuitAttacks.keys().index('EvictionNotice')
EVIL_EYE = SuitAttacks.keys().index('EvilEye')
FILIBUSTER = SuitAttacks.keys().index('Filibuster')
FILL_WITH_LEAD = SuitAttacks.keys().index('FillWithLead')
FINGER_WAG = SuitAttacks.keys().index('FingerWag')
FIRED = SuitAttacks.keys().index('Fired')
FIVE_O_CLOCK_SHADOW = SuitAttacks.keys().index('FiveOClockShadow')
FLOOD_THE_MARKET = SuitAttacks.keys().index('FloodTheMarket')
FOUNTAIN_PEN = SuitAttacks.keys().index('FountainPen')
FREEZE_ASSETS = SuitAttacks.keys().index('FreezeAssets')
GAVEL = SuitAttacks.keys().index('Gavel')
GLOWER_POWER = SuitAttacks.keys().index('GlowerPower')
GUILT_TRIP = SuitAttacks.keys().index('GuiltTrip')
HALF_WINDSOR = SuitAttacks.keys().index('HalfWindsor')
HANG_UP = SuitAttacks.keys().index('HangUp')
HEAD_SHRINK = SuitAttacks.keys().index('HeadShrink')
HOT_AIR = SuitAttacks.keys().index('HotAir')
JARGON = SuitAttacks.keys().index('Jargon')
LEGALESE = SuitAttacks.keys().index('Legalese')
LIQUIDATE = SuitAttacks.keys().index('Liquidate')
MARKET_CRASH = SuitAttacks.keys().index('MarketCrash')
MUMBO_JUMBO = SuitAttacks.keys().index('MumboJumbo')
PARADIGM_SHIFT = SuitAttacks.keys().index('ParadigmShift')
PECKING_ORDER = SuitAttacks.keys().index('PeckingOrder')
PICK_POCKET = SuitAttacks.keys().index('PickPocket')
PINK_SLIP = SuitAttacks.keys().index('PinkSlip')
PLAY_HARDBALL = SuitAttacks.keys().index('PlayHardball')
POUND_KEY = SuitAttacks.keys().index('PoundKey')
POWER_TIE = SuitAttacks.keys().index('PowerTie')
POWER_TRIP = SuitAttacks.keys().index('PowerTrip')
QUAKE = SuitAttacks.keys().index('Quake')
RAZZLE_DAZZLE = SuitAttacks.keys().index('RazzleDazzle')
RED_TAPE = SuitAttacks.keys().index('RedTape')
RE_ORG = SuitAttacks.keys().index('ReOrg')
RESTRAINING_ORDER = SuitAttacks.keys().index('RestrainingOrder')
ROLODEX = SuitAttacks.keys().index('Rolodex')
RUBBER_STAMP = SuitAttacks.keys().index('RubberStamp')
RUB_OUT = SuitAttacks.keys().index('RubOut')
SACKED = SuitAttacks.keys().index('Sacked')
SANDTRAP = SuitAttacks.keys().index('SandTrap')
SCHMOOZE = SuitAttacks.keys().index('Schmooze')
SHAKE = SuitAttacks.keys().index('Shake')
SHRED = SuitAttacks.keys().index('Shred')
SONG_AND_DANCE = SuitAttacks.keys().index('SongAndDance')
SPIN = SuitAttacks.keys().index('Spin')
SYNERGY = SuitAttacks.keys().index('Synergy')
TABULATE = SuitAttacks.keys().index('Tabulate')
TEE_OFF = SuitAttacks.keys().index('TeeOff')
THROW_BOOK = SuitAttacks.keys().index('ThrowBook')
TREMOR = SuitAttacks.keys().index('Tremor')
WATERCOOLER = SuitAttacks.keys().index('Watercooler')
WITHDRAWAL = SuitAttacks.keys().index('Withdrawal')
WRITE_OFF = SuitAttacks.keys().index('WriteOff')
JURY_NOTICE = SuitAttacks.keys().index('JuryNotice')
COMPOUNDING_INTEREST = SuitAttacks.keys().index('CompoundingInterest')
BOOK_KEEPING = SuitAttacks.keys().index('BookKeeping')
CORRUPTION = SuitAttacks.keys().index('Corruption')
SHADOW_MARKETING = SuitAttacks.keys().index('ShadowMarketing')
RECARMDRA = SuitAttacks.keys().index('Recarmdra')
SHADOW_WAVE = SuitAttacks.keys().index('ShadowWave')
COALESCENCE = SuitAttacks.keys().index('Coalescence')
GROUP_CORRUPTION = SuitAttacks.keys().index('GroupCorruption')
HAYMAKER = SuitAttacks.keys().index('Haymaker')
DETONATE = SuitAttacks.keys().index('Detonate')
DETONATE_2 = SuitAttacks.keys().index('Detonate2')
DETONATE_3 = SuitAttacks.keys().index('Detonate3')
CRACK_UP = SuitAttacks.keys().index('CrackUp')
FLASHBANG = SuitAttacks.keys().index('Flashbang')

def getFaceoffTaunt(suitName, doId):
    if suitName in SuitFaceoffTaunts:
        taunts = SuitFaceoffTaunts[suitName]
    else:
        taunts = TTLocalizer.SuitFaceoffDefaultTaunts
    return taunts[doId % len(taunts)]


SuitFaceoffTaunts = OTPLocalizer.SuitFaceoffTaunts

def getAttackTauntIndexFromIndex(suit, attackIndex):
    adict = getSuitAttack(suit.getStyleName(), suit.getLevel(), attackIndex)
    return getAttackTauntIndex(adict['name'])


def getAttackTauntIndex(attackName):
    if attackName in SuitAttackTaunts:
        taunts = SuitAttackTaunts[attackName]
        return random.randint(0, len(taunts) - 1)
    else:
        return 1


def getAttackTaunt(attackName, index = None):
    if attackName in ['Corruption', 'GroupCorruption']:
        from string import ascii_letters, punctuation, digits
        s = ''
        for i in range(64):
            s += random.choice(ascii_letters + punctuation + digits)
        return s
    if attackName in SuitAttackTaunts:
        taunts = SuitAttackTaunts[attackName]
    else:
        taunts = TTLocalizer.SuitAttackDefaultTaunts
    if index != None:
        if index >= len(taunts):
            notify.warning('index exceeds length of taunts list in getAttackTaunt')
            return TTLocalizer.SuitAttackDefaultTaunts[0]
        return taunts[index]
    else:
        return random.choice(taunts)
    return


SuitAttackTaunts = TTLocalizer.SuitAttackTaunts
