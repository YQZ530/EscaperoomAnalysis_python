import json
import time
import pandas as pd
from sgt import SGT
import numpy as np
from itertools import chain
from Util import alphabet
from sklearn.decomposition import PCA
import kmedoids
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import euclidean_distances
from sklearn.cluster import AgglomerativeClustering
from scipy.spatial.distance import directed_hausdorff
from sklearn.metrics import silhouette_score

import csv
from sklearn.preprocessing import StandardScaler
from enum import Enum
from scipy.spatial.distance import cdist

class  EyeGazeClusterMetric(Enum):
    Euclidean =1,
    HausdorffDist =2,
        
    
class  EyeGazeClusterAlgor(Enum):
    KMean =1,
    PAM =2,
    Agglomerative =3,


def RenamePass(df):
    # change gaze Object only
    def RenamePass2(df):
        mask = df['GazeObject'].isin(['LoungeChair'])
        df.loc[mask, 'GazeObject'] = 'LoungeChairModel'

        mask = df['GazeObject'].isin(['LongTable'])
        df.loc[mask, 'GazeObject'] = 'LongTableModel'

    RenamePass2(df)
    objs = ['RedOfficeChair']
    mask = df['ParentName'].isin(objs)
    df.loc[mask, 'ParentName'] = 'ChairGroup'

    # shelf
    gaze_objects_to_check = ['ShelfSlot1', 'ShelfSlot2', 'ShelfSlot3', 'ShelfSlot4', 'ShelfSlot5', 'ShelfSlot6',
                             'Bookshelf']
    mask = df['ParentName'].isin(gaze_objects_to_check)
    df.loc[mask, 'ParentName'] = 'UpperShelf'

    objs = ['ShelfSlot7', 'ShelfSlot8', 'ShelfSlot9', 'BookshelfDrawer1', 'BookshelfDrawer2', 'BookshelfDrawer3']
    mask = df['GazeObject'].isin(objs)
    df.loc[mask, 'ParentName'] = 'LowerShelf'
    mask2 = df['ParentName'].isin(objs)
    df.loc[mask2, 'ParentName'] = 'LowerShelf'

    # cabin
    mask = df['ParentName'].isin(['Cabin'])
    df.loc[mask, 'ParentName'] = 'LowerCabin'

    objects_to_check = ['GothicCabinetDoor3', 'GothicCabinetDoor4']
    mask = df['GazeObject'].isin(objects_to_check)
    df.loc[mask, 'ParentName'] = 'LowerCabin'

    objects_to_check = ['SmallCabinetDrawer1', 'SmallCabinetDrawer2', 'SmallCabinetDrawer3']
    mask = df['GazeObject'].isin(objects_to_check)
    mask2 = df['ParentName'].isin(objects_to_check)
    df.loc[mask, 'ParentName'] = 'LoungeChair'
    df.loc[mask2, 'ParentName'] = 'LoungeChair'

    mask = df['ParentName'].isin(['OfficeSet'])
    df.loc[mask, 'ParentName'] = 'OfficeDeskSurface'

    # if gaze object is [objects_to_check], then change its parent name
    objects_to_check = ['OfficeTableDrawer1', 'OfficeTableDrawer2', 'OfficeTableDrawer3', 'Key5']
    mask = df['GazeObject'].isin(objects_to_check)
    mask2 = df['ParentName'].isin(objects_to_check)
    df.loc[mask, 'ParentName'] = 'OfficeTableDrawer'
    df.loc[mask2, 'ParentName'] = 'OfficeTableDrawer'

    # long table area
    mask = df['ParentName'].isin(['LongTable', 'ChargingStation'])
    df.loc[mask, 'ParentName'] = 'LongTableSurface'


# add event type to gazedf
def EventPass(gazedf, eventdf):
    gazedf['eventType'] = None  # Initialize the new column

    # Group events by user for efficient lookup
    events_by_user = eventdf.groupby('id')

    for user_id, user_gaze_df in gazedf.groupby('id'):
        if user_id in events_by_user.groups:
            user_events = events_by_user.get_group(user_id)

            for _, event_row in user_events.iterrows():
                event_start = event_row['startFrame']
                event_end = event_row['endFrame']
                event_type = event_row['eventType']

                # Condition 1: gaze interval is within event interval
                # (gaze_start >= event_start AND gaze_end <= event_end)
                condition1 = (user_gaze_df['startKeyframe'] >= event_start) & \
                             (user_gaze_df['endKeyframe'] <= event_end)

                # Condition 2: gaze interval starts within event, but ends after event
                # (gaze_start >= event_start AND gaze_start <= event_end AND gaze_end > event_end)
                condition2 = (user_gaze_df['startKeyframe'] >= event_start) & \
                             (user_gaze_df['startKeyframe'] <= event_end) & \
                             (user_gaze_df['endKeyframe'] > event_end)

                # Apply the event type to rows satisfying either condition
                # We use .loc for safe assignment to a slice of the DataFrame
                gazedf.loc[user_gaze_df.index[condition1 | condition2], 'eventType'] = event_type

    return gazedf

def Filter_events(df, minDur):
    t = df[df['duration'] >= minDur]
    return t


def Merge_events_ObjMerge(df):
    merged_data = []
    pre_chunk_data = None

    for i, row in df.iterrows():
        if pre_chunk_data is None:
            pre_chunk_data = row
        else:
            # If the `chunkName` is the same as the previous one, merge them
            if pre_chunk_data['id'] == row['id'] and pre_chunk_data['AreaName'] == row['AreaName'] and pre_chunk_data[
                'ParentName'] == row['ParentName']:
                pre_chunk_data['endKeyframe'] = row['endKeyframe']
                pre_chunk_data['duration'] += row['duration']
                pre_chunk_data['GazeObject'] = str(pre_chunk_data['GazeObject']) + "," + str(row['GazeObject'])
            else:
                # Append the completed chunk and start a new one
                merged_data.append(pre_chunk_data)
                pre_chunk_data = row

    # Don't forget to append the last chunk
    if pre_chunk_data is not None:
        merged_data.append(pre_chunk_data)

    return pd.DataFrame(merged_data)


def ExtractUniqueAreaName(df):
    # Replace "[env]" with "Wall" in the 'AreaName' column
    df['AreaName'] = df['AreaName'].replace('[Env]', 'Wall')
    df['ParentName'] = df['ParentName'].replace('[Env]', 'Wall')

    parent_names = df['ParentName'].unique().tolist()
    area_name = df['AreaName'].unique().tolist()
    return parent_names, area_name

#################
def AddAreaCode(df_original, isAreaOnly, areaNameList, parentNameList):
    df = df_original.copy() 
    df.loc[:, 'AreaCode'] = None 
    #encode chunk and chunkobj
    for uid, row in df.iterrows():
        AreaName = row['AreaName']
        ParentName = row['ParentName']
        code = None
        if(isAreaOnly):
            code =   str(alphabet[areaNameList.index(AreaName)]) 
        else:
            code =   str(alphabet[areaNameList.index(AreaName)]) +str(parentNameList.index(ParentName))
        df.at[uid, 'AreaCode'] = code
    return df
def ConsturctFeatureSeq(df):
    tpd = pd.DataFrame(columns=['id', 'sequence'])  # initialize a new frame

    idList = df['id'].unique()
    for i in range(len(idList)):
        uid = idList[i]
        AreaSeq = df[(df['id'] == uid)]['AreaCode'].tolist()
        # find target user, then combine corresponding chunk into list
        row = pd.DataFrame({'id': uid, 'sequence': [AreaSeq]})
        tpd = pd.concat([tpd, row], ignore_index=True)

    seen = set()
    Area_alphabets = list(filter(lambda x: not (x in seen or seen.add(x)),
                                 chain.from_iterable(tpd['sequence'])))
    print(tpd)
    print(f"encoded select area and  parent obj into alphabet {Area_alphabets};\n   return sequence shape {tpd.shape}")

    # sample X sequence(list)
    return tpd, Area_alphabets
def AddExtraFeatureToSeq(df, sequence_df, featNameArr):
    tpd = pd.DataFrame(columns=['id', 'duration'])

    idList = df['id'].unique()
    for i in range(len(idList)):
        uid = idList[i]
        dur = np.array(df[df['id'] == uid]['duration'])
        sumDur = dur.sum()
        stdDur = dur.std()
        avgDur = dur.mean()
        numFixation = len(dur)
        mdict = {}
        # add feature related data to dataframe, then normalize it and add to sequence df
        for feature in featNameArr:
            if (feature == "SumDur"):
                mdict['SumDur'] = sumDur
            if (feature == "StdDur"):
                mdict['StdDur'] = stdDur
            if (feature == "AvgDur"):
                mdict['AvgDur'] = avgDur
            if (feature == "NumFixation"):
                mdict['NumFixation'] = numFixation

        mdict['id'] = uid
        mdict['duration'] = [dur]
        row = pd.DataFrame(mdict)
        tpd = pd.concat([tpd, row], ignore_index=True)
    # normalized feature  name
    # normalized value and put that to df
    nfeatureArr = [str('n') + feature for feature in featNameArr]
    scaler = StandardScaler()
    if (len(featNameArr) != 0):
        X_normalized = scaler.fit_transform(tpd[[feature for feature in featNameArr]])
        array_df = pd.DataFrame(X_normalized, columns=nfeatureArr)
        tpd = pd.concat([tpd, array_df], axis=1)

    # merge with sequence df
    tpd = pd.merge(tpd, sequence_df, on='id', how='left')
    return tpd, nfeatureArr

######################

def ConvertSequenceToEmbedding(sequence_df, chunk_alphabets):
    
    sgt_ = SGT(kappa=5, alphabets=chunk_alphabets, flatten=True,
            lengthsensitive=True, mode='default')
   
    
    sgtembedding_df = sgt_.fit_transform(sequence_df)
  
    
    print(f"Convert sequence into Embedding; return df num_sampels X embedding_dimension = {sgtembedding_df.shape}")
    return sgtembedding_df

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


def decode_AreaCode(sequence_array, alphabet, areaNameList, parentNameList):
    area_names = []
    parent_names = []
    for encoded_string in sequence_array:
        try:
            # Assuming the first character is the index for alphabet (AreaName)
            # and the remaining characters are the index for parentNameList (ParentName).
            # This assumes that the index for alphabet is always a single digit.
            # If alphabet can have 10 or more items, you'll need a more robust parsing strategy.
            area_char = encoded_string[0]
            parent_index_str = encoded_string[1:]

            rea_char_index = alphabet.index(area_char)
            area_name = areaNameList[rea_char_index]

            parent_index = int(parent_index_str)
            parent_name = parentNameList[parent_index]

            area_names.append(area_name)
            parent_names.append(parent_name)

        except (ValueError, IndexError) as e:
            print(f"Error decoding '{encoded_string}': {e}. Check your lists and encoding logic.")
        return area_names, parent_names


class EREyeGazeClusters_ER:

    def __init__(self, eyegaze_df, event_df):
        self.eyegaze_df = eyegaze_df
        self.event_df = event_df
        #self.maxUser = maxUser
    def RunClusterMain(self, clusterSetting):    

        #1. load data from json
        tarEvtType = int(clusterSetting['tarEvtType'])

        minFixationDur = int(clusterSetting['minFixation']) # minimum duration to be consider a valid eye fixeation
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


        eyegaze_df = self.eyegaze_df.copy()
        event_df = self.event_df.copy()
        # 1. rename some Gazeobject parent area, then add event type to gaze_df
        RenamePass(eyegaze_df)
        eyegaze_df = EventPass(eyegaze_df, event_df)
        # 2. extra unique name list for areaName and Parent Name
        parentNameList, areaNameList = ExtractUniqueAreaName(eyegaze_df)
        eyegaze_df = Merge_events_ObjMerge(eyegaze_df)

        # 3filter out dur < target, and merge again
        eyegaze_df = Filter_events(eyegaze_df, 50)
        eyegaze_df = Merge_events_ObjMerge(eyegaze_df)

        # 4. select frames only for target event type and convert to AreaCode
        filterdf = eyegaze_df[eyegaze_df['eventType'] == tarEvtType]
        filterdf = AddAreaCode(filterdf, False, areaNameList, parentNameList)
        sequence_df, chunk_alphabets = ConsturctFeatureSeq(filterdf)
        sequence_df,nfeatureArr = AddExtraFeatureToSeq(filterdf, sequence_df,featNameArr)

        # check if Fixation Appear
        sgtembedding_df = None
        hasFixation = any(shouldUse and feature == "Fixation" for feature, shouldUse in feature_config.items())
        if hasFixation:
            temp_df = sequence_df.copy(deep=True)
            # construct segmentation embedding
            sgtembedding_df = ConvertSequenceToEmbedding(temp_df, chunk_alphabets)
            if len(featNameArr) != 0:
                sgtembedding_df = AppendFeatures(sgtembedding_df, sequence_df, nfeatureArr)
            print(f"embedding dataset shape {sequence_df.shape}")

        else:
            sgtembedding_df = AppendFeatures2(sequence_df, nfeatureArr)

        if (sgtembedding_df.shape[1] > 3):
            pca_df, X = Run_PCA(sgtembedding_df, num_PCA_comp)

        else:
            pca_df = sgtembedding_df
            X = sgtembedding_df.copy().drop(columns='id')
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
        for index, row in sequence_df.iterrows():
            uid = row['id']

            selectrow = pca_df[(pca_df['id'] == uid)]
            if not selectrow.empty:
                sequence_df.at[index, 'GroupID'] = selectrow.iloc[0]['GroupID']
            else:
                print("Select row is empty")

        sequence_df['AreaName'] = [[] for _ in range(len(sequence_df))]
        sequence_df['ParentName'] = [[] for _ in range(len(sequence_df))]
        for index, row in sequence_df.iterrows():
            seq_for_user = row['sequence']

            AreaNames, ParentNames = decode_AreaCode(seq_for_user, alphabet, areaNameList, parentNameList)
            sequence_df.at[index, 'AreaName'] = AreaNames
            sequence_df.at[index, 'ParentName'] = ParentNames
        # re-organize sequencedf based on groupID
        for gi in range(-1, nclusters):
            t = sequence_df[(sequence_df['GroupID'] == gi)]
            selectCol = ['id', 'sequence'] + nfeatureArr
            print(f"group = {gi};\n {t[selectCol]}  ")


        featureArr = [feature for feature in featNameArr]
        selectCol = ['id', 'GroupID'] + featureArr + ['AreaName', 'ParentName']
        df2 = sequence_df[selectCol]
        df2 = df2.rename(columns={'id': 'userID'})

        # since df1 is original dataset, it has all users
        # df2 is after filter, some users may not exist in df2
        # fillout NA infor for final df

        for i in range(df2['userID'].count()):
            # if this user does not has a group
            if (df2[df2['userID'] == i].empty):
                df2.loc[df2.shape[0]] = {'userID': i, 'GroupID': -1}

        df2['dummy'] = 0
        # Save the updated CSV file
        df2.to_csv('../EscapeRoomData/FinalEyeGazeGroup.csv', index=False)

        #filterdf.to_csv('../EscapeRoomData/FinalEyeGazeEvent.csv', index=False)
        filterdf.to_csv('../EscapeRoomData/FinalEyeGazeEvent.csv', index=False, quoting=csv.QUOTE_NONNUMERIC)
        time.sleep(1) # give time to save the csv before unity try to open it
        return "eyegaze-"+str(nclusters)

from escaperoom_database import  LoadEyeGazeForUsers2,LoadEventForUsers
def main():
    path = 'C:/Users/Administrator/Desktop/VREscapeRoom/EscapeRoomData'
    eyegaze_df = LoadEyeGazeForUsers2(path)
    event_df = LoadEventForUsers(path)
    eyegaze_cluster =  EREyeGazeClusters_ER(eyegaze_df, event_df)
    clusterSetting = None

    with open("./Setting/ClusterSetting.json") as json_file:
        clusterSetting = json.load(json_file)
        print(clusterSetting["EyeGaze_Metric"])
    result = eyegaze_cluster.RunClusterMain(clusterSetting)
    print("main")
    # print(result)

if __name__ =="__main__":
    main()