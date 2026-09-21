
import os
import pandas as pd
from ast import literal_eval
import re

#for userName in userNames:
def get_turn_number(s:str):
    return int(s.split('-turn')[1].split('-')[0])
def getArrFromCsv(data):
    if(data is None):
        return []
    return [r  for r in data.apply(literal_eval).values if r is not None ]

def LoadAllUsers(maxUser, path):
    df = pd.DataFrame(columns = ['userID', 'levelDiff', 'turn',
            'plyr_pos', 'plyr_rot', 'cam_pos', 'cam_rot', 
            'DifficultyRating', 'scariness_rating', 'FunRating'
            'GameplayResult','GameplayDur'])

    for userID in range(maxUser):
   
        new_df = LoadFileForUser(userID, df, path)
        df = new_df
    return df


def LoadFileForUser(userID, df:pd.DataFrame, path):
    userName = 'user'+ str(userID) #userNames[userID]
    if(path is not None):
        path += userName+'/'
    else:
        path = 'C:/Users/z5308/Desktop/VRTestingProject/data/all/' +userName+'/'
    files = os.listdir(path)
    files = sorted(files, key=get_turn_number) 
    #print(f"files {files} ")
   
    for file in files:
        print("Openning "+ file)
       
        with open(os.path.join(path, file)) as f:
                
            file_parts = file.split("-")
            turn = int(re.search(r'\d+', file_parts[1]).group()) 
            levelDiff = int(re.search(r'\d+', file_parts[2]).group()) 

            csv = pd.read_csv(f, header= 0) 
           
            
            data = {'userID': userID, 'levelDiff':levelDiff, 
                     'turn':turn,
                    'plyr_pos':   getArrFromCsv (csv['plyr_pos']), 
                    'plyr_rot': getArrFromCsv(csv['plyr_rot']), 
                    'cam_pos': getArrFromCsv (csv['cam_pos']), 
                    'cam_rot': getArrFromCsv(csv['cam_rot']),  #[csv['cam_rot'].values], 
                    'DifficultyRating': csv['difficulty_rating'].values[0], 
                    'ScarinessRating': csv['scariness_rating'].values[0], 
                    'FunRating': csv['fun_rating'].values[0] ,
                    'GameplayResult': csv['result'].values[0],
                    'GameplayDur':csv['duration'].values[0],
                     },
            
            #print(f"df shape before apend{df.shape}")

            if(df.shape[0] == 0 ):
                df = pd.DataFrame(data)
                
            else:
                new_df = pd.DataFrame(data)
                df = pd.concat([df,new_df], ignore_index= True)
    
   
    return df



def LoadEventFile():
    
    df = pd.DataFrame(columns = ['Event', 'userID', 'levelDiff', 'turn','startKeyframe','endKeyframe', 'dur'])
    path = 'C:/Users/z5308/Desktop/VRTestingProject/data/all/event.csv' 
    
    with open(path) as f:
        
        csv = pd.read_csv(f, header= 0) 

        data = {'userID': csv['userID'].values[0], 
                'levelDiff':csv['levelDiff'].values[0], 
                'turn':csv['turn'].values[0], 
                'event':csv['event'].values[0],
                'startKeyframe':csv['startKeyframe'].values[0],
                'endKeyframe':csv['endKeyframe'].values[0],
                'dur':csv['dur'].values[0],
                },
        
        #print(f"df shape before apend{df.shape}")

        if(df.shape[0] == 0 ):
            df = pd.DataFrame(data)
            
        else:
            new_df = pd.DataFrame(data)
            df = pd.concat([df,new_df], ignore_index= True)
    
    
    return df


