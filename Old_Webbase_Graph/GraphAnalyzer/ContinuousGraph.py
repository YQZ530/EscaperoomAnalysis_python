import pandas as pd
import numpy as np
from enum import Enum
from Util import GetInt, GetSelectedUserRangeData, GetUserRangeFromText
import chart_studio.plotly as py
import plotly.graph_objs as go


from plotly.subplots import make_subplots

class AttributeType(Enum):
        WalkingPath =0
        PlayerRot =1
        WalkDistance = 2
        Velocity =3
        Acceleration =4


def DetermineGraphType(df, userID, turn, levelDiff, showIndexArr):

    trace = None
    traceName =  f'user{str(userID)}_level{levelDiff}_turn{turn}'
    if(len(showIndexArr) == 3):
        trace = go.Scatter3d(
            x = [ pos[0] for pos in df['plyr_pos']],
            y = [ pos[1] for pos in df['plyr_pos']],
            z = [ pos[2] for pos in df['plyr_pos']],
            name = f'{traceName}_walkpath',
        )
        return trace
    elif(len(showIndexArr) == 2):
        firstIndex = showIndexArr[0]
        secondIndex = showIndexArr[1]
        trace = go.Scatter( 
                x = [ pos[firstIndex] for pos in df['plyr_pos']],
                y = [ pos[secondIndex] for pos in df['plyr_pos']],
                legendgroup=f'group_{str(userID)}_turn{turn}',
                name = f'{traceName}_walkpath',
                marker_colorscale = 'Picnic',
                mode='markers',
            )
                
    else: # len <=1 or >3
        print("Error")

    return trace

def PositionGraph(df:pd.DataFrame, fig:go.Figure, rowIdx:int, showIndexArr):
        
        for index, row in df.iterrows():
            
                userID = row['userID']
                levelDiff = row['levelDiff']
                turn = row['turn']
                trace = DetermineGraphType(row, userID, turn, levelDiff, showIndexArr)
                if(trace != None):
                    #fig.add_trace(trace)
                    fig.add_trace(trace, row = 1, col = 1)
                #print(f"{userID}, {turn}")
        return fig, rowIdx+1

def CalHeadRot(headArr, skip:int):
            head = headArr[::skip]
            angleDiff = []
            for frame in range(1, len(head)):
                angle = np.abs(head[frame][1] - head[frame -1][1]) 
                angleDiff += [angle]
            
            return angleDiff

def RotationGraph(df:pd.DataFrame, fig:go.Figure, rowIdx:int, skipFrame:int):

    for index, row in df.iterrows():
            userID = row['userID']
            levelDiff = row['levelDiff']
            turn = row['turn']
            headRotArr = CalHeadRot(row['plyr_rot'], skipFrame)
            trace = go.Scatter( 
                                x = [ i for i in range(len(headRotArr)) ],
                                y =  headRotArr,
                                name =  f'user{str(userID)}_level{levelDiff}_turn{turn}',
                                legendgroup=f'group_{str(userID)}_turn{turn}',
                                marker=dict(size=15, colorscale = 'Picnic'),
                                
                                )
            #print(f"RotationGraph :: rowIdx{rowIdx}")
            fig.add_trace(trace, row = rowIdx, col = 1)
            #fig.add_trace(trace)
    return fig, rowIdx+1
      

def CountNumGraph(graphSetting):
        count = 0
        for graph in graphSetting['GraphSetting']:
            if(graph['Enabled']): 
                count = count +1
        return count

def GetSubplotType(graphSetting):
        typeArr = []
        subplotTittles = []
        for graph in graphSetting['GraphSetting']:
            if(graph['Enabled']): 
                
                subplotTittles.append( f"{graph['graphProperty']['GraphTitle'] }" )

                if(graph['graphProperty']['is3DGraph']):
                    typeArr.append ([{'type': 'scatter3d'}])  # or scene
                else: 
                    typeArr.append ([{'type': 'xy'}]) 
        #print(subplotTittles)
        return typeArr, subplotTittles

def UpdateSubplotTitles(fig:go.Figure, graphSetting):
    colIdx = 1
    rowIdx = 1
    for graph in graphSetting['GraphSetting']:
        xTitle = graph['graphProperty']['xTitle']
        yTitle = graph['graphProperty']['yTitle']
        if(graph['Enabled']):
            fig.update_xaxes(title_text=xTitle, row=rowIdx, col=colIdx)
            fig.update_yaxes(title_text=yTitle, row=rowIdx, col=colIdx)
            rowIdx = rowIdx +1


def DistVelAccGraph(df:pd.DataFrame, fig:go.Figure,rowIdx:int, DVAGraph_Toogle):
  
    for index, row in df.iterrows():
            curRowIdx = rowIdx
            userID = row['userID']
            turn = row['turn']
            level = row['levelDiff']
            traceName = f'user{str(userID)}_level{level}_turn{turn}'
            distance, velocities, acceleration = CalDistVelAcc(row['plyr_pos'], 20)
            trace1 = go.Scatter(
                x = [ i for i in range(len(distance)) ],
                y =  distance,
                name =  f'{traceName}_dist',
                legendgroup=f'group_{str(userID)}_turn{turn}',
                marker=dict(size=5, colorscale = 'Picnic'),
            )
            trace2 = go.Scatter(
                x = [ i for i in range(len(velocities)) ],
                y =  velocities,
                name =  f'{traceName}_vel',
                legendgroup=f'group_{str(userID)}_turn{turn}',
                marker=dict(size=5, colorscale = 'Picnic'),
            )
            trace3 = go.Scatter(
                x = [ i for i in range(len(acceleration)) ],
                y =  acceleration,
                name =  f'{traceName}_acc',
                legendgroup=f'group_{str(userID)}_turn{turn}',
                marker=dict(size=5, colorscale = 'Picnic'),
            )

            if(DVAGraph_Toogle[0]):
                fig.add_trace(trace1, row = curRowIdx, col = 1)
                curRowIdx = curRowIdx+1
                
            if(DVAGraph_Toogle[1]):
                fig.add_trace(trace2, row = curRowIdx, col = 1)
                curRowIdx = curRowIdx+1
            if(DVAGraph_Toogle[2]):
                fig.add_trace(trace3, row = curRowIdx, col = 1)
                curRowIdx = curRowIdx+1

    return fig, rowIdx+1

def CalDistVelAcc(posArr, skip:int):
    pos = posArr[::skip]
    # time in second 
    # time = np.arange(0, len(posArr), skip)
    # time = time / skip
    #dt = np.diff(time)
    distance_vect = np.diff(np.array(pos), axis = 0) 

    distance_mag = np.linalg.norm(distance_vect, axis =1)

    acc_dist = 0
    accumulate_distArr = []
    for v_m in distance_mag:
        acc_dist = acc_dist + v_m
        accumulate_distArr +=[acc_dist]

     # delta time bet each point = 0.05(fps) * #skip frames
    dt = np.full((len(pos) -1), skip*0.05 )
    

    #print("time diff", dt)
    #dt[:, np.newaxis] for  each elem in dt, create new row
    # each v in distance vec =>  distance vec[i] / dt[i]
    velocities = distance_vect / dt[:, np.newaxis]
    #velocities2 = np.gradient(np.array(pos), axis=0)
    velocities_n = np.linalg.norm(velocities, axis =1)

    dt_velocity = dt[:-1]
    accelerations = np.diff(velocities, axis=0) / dt_velocity[:, np.newaxis]
    #print(accelerations)
    # acceleration = np.gradient(velocities, axis=0)
    accelration_n = np.linalg.norm(accelerations, axis =1)
   
    # print(accumulate_distArr)
    # print(accelration_n)
    return accumulate_distArr, velocities_n, accelration_n



def GetToogleForDistVelAcc(graphSetting):
    boolArr= [False,False, False]
    for graph in graphSetting['GraphSetting']:
        if(graph['Enabled'] and graph['Attribute'] == AttributeType.WalkDistance.value):
                boolArr[0] = True
        if(graph['Enabled'] and graph['Attribute'] == AttributeType.Velocity.value):
                boolArr[1] = True
        if(graph['Enabled'] and graph['Attribute'] == AttributeType.Acceleration.value):
                boolArr[2] = True
    return boolArr


class ConTinuousGraph:
    def __init__(self, graphSetting, df:pd.DataFrame):
        self.graphSetting = graphSetting
        self.df = df

        # initialization
        self.level = 0
        self.selectedUserRange = [i for i in range(0, 50) ]

        #load graph setting
        self.LoadGraphSetting(graphSetting)

    def LoadGraphSetting(self, graphSetting):
        self.graphSetting = graphSetting
        # self.level = graphSetting['selectedLevel']
        # u_start:int = graphSetting["SelectedUserRangeStart"]
        # u_end:int = graphSetting['SelectedUserRangeEnd']
        
        # self.selectedUserRange = [i for i in range(u_start, u_end) ]
        self.skipFrame = 20
        self.showIndexArr = None # will later load from graph setting

    def UpdateGraphLevelSetting(self, _,__,userRange, level):
        self.selectedUserRange = GetUserRangeFromText(userRange)
        self.level = level
        
      
    def UpdateOrConstructGraph(self):
        filter_df:pd.DataFrame = GetSelectedUserRangeData(self.df, self.level, self.selectedUserRange)
        print("UpdateGraphByLevel()")
        return self.ConstructConTinuousGraphHelper(filter_df)
   

    def ConstructConTinuousGraphHelper(self, filter_df):
        graphSetting = self.graphSetting
        skipFrame = self.skipFrame

        specsArr, subplotTitles = GetSubplotType(graphSetting)
        numGraph = CountNumGraph(graphSetting)
        print(f"numGraph {numGraph}")
        if(numGraph <1):
            print("no attribute has not been enabled")
        fig:go.Figure = make_subplots(rows = numGraph, cols =1,
                    subplot_titles = subplotTitles, specs= specsArr)

        UpdateSubplotTitles(fig, graphSetting)

        nextRow:int =1
        for graph in graphSetting['GraphSetting']:
           
            if(graph['Attribute'] == AttributeType.WalkingPath.value and graph['Enabled']):
                
                self.showIndexArr =  graph ['graphProperty']['SelectedXYZ']
                fig, nextRow = PositionGraph(filter_df,fig, nextRow,  self.showIndexArr ) 
                
            elif(graph['Attribute'] == AttributeType.PlayerRot.value and graph['Enabled']):
                
                self.skipFrame =  graph ['graphProperty']['skipFrame']
                fig, nextRow = RotationGraph(filter_df,fig, nextRow, skipFrame)

            # else:
            #     ...
            #     print(f"[warning] either graph is not enable or no graph attribute for this int  {graph['Attribute']}") 
    
        DVAGraph_Toogle = GetToogleForDistVelAcc(graphSetting)
        

        fig, nextRow = DistVelAccGraph(filter_df, fig, nextRow, DVAGraph_Toogle)


        figureWidth =  GetInt(graphSetting['figureWidth'], 800) 
        figureHeight = GetInt(graphSetting['figureHeight'], 280)* numGraph

        mainTitle = f'Selected Level {self.level}\'s User Performance '
        fig.update_layout(title = mainTitle,width=figureWidth, height=figureHeight,)
        return [fig, None]