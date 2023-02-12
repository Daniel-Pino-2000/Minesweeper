from random import randrange
from turtle import Screen, Turtle
from time import sleep
from datetime import datetime
import shelve
import atexit
import sys

class Minesweeper:
    
    HiddenCell = None
    MinedCell = True
    FreeCell = False

    def __init__(self, mines, rows, columns, board=None, board2=None,\
                 symbol=None, flag=None, cells_to_show=None,\
                 cells_shown=None, visited_cells=None, turns=None,\
                 assistant=None, assistant2=None):
        self.mines = mines
        self.rows = rows
        self.columns = columns
        # self.board initiates with every cell free of mines and then it locates the
        # mines randomly
        self.board = self.create_matrix(self.FreeCell) if board is None else board 
        # self.board2 initiates with every hiden cell to draw the board of the initial
        # game.        
        self.board2 = self.create_matrix(self.HiddenCell) if board2 is None else board
        # In each cell of self.symbol it writes the number of mines that surrounds it.
        self.symbol = self.create_matrix(self.HiddenCell) if symbol is None else symbol
        # In the matrix self.flag are located the cells that contains flags.
        self.flag = self.create_matrix(self.HiddenCell) if flag is None else flag 
        self.cells_to_show = self.create_matrix(0) if cells_to_show is None else cells_to_show
        # In cells_shown are the cells that are already shown and shouldn´t be visited.
        self.cells_shown = self.create_matrix(0) if cells_shown is None else cells_shown
        # visited cells saves the cells already visited.
        self.visited_cells = set() if visited_cells is None else visited_cells
        # self.turns counts the turns that the game last.
        self.turns = 0 if turns is None else turns
        self.assistant = [0] if assistant is None else assistant        
        self.assistant2 = self.create_matrix(None) if assistant2 is None else assistant2
        self.screen = self.create_screen()
        self.turtle = self.create_turtle()
        # Shows the current date.
        self.today = datetime.now()
        # Tells you if the game is over or not.
        self.end = False
        self.db = shelve.open("minesweeper.dbm")
        self.drawing = False
        atexit.register(self.exit)
    
    def create_screen(self):
        screen = Screen()
        screen.setup(self.columns*50, self.rows*50)
        screen.screensize(self.columns*50, self.rows*50)
        screen.setworldcoordinates(-.5, -.5, self.columns+.5, self.rows+.5)
        screen.delay(0)
        screen.onclick(self.left_click)
        if sys.platform == "darwin":
            screen.onclick(self.right_click, 2)
        else:
            screen.onclick(self.right_click, 3) 
        return screen
    
    def create_turtle(self):
        turtle = Turtle()
        turtle.hideturtle()
        turtle.speed('fastest')
        return turtle
    
    def start(self):
        if self.turns == 0:
            self.locate_mines()
            self.fill_symbols()
            self.draw_board(self.board2)
        else:
            for i in range(len(self.symbol)):
                for j in range(len(self.symbol[0])):            
                    self.draw_cell(self.assistant2, self.symbol, i, j)
                    if self.flag[i][j] == 1:
                        self.turtle.penup()
                        self.turtle.goto(j+.4, i+.2)
                        self.turtle.pendown()
                        self.turtle.pencolor('yellow')
                        self.turtle.goto(j+.4, i+.8)
                        self.turtle.goto(j+.7, i+.6)
                        self.turtle.goto(j+.4, i+.5)
                        
        self.screen.mainloop()
    
    def create_matrix(self, valor):
        '''
        This function creates the matrix with a size of rows x columns, and initiates with
        the last value.
        '''
        matrix = []
        for i in range(self.rows):
            matrix.append([valor] * self.columns)
        return matrix    


    def locate_mines(self):
        '''
        This function randomly locates the cells with mines.
        '''
        list = []
        while len(list) < self.mines:
            i = randrange(self.rows)
            j = randrange(self.columns)
            if [i, j] not in list:
                list.append([i, j])
                self.board[i][j] = self.MinedCell
    
    def fill_symbols(self):
        '''
        This function fills the cells with the corresponding symbols
        '''
        rows = len(self.symbol)
        columns = len(self.symbol[0])
        for i in range(rows):
            for j in range(columns):
                
                if self.board[i][j] == self.MinedCell:
                    self.symbol[i][j] = 'Mine'
                
                elif self.board[i][j] == self.FreeCell:
                    number_of_mines = 0
                    for location in self.CloseLocations(rows, columns, i, j):
                        if self.board[location[0]][location[1]] == self.MinedCell:
                            number_of_mines += 1
                    self.symbol[i][j] = number_of_mines

    def draw_board(self, board):
        '''
        This function draws the board of the game.
        '''
        for i in range(len(self.symbol)):
            for j in range(len(self.symbol[0])):
                if self.cells_shown[i][j] == 0:
                    self.draw_cell(board, self.symbol, i, j)

    def draw_cell(self, tile, board, i, j):
        '''
        This function draws the content of the cells.
        '''
        self.drawing = True
        self.turtle.penup()
        self.turtle.pencolor('black')
        self.turtle.goto(j+.5, i)
        self.turtle.begin_fill()
        if tile[i][j] == self.HiddenCell:
            self.turtle.fillcolor('blue')
            self.turtle.circle(.5)
        elif tile[i][j] == self.FreeCell:
            self.turtle.fillcolor('white')
            self.turtle.circle(.5)
            self.turtle.goto(j+.5, i+.25)
            self.turtle.write(board[i][j])
            self.assistant2[i][j] = self.FreeCell
        elif tile[i][j] == self.MinedCell:
            self.turtle.fillcolor('red')
            self.turtle.circle(.5)
            self.turtle.goto(j+.5, i+.25)
            self.turtle.write(board[i][j])
        self.turtle.end_fill()
        self.turtle.pendown()
        self.drawing = False
    
    def draw_flag(self, flag, i, j):
        '''
        This function draws the flags.
        '''
        if flag[i][j] == 1:
            self.turtle.penup()
            self.turtle.goto(j+.4, i+.2)
            self.turtle.pendown()
            self.turtle.pencolor('yellow')
            self.turtle.goto(j+.4, i+.8)
            self.turtle.goto(j+.7, i+.6)
            self.turtle.goto(j+.4, i+.5)
        elif flag[i][j] == None:
            self.turtle.penup()
            self.turtle.goto(j+.5, i)
            self.turtle.begin_fill()
            self.turtle.fillcolor('blue')
            self.turtle.circle(.5)
            self.turtle.end_fill()
    
    def CloseLocations(self, rows, columns, row, column):
        '''
        This function returns the location of the mines close to the cell.
        '''
        locations = []
        if row - 1 >= 0:
            locations.append((row - 1, column))
        if column - 1 >= 0:
            locations.append((row, column - 1))
        if row - 1 >= 0 and column - 1 >= 0:
            locations.append((row - 1, column - 1))
        if column + 1 < columns:
            locations.append((row, column + 1))
        if row + 1 < rows:
            locations.append((row + 1, column))
        if row + 1 < rows and column + 1 < columns:
            locations.append((row + 1, column + 1))
        if row + 1 < rows and column - 1 >= 0:
            locations.append((row + 1, column - 1))
        if row - 1 >= 0 and column + 1 < columns:
            locations.append((row - 1, column + 1))
        return locations
           
    def neighboring_cells(self, selection):
        '''
        This function shows the cells without mines.
        '''
        rows = len(self.symbol)
        columns = len(self.symbol[0])
        for location in self.CloseLocations(rows, columns, selection[0], selection[1]):
            if location in self.visited_cells:
                continue
            self.draw_cell(self.board, self.symbol, location[0], location[1])
            self.visited_cells.add((location[0], location[1]))
            self.cells_to_show[location[0]][location[1]] = 1        

    def show_cells(self, i, j):
        '''
        This function shows the cells close to the boxes with 0 mines arround.
        '''
        repetition = self.columns
        
        self.cells_to_show[i][j] = 1
        
        for a in range(repetition):
            for i in range(len(self.symbol)):
                for j in range(len(self.symbol[0])):
                    if self.symbol[i][j] == 0 and self.cells_shown[i][j] == 0 and self.cells_to_show[i][j] == 1:
                        self.neighboring_cells((i,j))
                        self.cells_shown[i][j] = 1
        
    def left_click(self, x, y):
        '''
        This function conects with the event of the left click.
        '''
        if self.drawing:
            return
        self.check(self.flag)
        [j, i] = [int(x), int(y)]
        if 0 <= i < len(self.symbol) and 0 <= j < (len(self.symbol[0])):
            if self.board[i][j] != None and self.flag[i][j] != 1:
                temporary1 = [i, j]
                self.assistant = [i, j]
                self.draw_cell(self.board, self.symbol, temporary1[0], temporary1[1])
                self.turns += 1
                self.show_cells(i, j)
            
            temporary1 = None
            self.save()

        if self.turns > 0 and self.ending(self.board, self.assistant):
            self.draw_board(self.board)
            self.save()
        else:
            self.screen.onclick(self.left_click)     

    def right_click(self, x, y):
        '''
        This function conects with the event of the right click.
        '''
        if self.drawing:
            return
        self.check(self.flag)
        [j, i] = [int(x), int(y)]
        if 0 <= i < len(self.symbol) and 0 <= j < (len(self.symbol[0])):
            if self.flag[i][j] == None:
                self.flag[i][j] = 1
            elif self.flag[i][j] == 1:
                self.flag[i][j] = None
            self.draw_flag(self.flag, i, j)
            self.save()
            
        if self.turns > 0 and self.ending(self.board, self.assistant):
            self.draw_board(self.board)
            self.save()
        else:
            self.screen.onclick(self.left_click)

    def exit(self):
        print("Goodbye")
        self.save()
        self.db.close()
            
    def check(self, flag):
        '''
        This function checks if you discovered every mine.
        '''
        number = 0
        for i in range(len(flag)):
            for j in range(len(flag[0])):
                if flag[i][j] == 1 and self.board[i][j] == True:
                    number += 1
        if number == self.mines:
            return True
        else:
            return False
                
    def ending(self, board, selection):
        '''
        Stop the game in the moment that you win or loose.
        '''
        if board[selection[0]][selection[1]] == self.MinedCell:
            print('Game Over')
            self.end = True
            return True
        elif self.check(self.flag):
            print('You Win')
            self.end = True
            return True
        else:
            return False
        
    def save(self):
        '''Saves the class minesweeper to the database'''
        if self.end and "data" in self.db:
            del self.db["data"]
        else:
            d = {"mines":self.mines, "rows":self.rows, "columns":self.columns, "board":self.board, "board2":self.board2, \
                 "symbol":self.symbol, "flag":self.flag, "cells_to_show":self.cells_to_show, \
                 "cells_shown":self.cells_shown, "visited_cells":self.visited_cells, \
                 "turns":self.turns, "assistant":self.assistant, "assistant2":self.assistant2, "fecha":self.today}
            self.db["data"] = d
        self.db.sync()

def start_minesweeper():
    '''
    Asks the user the difficulty he prefers.
    '''
    option = None
    while option not in [0, 1, 2, 3]:
        print('Choose an option.')
        db = shelve.open("minesweeper.dbm")
        data = db.get("data", None)
        
        if data is not None:
            today = data["fecha"]
            dia = today.strftime("%m-%d-%y %I:%M%p")
            print('0) Cargar juego de {0}'.format(dia))
        db.close()
        print('1) Easy (6 mines).')
        print('2) Normal (8 mines).')
        print('3) Hard (12 mines).')
        choice = input('Tell me your choice: ')
        try:
            option = int(choice)
        except ValueError:
            print('Error: choice {0} is not valid.'.format(choice))
            continue
        
        if option == 0 and data is not None:
            return minesweeper(data["mines"], data["rows"], data["columns"], data["board"], data["board2"], data["symbol"], \
                              data["flag"], data["cells_to_show"], data["cells_shown"], data["visited_cells"], \
                              data["turns"], data["assistant"], data["assistant2"])        
        elif option == 1:
            mines = 6
            rows = 6
            columns = 8
        elif option == 2:
            mines = 8
            rows = 8
            columns = 10
        elif option == 3:
            mines = 15
            rows = 15
            columns = 18
        else:
            print('Wrong choice.')
    return Minesweeper(mines, rows, columns)

def main():
    minesweeper = start_minesweeper()
    minesweeper.start()

if __name__ == '__main__':
    main()