
import os
import pandas as pd
from ast import literal_eval
import json

def getArrFromCsv(data):
    
    if(data is None):
        return []
    
    return [r  for r in data.apply(literal_eval).values if r is not None ]

def getStrArrFromCsv(data):
    if(data is None):
        return []

    return [r  for r in data]

def TryGetIntList(s):
    try:
        value = json.loads(s)
    
        if isinstance(value, list) and all(isinstance(item, int) for item in value):
            arr = [int(item) for item in value]
            return arr
        else:
            print(f"Invalid data type, return default value ")
            return []
    except json.JSONDecodeError:
        print("Invalid string. String should be capture by []. Return 6 as default value")
        return []

def is_csv_file(file_path):
            #_, file_extension = os.path.splitext(file_path)
            #return file_extension.lower() == '.csv'
        return file_path.lower().endswith('.csv')

def LoadSimpleFile(path):
    return pd.read_csv(path)

def LoadFileForUsers(path):
    def get_turn_number1(file:str):
        if not is_csv_file(file):
            return -1
        elif(not file.startswith('player')):
            return -1
        num = int(file.split('player')[1].split('.csv')[0])
        return num

    df = pd.DataFrame(columns = ['userID', 'plyr_pos', 'plyr_rot', 'l_hand_pos','r_hand_pos'])

    files = os.listdir(path)
    sorted_files = sorted(files, key=get_turn_number1) 

    #print(f"sorted_files {sorted_files} ")
   
    for file in sorted_files:
        
        if(not is_csv_file(file)):
            continue
        elif(not file.startswith('player')):
            continue
        print("Openning "+ file)

        with open(os.path.join(path, file)) as f:
                
            file_parts = file.split("player")
            userID = int(file_parts[1].split(".csv")[0]) 
            csv = pd.read_csv(f, header= 0) 
           
            data = { 'userID' : userID,
                    'plyr_pos':   getArrFromCsv (csv['plyr_pos']), 
                    'l_hand_pos':   getArrFromCsv (csv['l_hand_pos']), 
                    'r_hand_pos':   getArrFromCsv (csv['r_hand_pos']), 
                    'plyr_rot':  getArrFromCsv (csv['plyr_rot']), 
                     },
            
           
            if(df.shape[0] == 0 ):
                df = pd.DataFrame(data)
                
            else:
                new_df = pd.DataFrame(data)
                df = pd.concat([df,new_df], ignore_index= True)
    
   
    return df


def LoadEventForUsers(path):
    df = pd.DataFrame(columns=["eventType","startFrame","endFrame","dur"])
    sorted_files = os.listdir(path)
    for file in sorted_files:
        if (not file.endswith('event.csv')):
            continue

        with open(os.path.join(path, file)) as f:
            print("Openning " + file)
            suffix = file.split("_")[0]
            userID = int(suffix.split("player")[1])
            csv = pd.read_csv(f, header=0)
            data = {'id': userID,
                    'startFrame': csv['startFrame'],
                    'endFrame': csv['endFrame'],
                    'eventType': csv['eventType'],
                    }

            if (df.shape[0] == 0):
                df = pd.DataFrame(data)

            else:
                new_df = pd.DataFrame(data)
                df = pd.concat([df, new_df], ignore_index=True)

    return df

def LoadEyeGazeForUsers2(path):

    sorted_files = os.listdir(path)
    df = pd.DataFrame(columns=['AreaName', 'GazeObject', 'startKeyframe', 'endKeyframe', 'duration'])
    for file in sorted_files:  
        if(not file.endswith('_EyeGazeEvent.csv')):
            continue

        with open(os.path.join(path, file)) as f:
            print("Openning "+ file)
            suffix = file.split("_")[0]
            userID =  int(suffix.split("player")[1])
            csv = pd.read_csv(f, header= 0) 
            data = { 'id' : userID,
                    'AreaName':   csv['AreaName'],
                     'ParentName': csv['ParentName'],
                     'GazeObject':   csv['GazeObject'],
                    'startKeyframe':  csv['startKeyframe'], 
                    'endKeyframe':  csv['endKeyframe'], 
                    'duration':  csv['duration'], 
                     }
            
            
            if(df.shape[0] == 0 ):
                df = pd.DataFrame(data)
                
            else:
                new_df = pd.DataFrame(data)
                df = pd.concat([df,new_df], ignore_index= True)

    return df

