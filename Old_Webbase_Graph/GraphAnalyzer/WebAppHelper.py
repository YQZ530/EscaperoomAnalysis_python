from DiscreteGraph import GraphType
from dash import Dash,  Input, Output, callback, ctx, dcc,ALL, Patch
from dash import html,State
import dash_daq as daq

def ConstructDropdown(dropDownName, dropDownList, idName,default_dp_v = None ):
        return [
            html.Label(dropDownName),
            dcc.Dropdown(dropDownList, default_dp_v, id=idName,
            style={'width': '150px', 'height': '40px'}),
        ]
       
def ConstructTextField(textfiledName, textFileID, textStyle = None, default_field_value = None ):
                return [
                html.Label(textfiledName),
                dcc.Input(
                    id=textFileID,
                    type="text",
                    placeholder="input type text", 
                    value = default_field_value, style = textStyle),
            ]

def Construct_RankElem(percentileId, targetArr):
        markdown = dcc.Markdown("#### Rank")
        rankArr =  ConstructDropdown("Target:", targetArr, "rank_dropdown")
        rankArr += ConstructDropdown("Show users that are", ["Top", "Bottom"], f"{percentileId}_comp")
        rankArr += ConstructTextField(" ", "rank_input", {'width': '30px'},default_field_value =  "-1" )
        rankArr += [html.Label("of the population")]
        style ={'display': 'flex', 'flex-direction': 'row'}

        return markdown, rankArr,style

def Construct_AttriSel_DropDownElem(targetArr):
    markdown = dcc.Markdown("#### Graph Setting")
    dropdownElem =  ConstructDropdown("Show Attribute:", targetArr, "attrSel_dropdown")
    dropdownElem += ConstructTextField("Number of bins", "nbin_input", {'width': '300px'},default_field_value =  "5" )
    style ={'display': 'flex', 'flex-direction': 'row'}

    return markdown, dropdownElem,style

def Construct_SendToUnityElem(textFieldID = "text_field",  
        buttonName ='Submit',   buttonId = 'SendToUnityBtt', outputFiledID = "output_field"):
        title =  dcc.Markdown("#### Send Replay Message Back to Unity")

        return title,  [
            dcc.Input(
                id= textFieldID,
                type="text",
                placeholder="input type text", 
                value = ''),
            html.Button(buttonName, id= buttonId,n_clicks=0),
            html.Div(id= outputFiledID),
        ]

def Construct_LevelSliderElem(sliderID, sliderTitle, maxTick):
    title = dcc.Markdown(f"#### {sliderTitle}", id = f"{sliderID}_title")

    arr = [ dcc.Slider(
                id= sliderID,
                min=0,
                max=maxTick,
                step=1,
                value=0,
                marks={i: str(i) if i >= 0 else "All" for i in range(-1, 15)}
                #marks={i: str(i) for i in range(0, maxTick)}
            ),
            html.Div(id='LevelSlider_output')
    ]
    return title, arr

def Construct_RangeSliderElem(sliderID, sliderTitle, maxTick):
    title = dcc.Markdown(f"#### {sliderTitle}", id = f"{sliderID}_title")
    arr = [dcc.RangeSlider(
                id=sliderID ,
                min=-1,
                max=maxTick,
                step=1,
                value=[0,maxTick],
                marks={i: str(i) for i in range(0, maxTick)}
            )
            ]
    return title, arr




def ConstructProportion_Tab2():
    
    resultElemArr = ConstructDropdown("Proportion Func: Count(condition is True)/ Total.    Proportion Setting: Comparator", ["<", ">", ">=", "<=", "=="], "proportion_dp_comparator", "<")
    resultElemArr += ConstructTextField(" value", "proportion_dp_compvalue",{'width': '100px'}, default_field_value= "0" )
    style ={'display': 'flex', 'flex-direction': 'row'}
    return resultElemArr, style

def Construct_AttriSel_Tab2(attributeNameArr, FuncNameArr ):
    markdown = dcc.Markdown("#### Graph Setting")
    resultElemArr =  ConstructDropdown("Show Attribute:", attributeNameArr, "tab2_attrSel_dropdown", attributeNameArr[0])
    resultElemArr +=  ConstructDropdown("Function", FuncNameArr, "func_dropdown", FuncNameArr[0]) 

    style ={'display': 'flex', 'flex-direction': 'row'}
    return markdown, resultElemArr,style


def Construct_Filter_Template():
    markdown =  dcc.Markdown("#### Filtering", style={'marginRight': '10px'})
    #style ={'display': 'flex', 'flex-direction': 'row'}
    filterElems = [ html.Button('Add', id='filter_add', n_clicks=0), html.Button('Remove', id='filter_remove', n_clicks=0), ]
    style={'display': 'flex', 'alignItems': 'center'}
    return markdown, filterElems, html.Div( id='dropdown-container-div'), style

def Construct_FilterElem( patched_children, id, attributeNameArr):
    def target_dropdown(id_index, attributeNameArr):
        new_label =  html.Label("target:",  id= {"type": "target-dp-label", "index":  id_index})
        new_dropdown = dcc.Dropdown(
            attributeNameArr,
            id={"type": "target-dp", "index":  id_index},
            style={'width': '150px', 'height': '40px'},
        )
        return new_label, new_dropdown

    def comparator_dropdown( id_index):
        new_label =  html.Label("condition",  id= {"type": "comparator-dp-label", "index":  id_index})
        new_dropdown = dcc.Dropdown(
            [">", "<", ">=", "<="],
            id={"type": "comparator-dp", "index":  id_index},
            style={'width': '150px', 'height': '40px'},
        )
      
        return new_label, new_dropdown
    
    def textField(textfiledName, textFileID, id_index, textStyle):
                
        label=  html.Label(textfiledName,  id= {"type": f"{textFileID}-label", "index":  id_index})
        textfield =  dcc.Input(
            id={"type": textFileID, "index":  id_index},
            type="text",
            placeholder="input type text", 
            value = 0, 
            style = textStyle)
            
        return label, textfield
    
    l1,dp1 = target_dropdown(id, attributeNameArr)
    l2,dp2 = comparator_dropdown(id)
    l3, textfield = textField("value ", "filter-textfield", id ,{'width': '30px'})
    
    elems = [l1,dp1,l2,dp2,l3, textfield]

    patched_children.append( html.Div(elems, style={'display': 'flex', 'flex-direction': 'row'} ))

    return patched_children

def Construct_Sorting_Elem(targetArr):
    markdown =  dcc.Markdown("#### Sorting")
    sortArr_tab1 =  ConstructDropdown("Target:", targetArr, "sort_dropdown")
    sortArr_tab1 += ConstructDropdown("Sort Order",  ["Ascending", "Descending"], f"sort_order_t1")
    #rankArr += ConstructTextField(" ", "rank_input", {'width': '30px'},default_field_value =  "-1" )
    #rankArr += [html.Label("of the population")]
    style ={'display': 'flex', 'flex-direction': 'row'}
    sortArr_tab2 = ConstructDropdown("Sort Order",  ["Ascending", "Descending"], f"sort_order_t2")
    return markdown, sortArr_tab1,sortArr_tab2, style


def Construct_OtherControls_Elem():
    markdown =  dcc.Markdown("#### Other Controls")
    buttElem = [html.Button('Save To Graph Collection', id='coll_add_butt', n_clicks=0),
            html.Button('Clear Graph Collection', id='coll_clear_butt', n_clicks=0),
            html.Div(id= 'coll_add_text')]
    
    return markdown, buttElem