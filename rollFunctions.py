"""Functions for Rolling"""
import random
import logging

LOGGER = logging.getLogger(__name__)


async def keepHighest(dice: list, numToKeep: int):
    """Keeps Highest x in string"""
    return sorted(dice)[-numToKeep:]


async def keepLowest(dice: list, numToKeep: int):
    """Keeps Lowest x in string"""
    return sorted(dice)[:numToKeep]


async def dropHighest(dice: list, numToDrop: int):
    """Drops Highest x from string"""
    return sorted(dice)[:-numToDrop]


async def dropLowest(dice: list, numToDrop: int):
    """Drops Lowest x from string"""
    return sorted(dice)[numToDrop:]

dictDict = {"kh": keepHighest,
            "kl": keepLowest,
            "dh": dropHighest,
            "dl": dropLowest}


async def returnRoll(content):
    """Returns the roll message, ready to send"""
    diceRaw: str = content.split("roll ")[1].lower()
    prefix = diceRaw.split("d")[0]
    if prefix == "":
        diceToRoll = 1
    else:
        try:
            diceToRoll = int(prefix)
        except ValueError:
            return None
    try:
        diceSides = int(diceRaw.split("d")[1].split(" ")[0])
    except IndexError:
        diceSides = int(diceRaw.split("d")[1])
    except ValueError:
        return None

    if not all(0 <= x < 1000000 for x in [diceToRoll, diceSides]):
        return None

    if "+" in diceRaw:
        try:
            modNum = int(diceRaw.split("+")[1].split(" ")[0])
        except ValueError:
            modNum = int(diceRaw.split("+")[1])
        mod = modNum
    elif "-" in diceRaw:
        try:
            modNum = int(diceRaw.split("-")[1].split("-")[0])
        except ValueError:
            modNum = int(diceRaw.split("-")[1])
        mod = -modNum
    else:
        mod = 0
    diceRolls = [(random.randrange(1, diceSides + 1) + mod) for roll in range(diceToRoll)]
    if len(diceRolls) == 1:
        diceMessage = f"{diceRolls[0]}"
    else:
        diceMessage = f"{'+'.join([str(roll) for roll in diceRolls])}"

        for key, value in dictDict.items():
            if key in diceRaw:
                try:
                    numDice = int(diceRaw.split(key)[1].split(" ")[0])
                except IndexError:
                    numDice = int(diceRaw.split(key)[1])
                except ValueError:
                    numDice = 1
                finalDice = await value(diceRolls, numDice)
                break
        else:
            finalDice = diceRolls
        diceMessage = f"{diceMessage}; Final Value = {sum(finalDice)}"
    return diceMessage
