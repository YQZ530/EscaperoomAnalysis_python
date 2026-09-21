

from enum import Enum
import pandas as pd
from sklearn.cluster import KMeans
import chart_studio.plotly as py
import plotly.graph_objs as go
from ContinuousGraph import ConTinuousGraph
from ClusterGraph import ClusterGraph,ConstructDF,RunKmeanCluser

from DiscreteGraph import DiscreteGraph


class GraphAnalyzer:
	def __init__(self, df, maxLevel):
		self.df = df
		self.maxLevel = maxLevel
		self.conGraph = None
		self.clusterGraph = None
		self.disGraph = None

	
	def DiscreteGraph(self, graphSetting):
		df = self.df

		if(self.disGraph is None):
			self.disGraph = DiscreteGraph(graphSetting, df)
		else:
			self.disGraph.UpdateGraphSetting(graphSetting)
		figs, graphType =  self.disGraph.ConstructDisGraph()
		return figs, graphType, [self.disGraph.UpdateGraphLevelSetting, self.disGraph.UpdateFilterSetting, self.disGraph.UpdateRankSetting, self.disGraph.UpdateGraph, self.disGraph.UpdateUserPerspectiveSetting] 
		
	def RunEventGraph(self, graphSetting, edf):
		df = self.df

		if(self.disGraph is None):
			self.disGraph = DiscreteGraph(graphSetting, df)
		else:
			self.disGraph.UpdateGraphSetting(graphSetting)
		figs, graphType =  self.disGraph.ConstructDisGraph()
		return figs, graphType, [self.disGraph.UpdateGraphLevelSetting, self.disGraph.UpdateFilterSetting, self.disGraph.UpdateRankSetting, self.disGraph.UpdateGraph, self.disGraph.UpdateUserPerspectiveSetting] 
		
	def ContinuousGraph(self, graphSetting, df:pd.DataFrame):
		if(self.conGraph is None):
			self.conGraph = ConTinuousGraph(graphSetting, df)
		else:
			self.conGraph.LoadGraphSetting(graphSetting)
		figs =  self.conGraph.UpdateOrConstructGraph()
		return figs,  self.conGraph.UpdateGraphLevelSetting, self.conGraph.UpdateOrConstructGraph
		

	def RunCluster(self, graphSetting, df:pd.DataFrame):

		if(self.clusterGraph is None):
			self.clusterGraph = ClusterGraph()
		

		N_cluster, cluster_df, colNameArr = ConstructDF(self.maxLevel,graphSetting, df)
		result_df, clusterResultName = RunKmeanCluser(num_clusters=N_cluster, level_df = cluster_df, colNameArr = colNameArr)
		
		fig = self.clusterGraph.CreateClusterGraph(result_df, colNameArr, clusterResultName, graphSetting)

		return fig