import json
import time
import pandas as pd
from sgt import SGT
import numpy as np
from itertools import chain
from Util import alphabet,  chunkObjectList, levelOrder,printArr
from sklearn.decomposition import PCA
import kmedoids
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import euclidean_distances
from sklearn.cluster import AgglomerativeClustering
from scipy.spatial.distance import directed_hausdorff
from sklearn.metrics import silhouette_score
from scipy.spatial.distance import cdist
from sklearn.preprocessing import StandardScaler
from enum import Enum
import re
from typing import List, Tuple

class  EyeGazeClusterMetric(Enum):
    Euclidean =1,
    HausdorffDist =2,
        
    
class  EyeGazeClusterAlgor(Enum):
    KMean =1,
    PAM =2,
    Agglomerative =3,
        
def AddChunkCode(df):
    #encode chunk and chunkobj
    for uid, row in df.iterrows():
        chunkname = row['chunkName']
        chunkobj = row['chunkObject']
        code =   str(alphabet[levelOrder.index(chunkname)]) +str(chunkObjectList.index(chunkobj))
        df.at[uid, 'chunkCode'] = code
    return df

def FilterChunks(df, minDur):
    t = df[df['duration']>= minDur]
    return t
def SelectChunksOfInterest(df, chunkNames):
    t = df[df ['chunkName'].isin(chunkNames)]
    return t

def merge_chunks(df):
    merged_data = []
    pre_chunk_data = None

    for i, row in df.iterrows():
        if pre_chunk_data is None:
            pre_chunk_data = row
        else:
            # If the `chunkName` is the same as the previous one, merge them
            if pre_chunk_data['id'] == row['id'] and pre_chunk_data['chunkName'] == row['chunkName'] and pre_chunk_data['chunkObject'] == row['chunkObject']:
                pre_chunk_data['endKeyframe'] = row['endKeyframe']
                pre_chunk_data['duration'] += row['duration']
            else:
                # Append the completed chunk and start a new one
                merged_data.append(pre_chunk_data)
                pre_chunk_data = row
    
    # Don't forget to append the last chunk
    if pre_chunk_data is not None:
        merged_data.append(pre_chunk_data)

    return pd.DataFrame(merged_data)

def ConsturctChunkSequence(df):

    #print(df.head())
    tpd = pd.DataFrame(columns =  ['id', 'sequence']) # initialize a new frame
    
    idList = df['id'].unique()
    for i in range(len(idList)):
        uid = idList[i]
        chunkSeq =  df[(df['id'] == uid)]['chunkCode'].tolist() # find target user, then combine corresponding chunk into list
        row = pd.DataFrame({'id' : uid, 'sequence' : [chunkSeq] })
        tpd = pd.concat([tpd, row], ignore_index= True)

    seen = set()
    chunk_alphabets = list(filter(lambda x: not (x in seen or seen.add(x)),
                        chain.from_iterable(tpd['sequence'])))
    print(tpd)
    print(f"encoded select chunks and  chunk obj into {chunk_alphabets};\n   return sequence shape {tpd.shape}")
    #tpd['sequence']
    #sample X sequence(list)
    return tpd, chunk_alphabets

#id,duration, featurename arr
def ConstructChunkDurSeq(df, sequence_df,featNameArr):
    tpd = pd.DataFrame(columns =  ['id', 'duration'])
 
    idList = df['id'].unique()
    for i in range(len(idList)):
        uid = idList[i]
        dur =  np.array(df[df['id'] == uid ]['duration'])
        sumDur = dur.sum()
        stdDur = dur.std()
        avgDur = dur.mean()
        numFixation = len(dur)
        mdict = {}
        #add feature related data to dataframe, then normalize it and add to sequence df
        for feature in featNameArr:
            if(feature == "SumDur"):
                mdict['SumDur'] = sumDur
            if(feature == "StdDur"):
                mdict['StdDur'] = stdDur
            if(feature == "AvgDur"):
                mdict['AvgDur'] = avgDur
            if(feature == "NumFixation"):
                mdict['NumFixation'] = numFixation
        
        mdict['id'] = uid
        mdict['duration'] = [dur]
        row = pd.DataFrame(mdict)
        tpd = pd.concat([tpd, row], ignore_index= True)
    
    nfeatureArr = [str('n')+feature for feature in featNameArr] #normalized feature  name
    #normalized value and put that to df
    scaler = StandardScaler()
    if(len(featNameArr) != 0):
        X_normalized = scaler.fit_transform(tpd[[feature for feature in featNameArr]])
        array_df= pd.DataFrame(X_normalized, columns = nfeatureArr )
        tpd = pd.concat([tpd, array_df], axis=1)
    
    #merge with sequence df
    tpd = pd.merge(tpd, sequence_df,  on='id', how='left')
    return tpd,nfeatureArr




def ConvertSequenceToEmbedding(sequence_df, chunk_alphabets):
    
    sgt_ = SGT(kappa=5, alphabets=chunk_alphabets, flatten=True,
            lengthsensitive=True, mode='default')
   
    
    sgtembedding_df = sgt_.fit_transform(sequence_df)
  
    
    print(f"Convert sequence into Embedding; return df num_sampels X embedding_dimension = {sgtembedding_df.shape}")
    return sgtembedding_df

# def AppendFeatures(output_df, dataset_df,nfeatArrName):
    

#     output_df = pd.merge(output_df, dataset_df[nfeatArrName],
#     left_index=True, right_index=True, how = 'left')
    
#     renameguide = {fname: ('c1', fname)  for fname in nfeatArrName }
#     output_df = output_df.rename(columns= renameguide)
#     output_df = output_df.fillna(0)
#     print(f"[AppendFeatures]input dataset shape {dataset_df.shape} output  {output_df.shape}")
#     return output_df
def AppendFeatures(output_df, dataset_df,nfeatArrName):
    if 'id' in output_df.columns and 'id' in dataset_df.columns:
        if output_df.shape[0] < dataset_df.shape[0]:
            print("Warning: output_df has fewer entries than dataset_df, merging might result in data loss.")
    
        # Perform the merge
        output_df = pd.merge(output_df, dataset_df[nfeatArrName], 
                            left_index=True, right_index=True, how='left')
    else:
        print("Error: One or both DataFrames do not have the 'id' column. Merge not performed.")
        return output_df

    renameguide = {fname: ('c1', fname)  for fname in nfeatArrName }
    output_df = output_df.rename(columns= renameguide)
    output_df = output_df.fillna(0)
    print(f"[AppendFeatures]input dataset shape {dataset_df.shape} output  {output_df.shape}")
    return output_df

def AppendFeatures2( dataset_df,nfeatArrName):
    finalCol = ['id'] + nfeatArrName
    
    output_df = dataset_df[finalCol]
    print(f"[AppendFeatures]input dataset shape {dataset_df.shape} output  {output_df.shape}")
    return output_df

def Run_PCA(input_df,num_comp = 5):
    input_df.columns = input_df.columns.astype(str)
    #[Warning] need to drop all other column(e.g., id, duration); left with chunk seq code only 
    sgtembedding_df = input_df.drop(columns = 'id')
    
    pca = PCA(n_components=num_comp)

    #sum of PCA descript how much of total variance is retained after transformation
    X=pca.fit_transform(sgtembedding_df)#X = num_samples X num_comp
    #Check out how much original variance is captured by each principla componnent
    print(f"Run PCA; df numSample {len(X) } X {num_comp} components; \nsum of PCA {np.sum(pca.explained_variance_ratio_)}" )
    pca_df = pd.DataFrame(data=X, columns=['x'+ str(i) for i in range(num_comp)])
    pca_df['id'] = input_df['id'] #adding id col back
    # print("After run PCA")
    # print(pca_df.head())
    return pca_df,X

def Construct_HausdorffDistanceMatrix(X):
    def directed_hausdorff2(u, v, metric1 = 'euclidean'):
        """
        Calculate the directed Hausdorff distance from array1 to array2.
        
        Parameters:
        array1: numpy array of shape (n, 5) - first set of 5D coordinates
        array2: numpy array of shape (m, 5) - second set of 5D coordinates
        
        Returns:
        float: directed Hausdorff distance from array1 to array2
        """
        print("[directed_hausdorff_distance] u=" , u)
        print("[directed_hausdorff_distance] v=" , v)
        # Calculate pairwise distances between all points
        distances = cdist(u, v, metric = 'euclidean')
        
        # For each point in array1, find its minimum distance to any point in array2
        min_distances = np.min(distances, axis=1)
        
        # The directed Hausdorff distance is the maximum of these minimum distances
        dh = np.max(min_distances)
        
        return dh

    def directed_hausdorff1(u, v):
        #u, v must be size 1 X n 
        #print("[directed_hausdorff_distance] directed_hausdorff=" , directed_hausdorff(u, v))
        return max(directed_hausdorff(u, v)[0], directed_hausdorff(v, u)[0])

    distM = np.zeros((len(X),len(X)))
    for i, u in enumerate(X):
        for j, v in list(enumerate(X))[i:]: #i = 0 ->elem (0,0)..(n,n); i =1 -> elem (1,1)..n

            distM[i,j] = directed_hausdorff1(u.reshape(1,-1),v.reshape(1,-1))         
            distM[j,i] = distM[i,j]
    #print(f"construct distance matrix size  {len(distM)} X{len(distM[0])}")
    return distM 
#df contain 
def Construct_KMeanCluster(df, nclusters = 4):
    kmeans = KMeans(n_clusters= nclusters, max_iter =300)
    kmeans.fit(df)
    labels = kmeans.predict(df)
    centroids = kmeans.cluster_centers_
    return labels, centroids


def Construct_AgglomerativeClustering(distM, nclusters = 4):
    cluster = AgglomerativeClustering(n_clusters=nclusters, affinity='precomputed', linkage = 'average');  
    cluster.fit(distM)
    return cluster.labels_, cluster.n_connected_components_

def Construct_Dynmasc(distM,kmax, kmin):
    kmin = 2
    kmax = 5
    dm = kmedoids.dynmsc(distM, kmax, kmin)
    labels = dm.labels
    print("Optimal number of clusters according to the Medoid Silhouette:", dm.bestk)
    print("Medoid Silhouette over range of k:", dm.losses)
    return labels, dm.medoids
#PAM
def Construct_PAM(samples, distM, nclusters = 4):
    # dm = kmedoids.pam_build(distM, nclusters)
    assert distM.shape[0] == distM.shape[1], "distM must be a square matrix"
    assert isinstance(nclusters, int) and 1 <= nclusters <= distM.shape[0], "Invalid nclusters value"
    dm = kmedoids.fastpam1(distM,nclusters)
    labels = dm.labels
    sil_score = silhouette_score(samples, labels)

    print(f'Loss is {dm.loss}; Silhouette Score for K-medoids: {sil_score}')
    return labels, dm.medoids


def GetChunkAndObjFromSequence(sequence_array: List[str]) -> Tuple[List[str], List[str]]:
    chunks = []
    chunkObjs = []
    for item in sequence_array:
        
        # Use regex to split the letter and number (assuming the format is always letter+number)
        match = re.match(r"([A-Z]+)([0-9]+)", item, re.I)
        if match:
            char, num = match.groups()
            # Find the index of the character in the alphabet
            chunk = alphabet.index(char.upper())
            chunkObjIdx =   int(num)
             
        
            chunks.append(levelOrder[chunk])
            chunkObjs.append(chunkObjectList[chunkObjIdx])
    
    return chunks,chunkObjs



class EyeGazeClusters:

    def __init__(self, df, maxUser):
        self.database = AddChunkCode(df)
        self.maxUser = maxUser
    def RunClusterMain(self, clusterSetting):    
        database = self.database
        
        #1. load data from json
        startChunk =int(clusterSetting['startChunk']) 
        endChunk = int(clusterSetting['endChunk'])
        chunkNames = [ levelOrder[i]for i in range(startChunk,endChunk)] 
        minFixationDur = int(clusterSetting['minFixation']) # minimum duration to be consider a valid eye fixeation
        printArr(chunkNames, "selected chunk name")
        num_PCA_comp = 3
        nclusters = int(clusterSetting['NumCluster'])
        clusterAlgo =  clusterSetting['EyeGaze_Algo']
        clusterMetric = clusterSetting['EyeGaze_Metric'] 
        #1b. get feature name from configuration
        feature_config = clusterSetting['EyeGaze_Features']
        isAllFalse = all( not shouldUse for feature, shouldUse in feature_config.items())  
        if(isAllFalse):
            print("[Error] Did not select any feature to group!!")
            return "eyegaze-"+str(0)


        featNameArr = [feature for feature, shouldUse in feature_config.items() if shouldUse and feature != "Fixation"]
        
        
        #preprocessing: filter out user selected chunk, with dur > mindur, merge consecutive chunk together
        df = SelectChunksOfInterest(database, chunkNames)
        df = merge_chunks(df)
        df = FilterChunks(df, minFixationDur)

        if(df['id'].unique().size != database['id'].unique().size):
            s = "[warning]"+"origian database user count " + str(database['id'].unique().size) +"  but filtered database has "+str(df['id'].unique().size)
            print(s)
        #construct other df
        #return selected df =['id', 'sequence']
        selectedChunksequence_df, chunk_alphabets = ConsturctChunkSequence(df)
        #return ['id', 'duration', nfeature_colmns, 'sequence']
        selectedChunksequence_df,nfeatureArr = ConstructChunkDurSeq(df, selectedChunksequence_df,featNameArr)
        
        #check if Fixation Appear
        sgtembedding_df = None
        hasFixation = any(shouldUse and feature == "Fixation" for feature, shouldUse in feature_config.items()) 
        if(hasFixation):
            temp_df = selectedChunksequence_df.copy(deep= True)
            #construct segmentation embedding
            sgtembedding_df = ConvertSequenceToEmbedding(temp_df, chunk_alphabets)
            if(len(featNameArr) != 0):
                sgtembedding_df = AppendFeatures(sgtembedding_df, selectedChunksequence_df,nfeatureArr)
            print(f"embedding dataset shape {selectedChunksequence_df.shape}" )

        else:
            sgtembedding_df = AppendFeatures2(selectedChunksequence_df,nfeatureArr)

        if(sgtembedding_df.shape[1] >3):
            pca_df,X = Run_PCA(sgtembedding_df, num_PCA_comp)
    
        else:
            pca_df = sgtembedding_df
            X = sgtembedding_df.copy().drop(columns = 'id')
            X = X.to_numpy()


        
        distM = None
        if(clusterMetric == EyeGazeClusterMetric.Euclidean.name):
            distM = euclidean_distances(X)
        else:
            distM = Construct_HausdorffDistanceMatrix(X)

        labels = None
        if(clusterAlgo ==  EyeGazeClusterAlgor.Agglomerative.name):
            labels,_ = Construct_AgglomerativeClustering(distM, nclusters)
        elif (clusterAlgo ==  EyeGazeClusterAlgor.KMean.name):
            labels,_ = Construct_KMeanCluster(X, nclusters)
        elif(clusterAlgo ==  EyeGazeClusterAlgor.PAM.name):
            labels,_ = Construct_PAM(X, distM, nclusters)
        else:
            print("Error: cannot identify cluster algo; run Kmean by defalt")
            labels,_ = Construct_KMeanCluster(X, nclusters)

        #adding groupID label back to pca,  then add back to selected chunk seq accordingly
        pca_df['GroupID'] = labels
        for index, row in selectedChunksequence_df.iterrows():
            uid =  row['id'] 
        
            selectrow =  pca_df[(pca_df['id'] == uid)]
            if not selectrow.empty:
                selectedChunksequence_df.at[index, 'GroupID'] = selectrow.iloc[0]['GroupID']
            else:
                print("Select row is empty")
        
        selectedChunksequence_df['chunks'] = [[] for _ in range(len(selectedChunksequence_df))]
        selectedChunksequence_df['chunkObjs'] = [[] for _ in range(len(selectedChunksequence_df))]
        for index, row in selectedChunksequence_df.iterrows():
            flattened_sequence = row['sequence']
            chunks, chunkObjs = GetChunkAndObjFromSequence( flattened_sequence)
            selectedChunksequence_df.at[index,'chunks'] = chunks
            selectedChunksequence_df.at[index,'chunkObjs'] = chunkObjs

        for gi in range(-1, nclusters):
            t = selectedChunksequence_df[(selectedChunksequence_df['GroupID'] == gi)]
            selectCol = ['id','sequence']+ nfeatureArr
            print(f"group = {gi};\n {t[selectCol]}  ") 


       
        featureArr = [feature for feature in featNameArr] 
        selectCol = ['id', 'GroupID'] + featureArr+['chunks', 'chunkObjs']
        
        df2 = selectedChunksequence_df[selectCol]
        df2 = df2.rename(columns={'id': 'userID'})

        #since df1 is original dataset, it has all users
        #df2 is after filter, some users may not exist in df2
        #fillout NA infor for final df
        for i in range(self.maxUser):
            # if this user does not has a group
            if(df2[df2['userID'] == i].empty) :
                df2.loc[df2.shape[0]] = {'userID': i, 'GroupID' : -1}

        
        df2['dummy'] = 0
        #Save the updated CSV file
        df2.to_csv('C:/Users/z5308/Desktop/VRTestingProject/data/Reflex_data/simple_3joints/FinalEyeGazeInfo.csv', index=False)
        
        


        time.sleep(1) # give time to save the csv before unity try to open it
        return "eyegaze-"+str(nclusters)

# def main():
#     # eyegaze_path = "../data/Reflex_data/simple_3joints/otherInfo/"
#     # eyegaze_df = LoadEyeGazeForUsers(eyegaze_path)
#     # eyegaze_cluster = EyeGazeClusters(eyegaze_df)

#     # clusterSetting = None
#     # with open("./Setting/ClusterSetting.json") as json_file:
#     #     clusterSetting = json.load(json_file)
#     #     print(clusterSetting["EyeGaze_Metric"])
#     # result = eyegaze_cluster.RunClusterMain(clusterSetting)
#     print("main")
#     # print(result)

# if __name__ =="__main__":
#     main()