class Bonus(object):
    def __init__(self, tags, multiplier, exceptions=['nothing']):
        self.tags = tags
        self.exceptions = exceptions
        self.multiplier = multiplier

    def bonusAgainst(self, target):
        for tag in target.getTags():
            if tag in self.tags and tag not in self.exceptions:
                return self.multiplier
        return 1

class Bonuses(object):
    def __init__(self, *bonuses):
        self.bonuses = bonuses
        # This is a dictionary.

    def bonusAgainst(self, target):
        highestBonus = 1
        for bonus in self.bonuses:
            if bonus.bonusAgainst(target) > highestBonus:
                highestBonus = bonus.bonusAgainst(target)
        return highestBonus
