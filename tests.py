import main
import unittest


class TestDamage(unittest.TestCase):
    def testDamage(self):
        game = main.archivedboard.Board(main.statreader.produceableUnits)
        game.initializeUnit(5, 1, 'statsheets/Archer.txt', 0)
        game.initializeUnit(4, 19, 'statsheets/Archer.txt', 1)
        game.attack(game.tileAt(5, 1), game.tileAt(4, 19))
        self.assertEqual(game.unitOn(4, 19).getHp(), 6)
    def testDeath(self):
        game = main.archivedboard.Board(main.statreader.produceableUnits)
        game.initializeUnit(5, 1, 'statsheets/Archer.txt', 0)
        game.initializeUnit(4, 19, 'statsheets/Archer.txt', 1)
        game.tileAt(4, 19).damageUnit(20)
        self.assertEqual(game.unitOn(4, 19), None)
    def testIncome(self):
        game = main.archivedboard.Board(main.statreader.produceableUnits)
        game.initializeUnit(5, 1, 'statsheets/Archer.txt', 0)
        game.initializeUnit(4, 19, 'statsheets/Archer.txt', 1)
        game.initializeUnit(1, 1, 'statsheets/Farm.txt', 1)
        game.nextTurn()
        self.assertEqual(game.getPlayerNum(1).getMoney(), 6)

if __name__ == '__main__':
    unittest.main()