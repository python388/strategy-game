class Player(object):
    def __init__(self, money, team):
        self.money = money
        self.team = team

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