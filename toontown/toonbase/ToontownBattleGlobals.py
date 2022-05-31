from ToontownGlobals import *
import math
import TTLocalizer
MAX_TOON_CAPACITY = 4
MAX_SUIT_CAPACITY = 4
BattleCamFaceOffFov = 30.0
BattleCamFaceOffPos = Point3(0, -10, 4)
BattleCamDefaultPos = Point3(0, -8.6, 16.5)
BattleCamDefaultHpr = Vec3(0, -61, 0)
BattleCamDefaultFov = 80.0
BattleCamMenuFov = 65.0
BattleCamJoinPos = Point3(0, -12, 13)
BattleCamJoinHpr = Vec3(0, -45, 0)
SkipMovie = 0
BaseHp = 15
Tracks = TTLocalizer.BattleGlobalTracks
NPCTracks = TTLocalizer.BattleGlobalNPCTracks
TrackColors = (
    (211 / 255.0, 148 / 255.0, 255 / 255.0),
    (249 / 255.0, 255 / 255.0, 93 / 255.0),
    (79 / 255.0, 190 / 255.0, 76 / 255.0),
    (93 / 255.0, 108 / 255.0, 239 / 255.0),
    (255 / 255.0, 145 / 255.0, 66 / 255.0),
    (255 / 255.0, 65 / 255.0, 199 / 255.0),
    (67 / 255.0, 243 / 255.0, 255 / 255.0)
)

HEAL_TRACK = 0
TRAP_TRACK = 1
LURE_TRACK = 2
SOUND_TRACK = 3
THROW_TRACK = 4
SQUIRT_TRACK = 5
DROP_TRACK = 6

NPC_RESTOCK_GAGS = 7
NPC_TOONS_HIT = 8
NPC_COGS_MISS = 9
NPC_DAMAGE_BOOST = 10

MIN_TRACK_INDEX = 0
MAX_TRACK_INDEX = 6
MIN_LEVEL_INDEX = 0
MAX_LEVEL_INDEX = 6

MAX_UNPAID_LEVEL_INDEX = 4
LAST_REGULAR_GAG_LEVEL = 5
UBER_GAG_LEVEL_INDEX = 6
NUM_GAG_TRACKS = 7

PropTypeToTrackBonus = {
    AnimPropTypes.Hydrant: SQUIRT_TRACK,
    AnimPropTypes.Mailbox: THROW_TRACK,
    AnimPropTypes.Trashcan: HEAL_TRACK
}

Levels = [0, 20, 100, 500, 2000, 6000, 10000]
MaxSkill = 10000
ExperienceCap = 10000

MaxToonAcc = 95
StartingLevel = 0
CarryLimits = (((10,
   0,
   0,
   0,
   0,
   0,
   0),
  (10,
   5,
   0,
   0,
   0,
   0,
   0),
  (15,
   10,
   5,
   0,
   0,
   0,
   0),
  (20,
   15,
   10,
   5,
   0,
   0,
   0),
  (25,
   20,
   15,
   10,
   3,
   0,
   0),
  (30,
   25,
   20,
   15,
   7,
   3,
   0),
  (30,
   25,
   20,
   15,
   7,
   3,
   1)),
 ((10,
   0,
   0,
   0,
   0,
   0,
   0),
  (10,
   5,
   0,
   0,
   0,
   0,
   0),
  (15,
   10,
   5,
   0,
   0,
   0,
   0),
  (20,
   15,
   10,
   5,
   0,
   0,
   0),
  (25,
   20,
   15,
   10,
   3,
   0,
   0),
  (30,
   25,
   20,
   15,
   7,
   3,
   0),
  (30,
   25,
   20,
   15,
   7,
   3,
   1)),
 ((10,
   0,
   0,
   0,
   0,
   0,
   0),
  (10,
   5,
   0,
   0,
   0,
   0,
   0),
  (15,
   10,
   5,
   0,
   0,
   0,
   0),
  (20,
   15,
   10,
   5,
   0,
   0,
   0),
  (25,
   20,
   15,
   10,
   3,
   0,
   0),
  (30,
   25,
   20,
   15,
   7,
   3,
   0),
  (30,
   25,
   20,
   15,
   7,
   3,
   1)),
 ((10,
   0,
   0,
   0,
   0,
   0,
   0),
  (10,
   5,
   0,
   0,
   0,
   0,
   0),
  (15,
   10,
   5,
   0,
   0,
   0,
   0),
  (20,
   15,
   10,
   5,
   0,
   0,
   0),
  (25,
   20,
   15,
   10,
   3,
   0,
   0),
  (30,
   25,
   20,
   15,
   7,
   3,
   0),
  (30,
   25,
   20,
   15,
   7,
   3,
   1)),
 ((10,
   0,
   0,
   0,
   0,
   0,
   0),
  (10,
   5,
   0,
   0,
   0,
   0,
   0),
  (15,
   10,
   5,
   0,
   0,
   0,
   0),
  (20,
   15,
   10,
   5,
   0,
   0,
   0),
  (25,
   20,
   15,
   10,
   3,
   0,
   0),
  (30,
   25,
   20,
   15,
   7,
   3,
   0),
  (30,
   25,
   20,
   15,
   7,
   3,
   1)),
 ((10,
   0,
   0,
   0,
   0,
   0,
   0),
  (10,
   5,
   0,
   0,
   0,
   0,
   0),
  (15,
   10,
   5,
   0,
   0,
   0,
   0),
  (20,
   15,
   10,
   5,
   0,
   0,
   0),
  (25,
   20,
   15,
   10,
   3,
   0,
   0),
  (30,
   25,
   20,
   15,
   7,
   3,
   0),
  (30,
   25,
   20,
   15,
   7,
   3,
   1)),
 ((10,
   0,
   0,
   0,
   0,
   0,
   0),
  (10,
   5,
   0,
   0,
   0,
   0,
   0),
  (15,
   10,
   5,
   0,
   0,
   0,
   0),
  (20,
   15,
   10,
   5,
   0,
   0,
   0),
  (25,
   20,
   15,
   10,
   3,
   0,
   0),
  (30,
   25,
   20,
   15,
   7,
   3,
   0),
  (30,
   25,
   20,
   15,
   7,
   3,
   1)))

MaxProps = ((20, 50), (40, 80), (110, 140))

DLF_SKELECOG = 1
DLF_FOREMAN = 2
DLF_VP = 4
DLF_CFO = 8
DLF_SUPERVISOR = 16
DLF_VIRTUAL = 32
DLF_REVIVES = 64
EXECUTIVE_HP_MULT = 1.5
EXECUTIVE_DMG_MULT = 1.2
EXECUTIVE_BASE_CHANCE = 30
V2_SKELECOG_DMG_MULT = 1.5
pieNames = ['tart',
 'fruitpie-slice',
 'creampie-slice',
 'fruitpie',
 'creampie',
 'birthday-cake',
 'wedding-cake',
 'lawbook']
AvProps = (('feather',
  'bullhorn',
  'lipstick',
  'bamboocane',
  'pixiedust',
  'baton',
  'baton'),
 ('banana',
  'rake',
  'marbles',
  'quicksand',
  'trapdoor',
  'tnt',
  'traintrack'),
 ('1dollar',
  'smmagnet',
  '5dollar',
  'bigmagnet',
  '10dollar',
  'hypnogogs',
  'hypnogogs'),
 ('bikehorn',
  'whistle',
  'bugle',
  'aoogah',
  'elephant',
  'foghorn',
  'singing'),
 ('cupcake',
  'fruitpieslice',
  'creampieslice',
  'fruitpie',
  'creampie',
  'cake',
  'cake'),
 ('flower',
  'waterglass',
  'waterballoon',
  'bottle',
  'firehose',
  'stormcloud',
  'stormcloud'),
 ('flowerpot',
  'sandbag',
  'anvil',
  'weight',
  'safe',
  'piano',
  'piano'))
AvPropsNew = (('inventory_feather',
  'inventory_megaphone',
  'inventory_lipstick',
  'inventory_bamboo_cane',
  'inventory_pixiedust',
  'inventory_juggling_cubes',
  'inventory_ladder'),
 ('inventory_bannana_peel',
  'inventory_rake',
  'inventory_marbles',
  'inventory_quicksand_icon',
  'inventory_trapdoor',
  'inventory_tnt',
  'inventory_traintracks'),
 ('inventory_1dollarbill',
  'inventory_small_magnet',
  'inventory_5dollarbill',
  'inventory_big_magnet',
  'inventory_10dollarbill',
  'inventory_hypno_goggles',
  'inventory_screen'),
 ('inventory_bikehorn',
  'inventory_whistle',
  'inventory_bugle',
  'inventory_aoogah',
  'inventory_elephant',
  'inventory_fog_horn',
  'inventory_opera_singer'),
 ('inventory_tart',
  'inventory_fruit_pie_slice',
  'inventory_cream_pie_slice',
  'inventory_fruitpie',
  'inventory_creampie',
  'inventory_cake',
  'inventory_wedding'),
 ('inventory_squirt_flower',
  'inventory_glass_of_water',
  'inventory_water_gun',
  'inventory_seltzer_bottle',
  'inventory_firehose',
  'inventory_storm_cloud',
  'inventory_geyser'),
 ('inventory_flower_pot',
  'inventory_sandbag',
  'inventory_anvil',
  'inventory_weight',
  'inventory_safe_box',
  'inventory_piano',
  'inventory_ship'))
AvPropStrings = TTLocalizer.BattleGlobalAvPropStrings
AvPropStringsSingular = TTLocalizer.BattleGlobalAvPropStringsSingular
AvPropStringsPlural = TTLocalizer.BattleGlobalAvPropStringsPlural
AvPropAccuracy = ((95,
  95,
  95,
  95,
  95,
  95,
  100),
 (0,
  0,
  0,
  0,
  0,
  0,
  0),
 (65,
  65,
  70,
  70,
  75,
  75,
  90),
 (95,
  95,
  95,
  95,
  95,
  95,
  95),
 (75,
  75,
  75,
  75,
  75,
  75,
  75),
 (95,
  95,
  95,
  95,
  95,
  95,
  95),
 (50,
  50,
  50,
  50,
  50,
  50,
  50))
AvLureBonusAccuracy = (60,
 60,
 70,
 70,
 80,
 80,
 100)
AvLureRounds = (2, 2, 3, 3, 4, 4, 5)
AvSoakRounds = (2, 2, 3, 3, 4, 4, 5)
AvSoakDefReduction = 15
AvTrackAccStrings = TTLocalizer.BattleGlobalAvTrackAccStrings
AvPropDamage = ((((6, 8), (Levels[0], Levels[1])),
  ((12, 15), (Levels[1], Levels[2])),
  ((22, 26), (Levels[2], Levels[3])),
  ((33, 39), (Levels[3], Levels[4])),
  ((45, 50), (Levels[4], Levels[5])),
  ((63, 78), (Levels[5], Levels[6])),
  ((135, 135), (Levels[6], MaxSkill))),
 (((35, 35), (Levels[0], Levels[1])),
  ((50, 50), (Levels[1], Levels[2])),
  ((75, 75), (Levels[2], Levels[3])),
  ((115, 115), (Levels[3], Levels[4])),
  ((160, 160), (Levels[4], Levels[5])),
  ((220, 220), (Levels[5], Levels[6])),
  ((280, 280), (Levels[6], MaxSkill))),
 (((0, 0), (0, 0)),
  ((0, 0), (0, 0)),
  ((0, 0), (0, 0)),
  ((0, 0), (0, 0)),
  ((0, 0), (0, 0)),
  ((0, 0), (0, 0)),
  ((0, 0), (0, 0))),
 (((5, 7), (Levels[0], Levels[1])),
  ((9, 11), (Levels[1], Levels[2])),
  ((14, 16), (Levels[2], Levels[3])),
  ((19, 21), (Levels[3], Levels[4])),
  ((26, 32), (Levels[4], Levels[5])),
  ((35, 50), (Levels[5], Levels[6])),
  ((65, 65), (Levels[6], MaxSkill))),
 (((13, 13), (Levels[0], Levels[1])),
  ((20, 20), (Levels[1], Levels[2])),
  ((35, 35), (Levels[2], Levels[3])),
  ((50, 50), (Levels[3], Levels[4])),
  ((90, 90), (Levels[4], Levels[5])),
  ((130, 130), (Levels[5], Levels[6])),
  ((170, 170), (Levels[6], MaxSkill))),
 (((6, 8), (Levels[0], Levels[1])),
  ((10, 12), (Levels[1], Levels[2])),
  ((18, 21), (Levels[2], Levels[3])),
  ((27, 30), (Levels[3], Levels[4])),
  ((45, 56), (Levels[4], Levels[5])),
  ((60, 80), (Levels[5], Levels[6])),
  ((115, 115), (Levels[6], MaxSkill))),
 (((18, 20), (Levels[0], Levels[1])),
  ((30, 35), (Levels[1], Levels[2])),
  ((45, 55), (Levels[2], Levels[3])),
  ((65, 80), (Levels[3], Levels[4])),
  ((90, 125), (Levels[4], Levels[5])),
  ((145, 180), (Levels[5], Levels[6])),
  ((220, 220), (Levels[6], MaxSkill))))

TRAP_EXECUTIVE_BONUS = 0.3
TRAP_HEALTHY_BONUS = 0.2
LURE_KNOCKBACK_VALUE = 0.65

ATK_SINGLE_TARGET = 0
ATK_GROUP_TARGET = 1
AvPropTargetCat = ((ATK_SINGLE_TARGET,
  ATK_GROUP_TARGET,
  ATK_SINGLE_TARGET,
  ATK_GROUP_TARGET,
  ATK_SINGLE_TARGET,
  ATK_GROUP_TARGET,
  ATK_GROUP_TARGET),
 (ATK_SINGLE_TARGET,
  ATK_SINGLE_TARGET,
  ATK_SINGLE_TARGET,
  ATK_SINGLE_TARGET,
  ATK_SINGLE_TARGET,
  ATK_SINGLE_TARGET,
  ATK_SINGLE_TARGET),
 (ATK_GROUP_TARGET,
  ATK_GROUP_TARGET,
  ATK_GROUP_TARGET,
  ATK_GROUP_TARGET,
  ATK_GROUP_TARGET,
  ATK_GROUP_TARGET,
  ATK_GROUP_TARGET),
 (ATK_SINGLE_TARGET,
  ATK_SINGLE_TARGET,
  ATK_SINGLE_TARGET,
  ATK_SINGLE_TARGET,
  ATK_SINGLE_TARGET,
  ATK_SINGLE_TARGET,
  ATK_GROUP_TARGET))
AvPropTarget = (0,
 3,
 0,
 2,
 3,
 3,
 3)

def getTrapDamage(trapLevel, toon, suit = None, executive = None, healthy = None):
    if suit:
        executive = suit.getExecutive() or suit.getManager()
        healthy = suit.currHP >= suit.maxHP / 2
    damage = getAvPropDamage(TRAP_TRACK, trapLevel, toon.experience.getExp(TRAP_TRACK))
    if healthy:
        damage += math.ceil(damage * TRAP_HEALTHY_BONUS)
    if executive:
        damage += math.ceil(damage * TRAP_EXECUTIVE_BONUS)
    return int(damage)

def getAvPropDamage(attackTrack, attackLevel, exp):
    minD = AvPropDamage[attackTrack][attackLevel][0][0]
    maxD = AvPropDamage[attackTrack][attackLevel][0][1]
    minE = AvPropDamage[attackTrack][attackLevel][1][0]
    maxE = AvPropDamage[attackTrack][attackLevel][1][1]
    expVal = min(exp, maxE)
    expPerHp = float(maxE - minE + 1) / float(maxD - minD + 1)
    damage = math.floor((expVal - minE) / expPerHp) + minD
    if damage <= 0:
        damage = minD
    return damage


def getDamageBonus(normal):
    bonus = int(normal * 0.1)
    if bonus < 1 and normal > 0:
        bonus = 1
    return bonus


def isGroup(track, level):
    return AvPropTargetCat[AvPropTarget[track]][level]


def getCreditMultiplier(floorIndex):
    return 1 + floorIndex * 0.5


def getFactoryCreditMultiplier(factoryId):
    return 2.0


def getFactoryMeritMultiplier(factoryId):
    return 4.0


def getMintCreditMultiplier(mintId):
    return {CashbotMintIntA: 2.0,
     CashbotMintIntB: 2.5,
     CashbotMintIntC: 3.0}.get(mintId, 1.0)


def getStageCreditMultiplier(floor):
    return getCreditMultiplier(floor)


def getCountryClubCreditMultiplier(countryClubId):
    return {BossbotCountryClubIntA: 2.0,
     BossbotCountryClubIntB: 2.5,
     BossbotCountryClubIntC: 3.0}.get(countryClubId, 1.0)


def getBossBattleCreditMultiplier(battleNumber):
    return 1 + battleNumber


def getInvasionMultiplier():
    return 2.0


def getMoreXpHolidayMultiplier():
    return 2.0


def encodeUber(trackList):
    bitField = 0
    for trackIndex in xrange(len(trackList)):
        if trackList[trackIndex] > 0:
            bitField += pow(2, trackIndex)

    return bitField


def decodeUber(flagMask):
    if flagMask == 0:
        return []
    maxPower = 16
    workNumber = flagMask
    workPower = maxPower
    trackList = []
    while workPower >= 0:
        if workNumber >= pow(2, workPower):
            workNumber -= pow(2, workPower)
            trackList.insert(0, 1)
        else:
            trackList.insert(0, 0)
        workPower -= 1

    endList = len(trackList)
    foundOne = 0
    while not foundOne:
        if trackList[endList - 1] == 0:
            trackList.pop(endList - 1)
            endList -= 1
        else:
            foundOne = 1

    return trackList


def getUberFlag(flagMask, index):
    decode = decodeUber(flagMask)
    if index >= len(decode):
        return 0
    else:
        return decode[index]


def getUberFlagSafe(flagMask, index):
    if flagMask == 'unknown' or flagMask < 0:
        return -1
    else:
        return getUberFlag(flagMask, index)

HUSTLER_SHADOW_WAVE_HEAL_AMP = 15
HUSTLER_COALESCENCE_HEAL_AMP = 5
HUSTLER_COALESCENCE_HEAL_BASE = 100
HUSTLER_BONUS_DMG_PER_SHADOW = 0.0725

ValidStatusConditions = (
    'cannotMiss',   # set acc. rate to 100%
    'alwaysMiss',   # set acc. rate to 0%
    'cannotDodge',  # set dodge rate to 0%
    'alwaysDodge',  # set dodge rate to 100%
    # both types, special conditions
    'dodgy',    # modify dodge rate by %
    # toon specific
    'allGagBoost',
    'noGags',
    'healBoost',
    'noToonUpGags',
    'trapBoost',
    'noTrapGags',
    'lureBoost',
    'noLureGags',
    'soundBoost',
    'noSoundGags',
    'throwBoost',
    'noThrowGags',
    'squirtBoost',
    'noSquirtGags',
    'dropBoost',
    'noDropGags',
    'noFires',
    'noSOS',
    # cog specific
    'soaked',   # decreases afflicted targets' dodge rates by 15%
    'lured',
    # battle specific
    'corruption',   # increases damage taken from attacks (toons only)
    'shadowInfluence',  # increases damage recieved from attacks (cogs only)
    'turnsSinceSummon',     # internal counter used for bosses
    'turnsSinceSummon2',    # internal counter used for bosses
)