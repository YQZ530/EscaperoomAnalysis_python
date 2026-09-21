
import os
import pandas as pd
os.environ["OMP_NUM_THREADS"] = "1"

from sklearn.cluster import KMeans
import numpy as np

from sklearn.preprocessing import normalize, StandardScaler
from tslearn.clustering import TimeSeriesKMeans
from sklearn.decomposition import PCA

from SSC_algo.cluster.selfrepresentation import ElasticNetSubspaceClustering
from sklearn import cluster
import time

from Util import printArr

def ResizeAndInterpolate2(max_frames, plyr_skeleton):

        final_pose = None
       
        if len(plyr_skeleton) < max_frames:
            # Calculate interpolation indices
            indices = np.linspace(0, len(plyr_skeleton) - 1, max_frames)
            #print(f"max z coor = { max(np_plyr_pos[:, 2]) }")
            # Perform interpolation for X, Y, Z coordinates separately
            x_interp = np.interp(indices, np.arange(len(plyr_skeleton)), plyr_skeleton[:, 0])
            y_interp = np.interp(indices, np.arange(len(plyr_skeleton)), plyr_skeleton[:, 1])
            z_interp = np.interp(indices, np.arange(len(plyr_skeleton)), plyr_skeleton[:, 2])
        
            # Combine interpolated values into a new pose
            
            interpolated_pose = np.column_stack((x_interp, y_interp, z_interp))
            final_pose = interpolated_pose
                
        else:
            final_pose = plyr_skeleton

       
        
        return final_pose

def Method_CovarianceMatrix2(data, numJoint, uppTriLen):
    N = len(data)
    numFrames = len(data[0])
    print(f"num sample is {N} numJoint {numJoint} uppTriLen {uppTriLen} numFrames = {numFrames}")
    print(f"final upper matric size  {uppTriLen} per sample")
    final = np.zeros((N,  uppTriLen))

    for i in range(data.shape[0]): # for all player
        plyr_pos = data[i]

        #construct S, each row represents a variable, with observations in the column.
        # S = should has size (3XJ, T)
        S = plyr_pos.T
        if(S.shape != (numJoint*3, numFrames)):
            print(f"[error] S.shape is not (3XJ, numFrames); it is{ S.shape}")
        #
        C = np.cov(S, rowvar= True) # C should have 3J X 3J size
        if(C.shape != (3*numJoint, 3*numJoint) ):
            print(f"[error] covariance matrix size not 3J X 3J; size is{ C.shape }")
        upper_triangular  = C[np.triu_indices(C.shape[0])] 
        
        normalized_data = normalize(upper_triangular.reshape(1, -1), norm='max', axis=1)
        #print(f"upper_triangular ={upper_triangular } \n normalized={normalized_data}")
        #print( f"normalized_data {len(normalized_data)} {len(normalized_data[0])} " )
        final[i] =  normalized_data

    return final, C

def ConstructTrainingSet2(dataset, startFrames, endFrames):
    def GetMaxFrame():
        max_frame = 0
        for userID in dataset['userID']:
            start = startFrames[(startFrames['userID'] == userID)]['startFrame'].values[0]
            end = endFrames[(endFrames['userID'] == userID)]['endFrame'].values[0]
            max_frame = (end-start +1) if max_frame <  (end-start +1) else max_frame
        
        return max_frame
    #max_frames = max(len(plyr) for plyr in dataset['plyr_pos'])
    max_frame =  GetMaxFrame()
    print(f"max frame for all players is {max_frame}")
    J = 3
    players_ske = []
    for userID in dataset['userID']:
        start = startFrames[(startFrames['userID'] == userID)]['startFrame'].values[0]
        end = endFrames[(endFrames['userID'] == userID)]['endFrame'].values[0]
        df = dataset[(dataset['userID'] == userID)]
        j1 = np.array(df['plyr_pos'].values[0])  # (frame,3)
        j2 = np.array(df['l_hand_pos'].values[0])
        j3 = np.array(df['r_hand_pos'].values[0])


        tj1 = j1[start:end][:]
        tj2 = j2[start:end][:]
        tj3 = j3[start:end][:]


        fj1= ResizeAndInterpolate2(max_frame,tj1)
        fj2= ResizeAndInterpolate2(max_frame,tj2)
        fj3= ResizeAndInterpolate2(max_frame,tj3)
        if(fj1.shape[0] != max_frame):
            print(f"[Error] final should has ({max_frame}, numjoints)" )
    #     print( f"j1x{j1[0][0]} j2x{j2[0][0]} j3x{j3[0][0]  }")
        skeleton =  np.column_stack((fj1,fj2,fj3))
        #print(skeleton.shape)
        #print(skeleton[0][:9])
        players_ske.append(skeleton)

    players_ske = np.array(players_ske)
    #construct covariance Matrix
    diagnoal_len = int(3*J * (3*J +1)/2) 
    X_train, C = Method_CovarianceMatrix2(players_ske, J, diagnoal_len)
    return X_train, C 


def GetPoseData(df):

    J = 3
    raw_pos = [df['plyr_pos'].values, df['l_hand_pos'].values,df['r_hand_pos'].values]
    #pose_data = PreprocessingData(J, raw_pos, frameToSkip)
def GetOtherFeatureArr(feature_dict):
    arr = []
    for feature in feature_dict:
        if(feature == "WalkPath"):
            continue
        if(feature_dict[feature]):
            if(feature== "NumCoinsCollected" or
                feature== "NumBombHit" or
                feature== "NumTreasureCollected"
              ):
               arr+= ["nor" +feature] 
            else:
                arr+= [feature]
                
    printArr(arr,"feature to do" )

    return arr
def AppendFeature(df, columns, X_train):
    if(columns == []): 
        return X_train
    for col in columns:
        extraFeature = df[col].astype(float).to_numpy()
        #print(f"before={extraFeature}")
        if(col == 'RatingA' ):
            extraFeature = extraFeature/ 7
        elif(col == 'GameplayDur' or col == 'NumObstaclesHit'):
            extraFeature = np.interp(extraFeature, (extraFeature.min(), extraFeature.max()), (0,1))
        else:
            a = 1 # dummy line
            
            # print(f"after={extraFeature}")
            

        extraFeature = extraFeature.reshape(-1,1)
        if(X_train is None):
            scaler = StandardScaler()
            # if walk path not present in traning dataset, then we need to standard inpt to avoid zeros
            X_train =  scaler.fit_transform(extraFeature)
            
        else:

            X_train = np.concatenate((X_train, extraFeature), axis = 1)
   
    return X_train
    
def RunHDBSCANCluster(X_train, minSample =3, minClusterSize = 2):
    #https://scikit-learn.org/stable/modules/generated/sklearn.cluster.HDBSCAN.html#
    hdbscan = cluster.HDBSCAN(
            # #samples in a neighborhood for a point to be considered as a core point
            min_samples=minSample,
            # min # samples in a group for that group to be considered a cluster; 
            min_cluster_size=minClusterSize,
            store_centers = "centroid",
        )
    #hdbscan.c
    y_predit = hdbscan.fit_predict(X_train)
    return y_predit

def RunKMeanCluster(X_train, numcluster):
    model = TimeSeriesKMeans(n_clusters=numcluster, metric="dtw",
                            max_iter=200, random_state=1)
    y_predit = model.fit_predict(X_train)
    
    return y_predit, model.cluster_centers_.ravel()

def RunElasticNetSSC(X_train, numcluster):

    elastic_model = ElasticNetSubspaceClustering(n_clusters=numcluster,algorithm='lasso_lars',gamma=50)
    elastic_model.fit(X_train)
    return elastic_model.labels_

def ObtainSelectRangeDiscreteData(startChunk, endChunk, maxUser, chunk_database):
    filter_database = chunk_database[(chunk_database['chunkType'] >= startChunk ) & (chunk_database['chunkType'] <= endChunk)]
    
    df = pd.DataFrame(columns = ['userID','GameplayDur' ,'NumCoinsCollected', 'NumBombHit', 
                        'NumObstaclesHit','NumTreasureCollected',
                         'norNumCoinsCollected','norNumBombHit', 'norNumTreasureCollected',])
    for userID in range(maxUser):

        numCoinsCollected = filter_database[(filter_database['userID'] == userID) ]['numCoinsCollected'].sum()
        numBombHit = filter_database[(filter_database['userID'] == userID) ]['numBombHit'].sum()
        numObstaclesHit= filter_database[(filter_database['userID'] == userID) ]['numObstaclesHit'].sum()
        numTreasureCollected = filter_database[(filter_database['userID'] == userID) ]['numTreasureCollected'].sum()

        numCoinsHave = filter_database[(filter_database['userID'] == userID) ]['numCoinsHave'].sum()
        numBomb = filter_database[(filter_database['userID'] == userID) ]['numBomb'].sum()
        numTreasureHave = filter_database[(filter_database['userID'] == userID) ]['numTreasureHave'].sum()
        
        normNumCoinsCollected = numCoinsCollected/ numCoinsHave if numCoinsHave !=0 else 0
        norNumBombHit =  numBombHit/ numBomb if numBomb !=0 else 0
        norNumTreasureCollected = numTreasureCollected/ numTreasureHave if numTreasureHave !=0 else 0

        GameplayDur = filter_database[(filter_database['userID'] == userID) & (filter_database['chunkType'] == endChunk)]['endFrame'].astype(int).iloc[0]/30.0
       
        data = {
            "userID": [userID],
            'GameplayDur':[GameplayDur],
            "NumCoinsCollected": [numCoinsCollected],
            "NumBombHit": [numBombHit],
            "NumObstaclesHit": [numObstaclesHit],
            "NumTreasureCollected": [numTreasureCollected],

            'norNumCoinsCollected':[normNumCoinsCollected],
            'norNumBombHit':[norNumBombHit],
            'norNumTreasureCollected':[norNumTreasureCollected],
     
        }
        # Create a DataFrame from the data dictionary
        new_df = pd.DataFrame(data)
        
        # Concatenate the new data to the existing DataFrame
        df = pd.concat([df, new_df], ignore_index=True)
    return df


class Cluster:
    def __init__(self, player_database, chunk_database, maxUser):
        self.player_database = player_database
        self.chunk_database = chunk_database
        self.clusterSetting = None
        self.maxUser= maxUser

    def RunClusterMain(self, clusterSetting):
        self.clusterSetting = clusterSetting
        player_dataset = self.player_database
        chunk_database=  self.chunk_database

        numcluster = int(self.clusterSetting['NumCluster']) 
        startChunk = int(self.clusterSetting['startChunk']) 
        endChunk = int(self.clusterSetting['endChunk']) 
        min_PlayerPerCluster = int(self.clusterSetting['Min_PlayerPerCluster'])
        features = self.clusterSetting['Features'] #get feature


        discrete_df = ObtainSelectRangeDiscreteData(startChunk, endChunk, self.maxUser,chunk_database)
        
        #initialization
        X_train = None
        

        sdf = chunk_database[chunk_database['chunkType'] == startChunk]
        startFrames = sdf[['userID', 'startFrame']]
        sdf = chunk_database[chunk_database['chunkType'] == endChunk]
        endFrames = sdf[['userID','endFrame']]
        if(features['WalkPath']):
            X_train, C = ConstructTrainingSet2(player_dataset, startFrames, endFrames)
        
        #print(X_train)
        #print(X_train.head())
        extraFeature = GetOtherFeatureArr(features)
        X_train = AppendFeature(discrete_df, extraFeature, X_train)
        #print(X_train)
       
        
        #print("num cluster =" + numcluster)

        y_predit = None
        if(clusterSetting['Pose_Algo'] == "ElasticNet"):
            y_predit = RunElasticNetSSC(X_train, numcluster)
            print("Run ElasticNet")
        elif(clusterSetting['Pose_Algo'] =="KMean" ):
            y_predit,_ = RunKMeanCluster(X_train, numcluster)
            print("Run Kmean")
        else: #
            y_predit = RunHDBSCANCluster(X_train, 3, min_PlayerPerCluster)
            print("Run HDBSCAN")
        
        
        
        discrete_df['GroupID'] = y_predit
        #columns = ['userID','GroupID'] + extraFeature

        # Save the updated CSV file
        #final_df = discrete_df[columns]
        #final_df.to_csv('C:/Users/z5308/Desktop/VRTestingProject/data/Reflex_data/simple_3joints/FinalInfo.csv', index=False)
        
        discrete_df.to_csv('C:/Users/z5308/Desktop/VRTestingProject/data/Reflex_data/simple_3joints/SelectedAggregateData.csv', index=False)
        time.sleep(1)
        return "cluster-"+str(numcluster)