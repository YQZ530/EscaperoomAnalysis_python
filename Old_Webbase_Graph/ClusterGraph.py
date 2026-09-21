from enum import IntEnum
from plotly.subplots import make_subplots
import pandas as pd
from typing import List, Tuple
import plotly.graph_objs as go
from sklearn.cluster import KMeans
from scipy.signal import find_peaks
import numpy as np

class basicAlgorithm(IntEnum):
    Avg = 0
    Std =1
    Median =2
    NumPeak =3



def ConstructDF(maxLevel, graphSetting, df):
       
        N_cluster = graphSetting['clusterAlgSetting']['N_cluster']
        feature_alg_pairs = [ (item['name'], basicAlgorithm(item['method']))  for item in graphSetting["GraphSetting"]]
        cluster_df, colNameArr = constructDFHelper(maxLevel, df,feature_alg_pairs )

        return N_cluster,cluster_df, colNameArr

def FindPeak(arr):
    
    peaks, properties  = find_peaks(arr, distance=30, height=1)
    #peak_yloc =[arr[p] for p in peaks]

    return peaks, len(peaks)
def CalHeadRot(headArr, skip:int):
    head = headArr[::skip]
    angleDiff = []
    for frame in range(1, len(head)):
        angle = np.abs(head[frame][1] - head[frame -1][1]) 
        angleDiff += [angle]
    
    return angleDiff
#based on  algorithm type, run algo on dataset

def Calculator(df, colName, selectedLevel:int, algorithm: basicAlgorithm):
    result = 0
    if(colName == "sucessRate"):
        tot = (df['levelDiff'] == selectedLevel).sum()
        count =   ((df['GameplayResult'] > 0) &  (df['levelDiff'] == selectedLevel)).sum()
        result = count /tot; 
        result = round(result, 2)
       
    elif(colName == "playerRot"):
        filtered_df= df[df['levelDiff'] == selectedLevel]
        results = []
        for index, row in filtered_df.iterrows():
            userID = row['userID']
            turn = row['turn']
            headRotArr = CalHeadRot(row['plyr_rot'], 20)
            headRot_df = pd.DataFrame(headRotArr)

            if(algorithm == basicAlgorithm.Avg):
                results += [headRot_df.mean()[0]]
            elif(algorithm == basicAlgorithm.Median):
                results += [headRot_df.median()[0]]
            elif(algorithm == basicAlgorithm.Std):
                results += [headRot_df.std()[0]]
            else:
                _, numPeak = FindPeak(headRotArr)
                results += [numPeak]
            #print(f"{userID} ::{headRot_df.mean()[0]}")
        result = pd.DataFrame(results).mean()[0] 
        
        # print(f"  palyerRot::{result}")
        
    else:
        
        
        filtered_df= df[df['levelDiff'] == selectedLevel]
        if(algorithm == basicAlgorithm.Avg):
            result = filtered_df[colName].mean()
        elif(algorithm == basicAlgorithm.Median):
            result = filtered_df[colName].median()
        else:
            result = filtered_df[colName].std()
    
    result = round(result, 2)
    return result


def constructDFHelper(maxLevel, df, feature_alg_pairs: List[ Tuple[str, basicAlgorithm]]):
    #colArr = [pair[0]  for pair in feature_alg_pairs] + ["level"]
    colNameArr =[ f"{pair[1].name}_{pair[0]}"  for pair in feature_alg_pairs]
    # level_df = pd.DataFrame(columns= colArr)
    level_df = pd.DataFrame({})
    count = 0

    resultArr = []

    for level in range(maxLevel):
        #calculated success rate
        new_data = {}
        for pair in feature_alg_pairs:
            featureName = pair[0]
            method = pair[1]
        
            key = f"{method.name}_{featureName}"
            new_data[key] = Calculator(df, featureName, level, method)
        
        new_df = pd.DataFrame([new_data])

        level_df = pd.concat([level_df, new_df], ignore_index = True)
        

    return level_df, colNameArr

def RunKmeanCluser(num_clusters: int, level_df, colNameArr):
    model = KMeans(n_init = 'auto', n_clusters=num_clusters)
    #arr = level_df[['successRate', 'avgDur', 'avg_diffRating']]
    arr = level_df[[ item for item in colNameArr]]
    
    model.fit(arr)
    predict = model.predict(arr) 
    level_df['ClusterGroup'] = predict

    return level_df,'ClusterGroup'

class ClusterGraph:
    def __init__(self):
        pass
       
  
    
    def CreateClusterGraph(self, df, colNameArr, predictedColName, graphSetting):
      
        hoverTextName = [ f"level{x}"  for x in range( df.shape[0] )]
        trace = None
        fig =  make_subplots(
            rows=2, cols=1,
            shared_xaxes=False,
            vertical_spacing=0.1,
            specs=[
                [{"type": "scatter3d"}] if len(colNameArr) >2 else [{"type": "scatter"}],
                [{"type": "table"}]]
            )
        
        if(colNameArr is None or len(colNameArr) <1):
            print("[Error] colName Arr is empty")
            return
        print(df[colNameArr])
        
        mainTitle = graphSetting['mainTitle']
        xTitle = graphSetting['xTitle']
        yTitle = graphSetting['yTitle']
        zTitle = None if 'zTitle' not in graphSetting else graphSetting['zTitle']
       
        if(len(colNameArr) == 1):
            trace = go.Scatter(   
                        x = df.index,
                        y = df[colNameArr[0]],
                        mode='markers+text',
                        marker=dict(size=10, color= df[predictedColName], colorscale = 'Picnic'),
                        visible=True,
                        text = hoverTextName,
                        hovertemplate='xTitle'+ '=%{x}<br>' + yTitle + '=%{y}<br>'+ '%{hovertext}',
                        hovertext = hoverTextName )
        elif(len(colNameArr) == 2):
            trace =  go.Scatter( 
                        x = df[colNameArr[0]] ,
                        y = df[colNameArr[1]],
                        text = hoverTextName,
                        mode='markers+text',
                        marker=dict(size=10, color= df[predictedColName], colorscale = 'Picnic'),
                        visible=True,
                        hovertemplate='xTitle'+ '=%{x}<br>' + yTitle + '=%{y}<br>'+ '%{hovertext}',
                        hovertext = hoverTextName ) 
        else:
            trace =  go.Scatter3d( 
                        x = df[colNameArr[0]] ,
                        y = df[colNameArr[1]],
                        z = df[colNameArr[2]],
                        text = hoverTextName,
                        mode='markers+text',
                        marker=dict(size=10, color= df[predictedColName], colorscale = 'Picnic'),
                        visible=True,
                        hovertemplate=xTitle+ '=%{x}<br>' + yTitle 
                                + '=%{y}<br>'+zTitle+ ' =%{z}<br>'+ '%{hovertext}',
                        hovertext = hoverTextName )

        fig.add_trace(trace, row=1, col=1)
        if(len(colNameArr) <3):
            fig.update_layout(
                    title= mainTitle,
                    xaxis=dict(title=xTitle),
                    yaxis=dict(title=yTitle),
                    width = 600,
                    )
        else:
            fig.update_layout(
                    title= mainTitle,
                    scene=dict(
                    xaxis=dict(title=xTitle),
                    yaxis=dict(title=yTitle),
                    zaxis= dict(title = zTitle)),
                    width = 900,
                    height = 800,
                    )
        df['LevelIdx'] = df.index
        table = go.Table(
            header=dict(values=df.columns,
                        fill = dict(color='#C2D4FF'),
                        align = ['left'] * 5),
            cells=dict(values=[df[col] for col in df.columns],
                    fill = dict(color='#F5F8FF'),
                    align = ['left'] * 5))

    

        fig.add_trace(table, row=2, col=1)


        def Construct_buttons(df):
            buttons = []
            for selCol in  df.columns:
                button = dict(
                    label= f'sort by {selCol}',
                    method="restyle",
                    args=[dict(
                        cells = { "values":  [df.sort_values(by = selCol)[col] for col in  df.columns]}
                    )],
        
                )
                buttons.append(button)
        
            return buttons
        tableLayout = go.Layout(
            #title = "User Performance",
            updatemenus=[
            {
                'buttons' : Construct_buttons(df),
                'direction': 'down',
                'showactive': True,
                'x': 0,
                'xanchor': 'left',
                'y':0.5,
                'yanchor': 'top'
            },
        ]
        )
        fig.update_layout(tableLayout) 

        return fig