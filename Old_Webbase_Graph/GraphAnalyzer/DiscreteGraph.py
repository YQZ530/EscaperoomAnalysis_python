import pandas as pd
import numpy as np
from enum import Enum
from Util import  checkIsIntOrIntList,GetSelectedUserRangeData,GetUserRangeFromText,GetInt
import plotly.graph_objs as go
from DiscreteGraphUserPersp import CreateUserPerspectiveGraph
from Util import GetNumber

class GraphType(Enum):
	barGraph = 0
	lineGraph = 1
	scatterGraph = 2
	Boxplot = 3
	Piechart = 4
	Histogram = 5


def FilterTable(df, target_values, comparator_values, textfield_values):
        def RunComparator(compare_text, df, target, value):
            filter_df = None
            if(compare_text == ">"):
                filter_df = df[df[target] > value ]
            elif(compare_text == ">="):
                filter_df = df[df[target] >= value ]
            elif(compare_text == "=="):
                filter_df = df[df[target] == value ]
            elif(compare_text == "<"):
                filter_df = df[df[target] < value ]
            else: #if(compare_text == "<="):
                filter_df = df[df[target] <= value ]
            return filter_df

        
        if(target_values is None or len(target_values) == 0):
            return df

        final_df = df
        for i in range(len(target_values)):
            target = target_values[i]
            compare_text = comparator_values[i]
            value =  GetNumber(textfield_values[i], 0) 
            
            if(target == None or compare_text == None):
                continue
            filter_df = RunComparator(compare_text, final_df, target, value)
            final_df = filter_df
            
            #print(f"filterDf:: {target}, {compare_text}, {value}\n df {final_df}")
        return final_df

def RankTable(df,target, comparator, rank_text ):
        if(target == None or comparator == None or rank_text == None):
            return df
        rank = GetNumber(rank_text, 10)
        temp = df.copy()

        ascending = True
        if(comparator == "Top"):
            ascending = False
        temp['Rank'] = temp[target].rank(ascending=ascending, method='min')
        filter_df = temp[(temp['Rank'] < rank)]
        
        return  filter_df
def SortTable(df, target, sortOrder):
    if(target == None or sortOrder == None):
        #print(f"sort table fail, either parameter is null {target}, {sortOrder}")
        return df
    isAscending = sortOrder == "Ascending"
    sorted_df = df.sort_values(by = target, ascending = isAscending)

    return sorted_df

def CreateTrace( graphType:int, colname:str, df:pd.DataFrame, x_names, nbin_histogram,nbin_piechart ):
        
        initial_visibile = True
        trace = None
        legendName = f"{colname}"
        #print(f"graphType{graphType} x_names {x_names}  ")
        if(graphType == GraphType.barGraph.value):
            #print("bar")
            trace =  go.Bar( x = x_names,
                            y = df[colname] ,
                            name = legendName , 
                            visible=initial_visibile,
                            #width = 3,
                    )
        elif (graphType == GraphType.lineGraph.value):

            trace =  go.Scatter( x = x_names,
                                y = df[colname] ,
                                name = legendName , 
                                visible=initial_visibile,
                    )
        elif (graphType == GraphType.scatterGraph.value):  # scatter
            trace =  go.Scatter( 
                x = x_names,
                y = df[colname] ,
                name = legendName , 
                mode='markers',
                #marker=dict(size=10, color=marker_colors, symbol= marker_styles),
                visible=initial_visibile)
        
            #print("create scatter")
        elif (graphType == GraphType.Boxplot.value):
            trace = go.Box(y = df[colname],boxpoints='outliers', boxmean= True, name = legendName)

        elif(graphType == GraphType.Histogram.value):
            hover_template = colname+ ' Count: %{y}<br> Bin Range: %{x}<br>'
            trace = go.Histogram(x = df[colname], nbinsx =  nbin_histogram, hovertemplate=hover_template)
                
        elif(graphType == GraphType.Piechart.value):
            
            custom_bins =nbin_piechart
            trace = CreatePieChart(custom_bins, colname, df)
                
        else:
                print(f"undefine graph function for graphtype {graphType}")
        return trace

def CreatePieChart(custom_bins, colname:str, df:pd.DataFrame):

        hist_values, bin_edges = np.histogram(df[colname], bins=custom_bins)
        #x_names = [f"Rating ={custom_bins[i]}" for i in range(len(custom_bins)-1) ]
        #print(f"hist value{hist_values}, binedge{bin_edges}")

        def SetBinName(bin_edges):
            bin_names = []
            if(len(bin_edges) <2):
                return "Not enough bin edges"
            
            for i in  range(1, len(bin_edges)):
                bin_names += [f"{round(bin_edges[i-1],2)} <= x < { round(bin_edges[i],2)}"]

            #bin_names += [f"x >= {round(bin_edges[-1],2)}"]
            return bin_names

        x_names = SetBinName(bin_edges) #bin egdge always has number of bin +1
        hover_template = 'Category: %{label}<br>Value: %{value}<br>Percentage: %{percent}'

        trace =  go.Pie( values=hist_values, labels=x_names, hovertemplate=hover_template)
        return trace

class DiscreteGraph:
    def __init__(self, graphSetting, df:pd.DataFrame):
        self.graphSetting = graphSetting
       

        self.df = df
        self.graphType = -1

        self.level = 0 # TODO load from graph setting
        self.selectedUserRange = [i for i in range(0,60)]
        self.selectAttribute = "GameplayDur"
        self.nbin_piechart = 5
        self.nbin_histogram = 5

        self.userPersp_colName = "GameplayDur"
        self.userPersp_funcName = "Avg"
        self.userPersp_params = [">", "0"]
        #self.percentileSetting =  Percentile()
        self.rankComparator = None
        self.rankValue = None
        self.rankTarget = None

        self.sort_target = None
        self.sort_Order = None

        self.filter_target_values = None
        self.filter_comparator_value = None
        self.filter_textfield_values = None

    def UpdateGraphSetting(self, graphSetting):
        self.graphSetting = graphSetting


    def UpdateGraphLevelSetting(self, selectedAttr = None, nbin = None, userRange = None, level =None):
       
        if(self.graphType == GraphType.Piechart.value and nbin is not None):
            self.nbin_piechart = checkIsIntOrIntList(nbin)

        elif(self.graphType == GraphType.Histogram.value and nbin is not None):
            self.nbin_histogram = GetInt(nbin, 6)

        if(selectedAttr is not None): self.selectAttribute = selectedAttr 
        if(userRange is not None): self.selectedUserRange = GetUserRangeFromText(userRange)
        if(level is not None): self.level = level
        #if(self.percentileSetting is None): self.percentileSetting = Percentile()
       
    def UpdateRankSetting(self,  rankTarget, rankComparator, rankValue):
        self.rankTarget = rankTarget
        self.rankComparator = rankComparator
        self.rankValue = rankValue
        
    
    # # find users whose score is lower than 80% of the group ::  TOP Percentile 0.8, greatherThan False
    # # find users whose score is higher than 80% of the group :: TOP Percentile 0.2, greatherThan True
    # def UpdatePercentileSetting(self,  colName = 'DifficultyRating',
    #      top_percentage = 100, greaterThanPercentile = True):

    #     self.percentileSetting.SetValue(colName, top_percentage, greaterThanPercentile)

    def UpdateUserPerspectiveSetting(self, colName, funcName, otherParams ):
        self.userPersp_colName =  colName
        self.userPersp_funcName = funcName
        self.userPersp_params = otherParams

        
    
    def UpdateFilterSetting(self, filter_target, filter_comparator, filter_value,
                    sort_target, sort_order ):
        self.filter_target_values = filter_target
        self.filter_comparator_value = filter_comparator
        self.filter_textfield_values = filter_value
        self.sort_target = sort_target
        self.sort_Order = sort_order

    def UpdateGraph(self):
        df = GetSelectedUserRangeData(self.df, self.level, self.selectedUserRange)
        filter_df = FilterTable(df, self.filter_target_values, self.filter_comparator_value, self.filter_textfield_values)
        rank_df = RankTable(filter_df, self.rankTarget, self.rankComparator, self.rankValue )
        sorted_df = SortTable(rank_df, self.sort_target, self.sort_Order)
        return self.DiscreteGraph(sorted_df)

    
    def DiscreteGraph(self, filter_df):
        graphSetting = self.graphSetting

        traces = []
        mainFig = go.Figure()
        
        x_names = [ f"user{x}_level{z}_turn{y}"  for x, y,z in zip(filter_df['userID'], filter_df['turn'], filter_df['levelDiff'] )]
       
       
        xTitle =graphSetting[ "X_Axis"]
        yTitle =graphSetting[ "Y_Axis"]
        
        try:
             self.graphType = int(graphSetting["graphType"]) 
            
        except:
            print(f"[Error] undefined input graphtype {self.graphType}; should be int")

        graphType = self.graphType
        
        
        if( (graphType == GraphType.barGraph.value) or 
            (graphType == GraphType.lineGraph.value) or 
            (graphType == GraphType.scatterGraph.value)or 
            (graphType == GraphType.Boxplot.value)
            ):
            for col  in graphSetting['SimpleGraphSetting']:
                colName = col["Label"]
                trace = CreateTrace(graphType, colName, filter_df, x_names, self.nbin_histogram, self.nbin_piechart )
                traces+=[trace]
                mainFig.add_trace(trace)

            # set tittles        
            mainFig.update_layout(
                title = f'Selected Level {self.level}\'s User Performance ' if self.level >=0 else f'All Level\'s User Performance ',
                xaxis =dict(title=xTitle),
                yaxis =dict(title=yTitle),
            )
        elif ((graphType == GraphType.Piechart.value) or 
                    (graphType == GraphType.Histogram.value)):
                trace = CreateTrace(graphType, self.selectAttribute, filter_df, None, self.nbin_histogram, self.nbin_piechart)
                mainFig.add_trace(trace)

                mainFig.update_layout(
                    title = f'Distribution of {self.selectAttribute} at level {self.level}' if self.level >=0 
                    else f'Distribution of {self.selectAttribute} across all levels',
                )
        else:
            print(f"[Error] undefined input graphtype {graphType}; should be int")
      
       
        fig2 = CreateUserPerspectiveGraph(self.df, self.selectedUserRange, 
            self.userPersp_colName, self.userPersp_funcName, self.userPersp_params, self.sort_Order)
    
        
        return [mainFig, fig2]


    def ConstructDisGraph(self):
        return self.DiscreteGraph(self.df), self.graphType
