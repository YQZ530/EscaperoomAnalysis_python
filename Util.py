import os
import pandas as pd
from enum import Enum, IntEnum
import json
import string
class Percentile:
    def __init__(self):
   
        self.quantile = 0
        self.colName  = 'DifficultyRating'
        self.greaterThanPercentile = True

    def SetValue(self,  colName, 
         top_percentage, greaterThanPercentile):
        
        self.quantile = 1 - top_percentage/100
        self.colName  = colName
        self.greaterThanPercentile = greaterThanPercentile


class basicAlgorithm(IntEnum):
    Avg = 0
    Std =1
    Median =2
    NumPeak =3


 #Get Int from parameter
def checkIsIntOrIntList(s, default_v = 6):
    try:
        value = json.loads(s)
        # Check the type of the parsed value
        if isinstance(value, int):
            print(f"The value is an integer: {value}")
            return int(value)

        elif isinstance(value, list) and all(isinstance(item, int) for item in value):
            return [int(item) for item in value]
        else:
            print(f"Invalid data type, return default value {default_v}")
            return default_v
    except json.JSONDecodeError:
        print("Invalid string. String should be capture by []. Return 6 as default value")
        return default_v


def ifNeedToCreateFolder(filePath):
    # check if the folder existed
    if( "/" in filePath or "\\" in filePath):
        folder = filePath.rsplit('/', 1)[0]
        if(os.path.exists(folder) == False):
            # create a folder
            os.makedirs(folder)
def GetInt(s, default_v):
        # Check the type of the parsed value
        try:
            v = int(s)
            # print(f"The value is an integer: {s}")
            return v
        except:
            print(f"Invalid data type, return default value {default_v}")
        
        return default_v
        
def GetNumber(s, default_v):
    try:
        v = int(s)
        # print(f"The value is an integer: {s}")
        return v
    except ValueError:
         try:
            return float(s)
         except ValueError:
            print(f"Invalid data type or input {s}, return default value {default_v}")
            return default_v
def GetUserRangeFromText(userRangeText):
    def AddNumToArr(fromNum, toNum):
        arr = []
        for i in range(fromNum, toNum+1):
            arr.append(i)
        return arr
    def ParseInt(elem):
        parsed_value = -1
        try:
                parsed_value = int(elem)
                #print(f"add {parsed_value}")
        except ValueError:
                print(f"Unable to parse '{elem}' as an integer.")
        return parsed_value

    range_arr= userRangeText.split(",")
    userRangeArr = []
    for r in range_arr:
        elems = r.split("-")
        
        if(len(elems) == 1):
            userRangeArr.append(ParseInt(elems[0]))
        elif(len(elems) ==2):
            userRangeArr += AddNumToArr(ParseInt(elems[0]),ParseInt(elems[1]))
        else:
            print(f"wrong format for {r}")
    #print(userRangeArr)
    return userRangeArr

def GetAllUserData(df:pd.DataFrame, level:int ):
		filter_df = df[df['levelDiff'] == level]
		return filter_df

def GetSelectedUserData(df:pd.DataFrame, level:int, userStart:int, userTo:int):
    filtered_df = df[(df['userID'] >= userStart)  
                    & (df['userID'] <= userTo ) 
                    & (df['levelDiff'] == level  )]
    return filtered_df

def GetSelectedUserRangeData(df:pd.DataFrame, level:int, userSelectedRange):
	filtered_df = df[(df['userID'].isin(userSelectedRange)) & (df['levelDiff'] == level)]
	return filtered_df
def GetAllLevelFromUser(df:pd.DataFrame, userID:int):
    filter_df = df[df['userID'] == userID]
    return filter_df

def printArr(arr, prefix):
    s =""
    for i in arr:
        s+= f"{i},"
    print(f"{prefix}: [{s}]")

levelOrder = ['CBLeft1', 
'ObstacleSpec1', 'CoinsOnly1', 'CBSwipeUp1','ObstacleSpec3',   'ObstacleSpec2',
    'CBLeft2',  'CoinsOnly2','ObstacleSpec5','CBSwipeUp2',
    'ObstacleSpec4', 'CBSwipeDown1',] # it will match with unity

chunkObjectList = ['Coin1',
'Coin2','Coin3','Coin4','Coin5','Coin6',
'Bomb1','Bomb2','Bomb3', 'QuestionBox','ObstacleBox1',
'ObstacleBox2','Bar','Star','GroundIsland']
alphabet = list(string.ascii_uppercase)