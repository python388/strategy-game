class Player(object):
    def __init__(self, money, team, is_ai=False):
        self.money = money
        self.team = team
        self.is_ai = is_ai

    def isAI(self):
        return self.is_ai

    def setIsAI(self, is_ai: bool):
        self.is_ai = is_ai

    def getTeam(self):
        return self.team
    
    def setTeam(self, team):
        self.team = team

    def makeIncome(self, income):
        self.money += income
    
    def spendMoney(self, money):
        self.money -= money

    def setMoney(self, money):
        self.money = money

    def getMoney(self):
        return self.money