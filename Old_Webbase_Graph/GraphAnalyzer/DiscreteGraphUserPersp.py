from enum import Enum
import plotly.graph_objs as go
from enum import IntEnum
import pandas as pd
from Util import GetInt
class basicAlgorithm(IntEnum):
    Avg = 0
    Std =1
    Median =2
    SuccessRate = 3
    Proportion = 4

class MyComparator(Enum):
    GREATER_THAN = ">"
    GREATER_EQUAL_THAN = ">="
    LESS_THAN = "<"
    LESS_EQUAL_THAN = "<="
    EQUAL = "=="

    
def Calculator_GivenUser(df, userID, algorithm, colName, controls, ):
    filtered_df= df[df['userID'] == userID]
    
        
    
    result = 0
    if(algorithm == basicAlgorithm.SuccessRate):
        result = SuccessRate(df, userID)
    elif(algorithm == basicAlgorithm.Avg):
        result = filtered_df[colName].mean()
    elif(algorithm == basicAlgorithm.Median):
        result = filtered_df[colName].median()
    elif(algorithm == basicAlgorithm.Proportion):
        result = SelectAttributeProprotion(df, userID, colName, controls[0], controls[1])
    else:
        result = filtered_df[colName].std()
    
  

    return result

def SuccessRate(df, selectedUser):
        filtered_df = df[(df['userID'] == selectedUser)]  
        tot = len(filtered_df['GameplayResult'])
        count =   ((filtered_df['GameplayResult'] > 0) ).sum()
        result = count /tot; 
        result = round(result, 2)
        #print(f"tot played {tot}  win{count} result{result}")
        return result

def SelectAttributeProprotion(df, selectedUser, colName, compartor, value,  ):
        filtered_df = df[(df['userID'] == selectedUser)]  
        tot = len(filtered_df[colName])
        print(f"select user's df {filtered_df[colName]}")
        # based on comparator to do > < >= <= ==
        count = 0
        if(compartor == MyComparator.EQUAL):
            count =   ((filtered_df[colName] == value)).sum()
        elif(compartor == MyComparator.LESS_THAN):

            count =   ((filtered_df[colName] < value)).sum()
        elif(compartor == MyComparator.LESS_EQUAL_THAN):
            count =   ((filtered_df[colName] <= value)).sum()
        elif(compartor == MyComparator.GREATER_THAN):
            count =   ((filtered_df[colName] > value)).sum()
        elif(compartor == MyComparator.GREATER_EQUAL_THAN):
            count =   ((filtered_df[colName] >= value)).sum()

        if(tot is None or tot == 0):
            tot = 1
        result = count /tot; 
        result = round(result, 2)
        #print(f"tot played {tot}  win{count} result{result}")
        return result

def CreateSuccessRateGraph(self, df:pd.DataFrame):

        allLevelSuccessRate = []
        # from user 0 to user 5
        #colName = self.selectAttribute
        colName = "GameplayResult"
        for i in df['userID'].unique():
            allLevelSuccessRate+=[SuccessRate(i, colName, df)]
        #print(allLevelSuccessRate)
        x_names = [ f"user{x}"  for x in df['userID'].unique()]

        trace = go.Bar(x = x_names,  y = allLevelSuccessRate )
        return trace 

def CreateUserPerspectiveGraph(df:pd.DataFrame, userRange,  colName, funcName, params, sortOrder ):
    #print(f"CreateUserPerspectiveGraph(): {colName}, {params}, {userRange}, {funcName} ")
    if(params == None or len(params) == 0):
        fig = go.Figure()
        return fig
    
    comparator = next(member for member in MyComparator if member.value == params[0])
    #comparator = MyComparator[params[0]]
    value = GetInt(params[1], 0)
  
    algorithm = basicAlgorithm[funcName]
    y_arr = [ Calculator_GivenUser(df,userID, algorithm, colName, [comparator, value])  for userID in userRange]
    x_arr = [ f"user{userID}" for userID in userRange]
    
    tempdf = pd.DataFrame({"userID":x_arr, "func_values":y_arr})
    #print(f"~~~~~~~before sort~~~~~~~\n {tempdf}\n")
    if(sortOrder != None):
        isAscending = sortOrder == "Ascending"
        sortTarget = "func_values" 
        tempdf = tempdf.sort_values(by = sortTarget, ascending= isAscending)
        #print(f"~~~~~~~after sort~~~~~~~\n {tempdf}\n")
    #print(f"CreateUserPerspectiveGraph(): {colName}, {comparator}, {algorithm}, {array} ")
   
   
    fig = go.Figure()
    trace = go.Bar(x = tempdf['userID'],  y = tempdf['func_values'] )

    fig.add_trace(trace)
    fig.update_layout(
                    title = f'{funcName} {colName} of all users ' if algorithm != basicAlgorithm.SuccessRate else f" Success Rate of all users" ,
                    xaxis =dict(title="Users"),
                    yaxis =dict(title= colName) if algorithm != basicAlgorithm.SuccessRate else  dict(title = "Success Rate"),
            )
    return fig

