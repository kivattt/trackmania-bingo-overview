# Put Youtube in fullscreen on the rightmost 1080p monitor

# pip3 install pillow scikit-learn

import time
import numpy as np
from PIL import ImageGrab, Image, ImageStat
from sklearn.cluster import KMeans

# Adjust these variables!
boardCellsWidth = 5
boardCellsHeight = 5
numTeams = 2

boardX = 5244
boardY = 874
boardWidth = 263
boardHeight = 263

boardCellWidth = boardWidth / boardCellsWidth
boardCellHeight = boardHeight / boardCellsHeight

def rgbWithin(r, g, b, within):
    if abs(r-g) > within:
        return False
    if abs(g-b) > within:
        return False
    if abs(r-b) > within:
        return False
    return True

def grabImageAveraged(theBbox):
    img1 = ImageGrab.grab(bbox = theBbox)
    time.sleep(1)
    img2 = ImageGrab.grab(bbox = theBbox)
    return Image.blend(img1, img2, 0.5)

def teamLeading(board):
    teamsBestLine = dict()
    teamsBestLinePosition = dict()

    # Rows (left/right)
    for y in range(boardCellsHeight):
        teamLine = dict()
        for x in range(boardCellsWidth):
            index = y * boardCellsHeight + x
            try:
                teamLine[board[index]] += 1
            except KeyError:
                teamLine[board[index]] = 1

        maxKey = max(teamLine, key=teamLine.get)
        try:
            if teamLine[maxKey] >= teamsBestLine[maxKey]:
                teamsBestLine[maxKey] = teamLine[maxKey]
                teamsBestLinePosition[maxKey] = (y, False)
        except KeyError:
            teamsBestLine[maxKey] = teamLine[maxKey]
            teamsBestLinePosition[maxKey] = (y, False)

    # Columns (up/down)
    for x in range(boardCellsWidth):
        teamLine = dict()
        for y in range(boardCellsHeight):
            index = y * boardCellsHeight + x
            try:
                teamLine[board[index]] += 1
            except KeyError:
                teamLine[board[index]] = 1

        maxKey = max(teamLine, key=teamLine.get)
        try:
            if teamLine[maxKey] >= teamsBestLine[maxKey]:
                teamsBestLine[maxKey] = teamLine[maxKey]
                teamsBestLinePosition[maxKey] = (x, True)
        except KeyError:
            teamsBestLine[maxKey] = teamLine[maxKey]
            teamsBestLinePosition[maxKey] = (x, True)

    bestTeam = max(teamsBestLine, key=teamsBestLine.get)
    return (bestTeam, teamsBestLinePosition[bestTeam])

while True:
    #img = ImageGrab.grab(bbox = (x, y, x+boardWidth, y+boardHeight))
    img = grabImageAveraged((boardX, boardY, boardX+boardWidth, boardY+boardHeight))

    meanColorsRGB = []
    meanColorsHue = []
    for y in range(boardCellsHeight):
        for x in range(boardCellsHeight):
            theX = x * boardCellWidth
            theY = y * boardCellHeight
            img2 = img.crop((theX, theY, theX + boardCellWidth, theY + boardCellHeight))
            meanColor = ImageStat.Stat(img2).median

            r = meanColor[0] / 255
            g = meanColor[1] / 255
            b = meanColor[2] / 255
            minimum = min(r,g,b)
            maximum = max(r,g,b)
            hue = 0
            if r == maximum:
                hue = (g - b) / max(1, maximum - minimum)
            elif g == maximum:
                hue = 2 + (b - r) / max(1, maximum - minimum)
            else:
                hue = 4 + (r - g) / max(1, maximum - minimum)

            meanColorsHue.append(hue)
            meanColorsRGB.append(meanColor)

    kmeans = KMeans(n_clusters = numTeams+1)
    # We do K-means on the hues instead of the RGB colors so it's more accurate
    kmeans.fit(np.array(meanColorsHue).reshape(-1, 1))
    #kmeans.fit(meanColors)

    board = kmeans.labels_
    teamAverageColors = dict()
    teamNColors = [0] * (numTeams+1)

    for i in range(len(board)):
        team = board[i]
        try:
            teamAverageColors[team][0] += meanColorsRGB[i][0]
            teamAverageColors[team][1] += meanColorsRGB[i][1]
            teamAverageColors[team][2] += meanColorsRGB[i][2]
        except KeyError:
            teamAverageColors[team] = meanColorsRGB[i]

        teamNColors[team] += 1

    for team, color in teamAverageColors.items():
        teamAverageColors[team][0] //= teamNColors[team]
        teamAverageColors[team][1] //= teamNColors[team]
        teamAverageColors[team][2] //= teamNColors[team]

    theTeamLeading = teamLeading(board)

    i = 0
    for y in range(boardCellsHeight):
        for x in range(boardCellsWidth):
    #        color = meanColorsRGB[i]
            color = teamAverageColors[board[i]]
            colorToUse = color.copy()

            print("\033[0;30m", end='')
    
            if theTeamLeading[1][1]: # Leading line is a column
                if x == theTeamLeading[1][0]:
                    print("\033[9m", end='')
                    colorToUse[0] //= 2
                    colorToUse[1] //= 2
                    colorToUse[2] //= 2
            else: # Leading line is a row
                if y == theTeamLeading[1][0]:
                    print("\033[9m", end='')
                    colorToUse[0] //= 2
                    colorToUse[1] //= 2
                    colorToUse[2] //= 2

            print("\033[48;2;" + str(colorToUse[0]) + ";" + str(colorToUse[1]) + ";" + str(colorToUse[2]) + "m", end='')
            print(board[i], end=' ')
            print("\033[0m", end='')
            i += 1
        print()

    color = teamAverageColors[theTeamLeading[0]]
    print("\033[38;2;" + str(color[0]) + ";" + str(color[1]) + ";" + str(color[2]) + "m", end='')
    print("+--------------+")
    print("| TEAM LEADING |")
    print("+--------------+")
    print()
    print("\033[0m", end='')
    time.sleep(2)
