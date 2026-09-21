
#python script to remove level file
import os
from database import LoadAllUsers
import re
maxUser =11
maxLevel =5
path = 'C:/Users/z5308/Desktop/VRTestingProject/data/small/'

def get_turn_number(s:str):
    return int(s.split('-turn')[1].split('-')[0])

levelmax = 5

fileToRemove = []
for userID in range(20):

    userName = 'user'+ str(userID)
    finalPath = path + userName+'/'
    files = os.listdir(finalPath)
    files = sorted(files, key=get_turn_number) 
    for file in files:
        file_parts = file.split("-")
      
        levelDiff = int(re.search(r'\d+', file_parts[2]).group()) 
        if(levelDiff > levelmax):
            fileToRemove.append(finalPath +file)


for file_path in fileToRemove:
    try:
        os.remove(file_path)
        print(f"File '{file_path}' has been successfully deleted.")
    except FileNotFoundError:
        print(f"File '{file_path}' not found.")
    except Exception as e:
        print(f"An error occurred while deleting '{file_path}': {e}")