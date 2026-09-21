
from DiscreteGraph import GraphType
from dash import Dash,  Input, Output, callback, ctx, dcc,ALL, Patch
from dash import html,State
import dash_daq as daq
import copy
from WebAppHelper import Construct_FilterElem,Construct_AttriSel_Tab2,Construct_LevelSliderElem, Construct_OtherControls_Elem,Construct_RangeSliderElem, Construct_Sorting_Elem
from WebAppHelper import Construct_Filter_Template,Construct_SendToUnityElem,Construct_AttriSel_DropDownElem,Construct_RankElem,ConstructTextField,ConstructProportion_Tab2

class MDash:
    def __init__(self, maxUser, maxLevel):
        
        self.app = Dash(__name__)
        self.isRun = False
        self.conn = None


        self.figs = []
        self.tab3Figs = []

        self.tab1Elem = None
        self.tab2Elem = None
        self.tab3Elem = None
        self.curTabIdx = 0
        self.tab1GraphID= 'mainGraph'
        self.tab2GraphID= 'userGraph'
        self.tab3GraphID= 'collectionGraph'
        
        self.figFilterControl = None
        self.figRankControl = None
        self.figTab2updateControl = None

        self.num_filtercontrols = 0
        self.maxUser = maxUser
        self.maxLevel = maxLevel
        
        
        self.allFiveAttributes = ["GameplayDur", "DifficultyRating", "ScarinessRating", "FunRating", "GameplayResult"]
        
      
        self.levelSlider = "LevelSlider"
        self.uRangeSlider = "ContSlider" #user Range

        lvl_markdown, lvlSliderArr = Construct_LevelSliderElem(self.levelSlider, "Level Selection", self.maxLevel)
        uRange_markdown, uRangeSliderArr = Construct_RangeSliderElem(self.uRangeSlider, "User Range Selection", self.maxUser)
        p_markdown, percentileArr,_ = Construct_RankElem("rank", self.allFiveAttributes)
        send_markdown, sendArr =     Construct_SendToUnityElem()
        
        elementArr = [
            dcc.Graph(id =self.tab1GraphID),
            lvl_markdown, html.Div(lvlSliderArr,  style={'display': 'none'}),
            uRange_markdown, html.Div(uRangeSliderArr, style={'display': 'none'}), 
            p_markdown, html.Div(percentileArr, style={'display': 'none'}),
            send_markdown, html.Div(sendArr, style={'display': 'none'})
        ]
       
      
        self.app.layout = html.Div(elementArr)

        #register  submit button called back
        self.app.callback(
            Output('output_field', 'children'),
            Input("SendToUnityBtt", "n_clicks"),
            State('text_field', 'value'), 
            suppress_callback_exceptions=True,
        )(self.SendToUnity)

        # Register clickdata called back
        self.app.callback(
            Output("text_field", "value"),
            Input(self.tab1GraphID, "clickData"), 
            suppress_callback_exceptions=True,
            prevent_initial_call=True,
        )(self.ShowClickableData)  


         # Register level slider title called back
        self.app.callback(
            Output(f"{self.levelSlider}_title", "children"),
            Input(self.levelSlider, "value"), 
            suppress_callback_exceptions=True,
            prevent_initial_call=True,
        )(self.UpdateLvlSliderOutput)  


        #tab callback
        self.app.callback(
            Output('tab_content', "children"),
            Input('tabs_div', "value"), 
            
            prevent_initial_call=True,
            allow_duplicate=True,
        )(self.SwitchTabCallback)  
       
        self.app.callback(
            Output('coll_add_text', 'children'),
            [Input("coll_add_butt", "n_clicks"),
             Input("coll_clear_butt", "n_clicks")],
        )(self.CloneGraph)


        self.tab1_callback()
        self.tab2_callback()
        self.tab3_callback()
        self.filter_callbacks()
        

    def tab1_callback(self):

        @self.app.callback(
            Output(self.tab1GraphID, 'figure'),
            [
            Input('tabs_div', "value"), 
            Input('attrSel_dropdown', 'value'),
            Input('nbin_input', 'value'),
            Input(self.uRangeSlider, 'value'), 
            Input(self.levelSlider, 'value'), 

            Input('rank_dropdown', 'value'), 
            Input('rank_comp', 'value'), 
            Input('rank_input', 'value'), 

            Input('sort_dropdown', 'value'),
            Input('sort_order_t1', 'value'),
            Input({"type": "target-dp", "index": ALL}, "value"),
            Input({"type": "comparator-dp", "index": ALL}, "value"),
            Input({"type": "filter-textfield", "index": ALL}, "value"),
            
            ],
            prevent_initial_call=True,
            suppress_callback_exceptions=True,
         
        )#(self.Update_Figure_tab1)
        
        def Update_Figure_tab1(tab_v, attrSel_v, nbin_v, userslider_v, levelsliderValue,
                     rankTarget, rankComparator, rankValue,
                     sortTarget, sortOrder,
                     target_values, comparator_values, textfield_values):

            if(self.curTabIdx != 0): 
                #skip as current tab is not fig 1
                return None
            self.SwitchTabCallback(tab_v)
            #update level, user range, selected attribute
            if(self.figLevelControl is not None):
                print(f"Update_Figure_tab1::level {levelsliderValue}")
                self.figLevelControl(attrSel_v, nbin_v, userslider_v, levelsliderValue)
            
            #update filter
            if(self.figFilterControl is not None):
                self.figFilterControl(target_values,comparator_values,textfield_values, sortTarget, sortOrder)
                print(f"Update_Figure_tab1::figFilterControl  {target_values},{comparator_values},{textfield_values}")
            
            if(self.figRankControl is not None):
            #     #b_isHigher = "Higher" == isHigher
                #print(f"Update_Figure_tab1:: colname {rankTarget} percentile{rankValue},")
                self.figs = self.figRankControl(rankTarget, rankComparator, rankValue)
            

            if(self.figUpdateControl is not None):
                self.figs = self.figUpdateControl()
            return self.figs[self.curTabIdx]


    def tab2_callback(self):
         #tab2 figure callback
        @self.app.callback(
            Output(self.tab2GraphID, 'figure'),
            [
            Input('tabs_div', "value"), 
            Input('tab2_attrSel_dropdown', 'value'),
            Input('func_dropdown', 'value'),
            Input('proportion_dp_comparator', 'value'),
            Input('proportion_dp_compvalue', 'value'),
            Input(self.uRangeSlider, 'value'), 
            Input('sort_order_t2', 'value'),
            ],
            prevent_initial_call=True,
            suppress_callback_exceptions=True,
        ) 

        def Update_Figure_Tab2( tab_v, attrSel_v, func, comparator, compvalue, userslider_v, sort_order):
            
            if(self.curTabIdx != 1):
                return None
            #print(f"Update_Figure_Tab2:: {tab_v}, {attrSel_v}, {func}, {comparator} , {compvalue}, {userslider_v}")
            if(self.figTab2updateControl is not None):
                self.figTab2updateControl(attrSel_v, func, [comparator, compvalue])
            
            if(self.figFilterControl is not None):
                self.figFilterControl (None,None,None,None, sort_order)

            if(self.figLevelControl is not None):
                self.figLevelControl(None, None, userslider_v, None)

            if(self.figUpdateControl is not None):
                self.figs = self.figUpdateControl()
            return self.figs[self.curTabIdx]
        
    def filter_callbacks(self):
        
        @self.app.callback(
            Output("dropdown-container-div", "children"),
            [Input("filter_add", "n_clicks"),  Input("filter_remove", "n_clicks")],
            State("dropdown-container-div", "children"),
           # suppress_callback_exceptions=True,
        )
        def AddRemove_Filter(add_clicks, remove_clicks, children ):
            
            if("filter_add" == ctx.triggered_id):
               
                patched_children = Patch()
                # patched_children = target_dropdown(patched_children,self.num_filtercontrols)
                # patched_children = comparator_dropdown(patched_children, self.num_filtercontrols)
                Construct_FilterElem(patched_children, self.num_filtercontrols, self.allFiveAttributes)
                self.num_filtercontrols = self.num_filtercontrols  +1 
                print(f" num control {self.num_filtercontrols}")

                return patched_children

            elif("filter_remove" == ctx.triggered_id):
                if(self.num_filtercontrols ==0):
                        return

                self.num_filtercontrols = self.num_filtercontrols - 1
                #print(children)
                filtered_components = []
                for c in children:
                    if 'children' in c['props']:
                        # Filter children components
                        filtered_children = [child for child in c['props']['children'] if child['props']['id']['index'] != self.num_filtercontrols]
                        c['props']['children'] = filtered_children
                        filtered_components.append(c)

                #print(f" num control {self.num_filtercontrols}")
                return filtered_components

    def tab3_callback(self):
         #tab3 figure callback
        @self.app.callback(
            Output(self.tab3GraphID, 'children'),
            Input('tabs_div', "value"), 
            #prevent_initial_call=True,
            #suppress_callback_exceptions=True,
        ) 

        def Update_Figure_Tab3(tab_v):
            if(tab_v == "tab1" or tab_v == "tab2"):
                return None
            #print(f"Update_Figure_Tab3:: tab {tab_v}")
            graphElem = [dcc.Graph(figure = fig, id = f"{self.tab3GraphID}_") for i, fig in enumerate( self.tab3Figs) ]
            #print(" Done Update_Figure_Tab3")
            return html.Div(graphElem)


    def CloneGraph(self, add_clicks, clear_clicks):
        

        if("coll_add_butt" == ctx.triggered_id):
            #print("CloneGraph(): ADD") 
            cloneFig = copy.deepcopy(self.figs[ self.curTabIdx]) 
            self.tab3Figs.append(cloneFig)

            return  'Done Add'
        elif("coll_clear_butt" == ctx.triggered_id):
            self.tab3Figs = []
            #print("CloneGraph(): clear") 
            return "Clear all collection"
        else:
            return ""


    def LoadDiscreteFig(self, figs, conn, graphType, callbackArr):
        self.figs = figs
       
        self.conn = conn
        self.figLevelControl = callbackArr[0]
        self.figFilterControl = callbackArr[1]
        self.figRankControl = callbackArr[2]
        self.figUpdateControl = callbackArr[3]
        self.figTab2updateControl = callbackArr[4]
       
        def ConstructControlsElem(self):

            #tab1
            otherCont_markdown, otherContElems =  Construct_OtherControls_Elem()
            lvl_markdown, lvlSliderArr = Construct_LevelSliderElem(self.levelSlider, "Level Selection", self.maxLevel)
            attriSel_markdown, attriSelArr, attriSel_style = Construct_AttriSel_DropDownElem(self.allFiveAttributes)
            uRange_markdown = dcc.Markdown("#### User Range Selection (e.g., 1-50)")
            uRangeSliderArr = ConstructTextField("Enter Range: ", self.uRangeSlider, default_field_value = "1-50")
            
            sortingTarget = ['userID'] + [elem for elem in self.allFiveAttributes] 
            sort_markdown, sortArrTab1, sortArrTab2, s_style =  Construct_Sorting_Elem(sortingTarget)
            filter_markdown, filterElems, filter_content_div, filter_style = Construct_Filter_Template()
            p_markdown, percentileArr,p_style = Construct_RankElem("rank", self.allFiveAttributes)
            send_markdown, sendArr =   Construct_SendToUnityElem()
            
            #tab2
            funcNameArr= ["Avg", "Std", "Median", "SuccessRate", "Proportion"]
            attriSel_markdown_t2, attriSelArr_t2, attriSel_style_t2 = Construct_AttriSel_Tab2(self.allFiveAttributes, funcNameArr)
            proportionArr, proportionstyle =    ConstructProportion_Tab2()


            controlsElemArr = []
        
            # add extra dropdown element for these two graph type
            if((graphType == GraphType.Piechart.value) or(graphType == GraphType.Histogram.value)):
                    controlsElemArr += [ attriSel_markdown,html.Div(attriSelArr, style = attriSel_style) ]
            else:
                controlsElemArr += [html.Div(attriSelArr,  style={'display': 'none'}) ]
            
            controlsElemArr += [
                otherCont_markdown, html.Div(otherContElems),
                lvl_markdown, html.Div(lvlSliderArr),
                uRange_markdown, html.Div(uRangeSliderArr), 
                
                html.Div([filter_markdown, filterElems[0], filterElems[1]], style = filter_style),
                filter_content_div,
                
                p_markdown, html.Div(percentileArr, style = p_style),
                sort_markdown, html.Div(sortArrTab1, style = s_style),
                send_markdown, html.Div(sendArr),

                #hide tab 2
                html.Div(attriSelArr_t2, style={'display': 'none'}),
                html.Div(proportionArr, style={'display': 'none'}),
                html.Div(sortArrTab2, style = {'display': 'none'}),
                
            ]
            tab1Arr = [dcc.Graph(id = self.tab1GraphID,  figure=self.figs[0])] + controlsElemArr
            
          
            controlsElemArr2 = [
                uRange_markdown, html.Div(uRangeSliderArr), 
                attriSel_markdown_t2, html.Div(attriSelArr_t2),
                html.Div(proportionArr, style = proportionstyle),
                sort_markdown, html.Div(sortArrTab2, style = s_style), # we only want sortOder UI not sort target
                
                #hide 
                html.Div(attriSelArr, style = {'display': 'none'}),
                html.Div(lvlSliderArr,style={'display': 'none'}),
                html.Div(percentileArr, style={'display': 'none'}),
                html.Div(sortArrTab1, style = {'display': 'none'}),
                html.Div(sendArr, style={'display': 'none'}),
               
            ]
            tab2Arr = [dcc.Graph(id = self.tab2GraphID,  figure=figs[1])] + controlsElemArr2

            controlsElemArr3 = [
                #hide 
                html.Div(uRangeSliderArr, style = {'display': 'none'}),
                html.Div(attriSelArr_t2, style = {'display': 'none'}),
                html.Div(proportionArr, style = {'display': 'none'}),
              
                html.Div(sortArrTab2, style = {'display': 'none'}),

                html.Div(attriSelArr, style = {'display': 'none'}),
                html.Div(lvlSliderArr,style={'display': 'none'}),
                html.Div(percentileArr, style={'display': 'none'}),
                html.Div(sortArrTab1, style = {'display': 'none'}),
                html.Div(sendArr, style={'display': 'none'}),
               
            ]

            tab3Arr = [ html.Div( 
                                #[dcc.Graph(id = f"{self.tab3GraphID}_fig",figure=figs[0])],   
                                id=self.tab3GraphID)
                        ] + controlsElemArr3
            return tab1Arr, tab2Arr, tab3Arr
        


        tab1Arr, tab2Arr, tab3Arr = ConstructControlsElem(self)
        # initialized tab content for all tabs
        self.tab1Elem = html.Div(tab1Arr)
        self.tab2Elem = html.Div(tab2Arr)
        self.tab3Elem = html.Div(tab3Arr)
        #self.curTabIdx = 0
        self.app.layout = html.Div([
            dcc.Tabs(id="tabs_div", value='tab2', 
                children=[
                    dcc.Tab(label='Level Oriented View', value='tab1'),
                    dcc.Tab(label='User Oriented View', value='tab2'),
                    dcc.Tab(label='Collection View', value='tab3'),
                ]
            ),

            html.Div(id='tab_content'),

            html.Div(id='tab_hide', children = [ self.tab2Elem, self.tab1Elem, self.tab3Elem], style = {'display': 'none'}),
        ])
    
        print("done load graph")
    
    
    
    def SwitchTabCallback(self,tab):

        if tab == 'tab1':
            self.curTabIdx = 0
            print(f"cur index after switch tab {self.curTabIdx}")
            return self.tab1Elem
        elif tab == 'tab2':
            self.curTabIdx = 1
            print(f"cur index after switch tab {self.curTabIdx}")
            return self.tab2Elem
        elif tab == 'tab3':
            self.curTabIdx =2
            print(f"cur index after switch tab {self.curTabIdx}")
            return self.tab3Elem
        else:
            print(f"[Error] Undefine tab {tab}")
        

    def StartApp(self):
        self.isRun = True
        self.app.run_server(host='127.0.0.3', port=8060, debug=True, use_reloader=False)
        self.figLevelControl = None
     

    def ShowClickableData(self, points): #trace, points, selector
        if(points is None):
            return ""
        #print(f" ShowClickableData:: {points}")
        first_point = points['points'][0]

        # if fig is bar graph, we get label from 'label' sec
        if 'label' in first_point and first_point['label']:
            print(f"clicked data = {first_point['label']}")
            return first_point['label']

        #else we get label from trace
        curve_number = points['points'][0] ['curveNumber'] 
        trace_name = self.figs[self.curTabIdx]['data'][curve_number]['name']

        if(trace_name is None):
            trace_name = first_point['x']
        print(f" clicked data2 = {trace_name}")
        return  trace_name


    def SendToUnity(self, n_clicks, value):
        self.conn.sendall(value.encode('utf-8'))
        return 'Message "{}"  is send'.format(value)

    def LoadClusterFig(self, fig, conn):
       
        self.conn = conn  
        lvl_markdown, lvlSliderArr = Construct_LevelSliderElem(self.levelSlider, "Level Selection", self.maxLevel)
        p_markdown, percentileArr,p_style = Construct_RankElem("rank", self.allFiveAttributes)
        send_markdown, sendArr =     Construct_SendToUnityElem()
        
        #element to be hide in display
        otherCont_markdown, otherContElems =  Construct_OtherControls_Elem()
        filter_markdown, filterElems, filter_content_div, filter_style = Construct_Filter_Template()

        sortingTarget = ['userID'] + [elem for elem in self.allFiveAttributes] 
        sort_markdown, sortArrTab1, sortArrTab2, s_style =  Construct_Sorting_Elem(sortingTarget)
        uRangeSliderArr = ConstructTextField("Enter Range: ", self.uRangeSlider, default_field_value = "1-50")
        _, attriSelArr, _ = Construct_AttriSel_DropDownElem(self.allFiveAttributes)
        funcNameArr= ["Avg", "Std", "Median", "SuccessRate", "Proportion"]
        _, attriSelArr_t2, _ = Construct_AttriSel_Tab2(self.allFiveAttributes, funcNameArr)
        proportionArr, _ =    ConstructProportion_Tab2()
        
        elementArr = [
            dcc.Graph(id =self.tab1GraphID,  figure=fig),
            send_markdown, html.Div(sendArr),
           

           #hide tab 2 
            html.Div(uRangeSliderArr, style = {'display': 'none'}),
            html.Div(attriSelArr_t2, style = {'display': 'none'}),
            html.Div(proportionArr, style = {'display': 'none'}),
            html.Div(sortArrTab2, style = {'display': 'none'}),
            #hide tab1
            html.Div(otherContElems, style = {'display': 'none'}),
           html.Div([filter_markdown, filterElems[0], filterElems[1], filter_content_div], style = {'display': 'none'}),
            html.Div(attriSelArr, style = {'display': 'none'}),

            
            html.Div(lvlSliderArr,style={'display': 'none'}),
            html.Div(percentileArr, style={'display': 'none'}),
            html.Div(sortArrTab1, style = {'display': 'none'}),
            html.Div(sendArr, style={'display': 'none'}),
            # hide tab section
            html.Div([
                lvl_markdown,
            dcc.Tabs(id="tabs_div", value='tab1' ),
            html.Div(id='tab_content', children = None),
            dcc.Graph(id =self.tab2GraphID,  figure=None),
            html.Div(id =self.tab3GraphID)], style = {'display': 'none'})
        ]

        self.app.layout = html.Div(elementArr)
        print("done load graph")
    

    def LoadContinFig(self, figs, conn, levelCallback, figUpdateCallback):

        if(figs[0] == None):
            self.app.layout = html.Div([html.h4("null figure")])

        self.conn = conn
        self.figs = figs
        
        self.attriSelControl = None
        self.figLevelControl = levelCallback
        self.figRankControl = None
        self.figUpdateControl = figUpdateCallback

        lvl_markdown, lvlSliderArr = Construct_LevelSliderElem(self.levelSlider, "Level Selection", self.maxLevel)
        attriSel_markdown, attriSelArr, _ = Construct_AttriSel_DropDownElem(self.allFiveAttributes)
        uRange_markdown = dcc.Markdown("#### User Range Selection (e.g., 1-50)")
        uRangeSliderArr = ConstructTextField("Enter Range: ", self.uRangeSlider, default_field_value = "1-50")
        p_markdown, percentileArr,_ = Construct_RankElem("rank", self.allFiveAttributes)
        send_markdown, sendArr =     Construct_SendToUnityElem()
       
        #element to be hide in display
        otherCont_markdown, otherContElems =  Construct_OtherControls_Elem()
        filter_markdown, filterElems, filter_content_div, filter_style = Construct_Filter_Template()
        sortingTarget = ['userID'] + [elem for elem in self.allFiveAttributes] 
        sort_markdown, sortArrTab1, sortArrTab2, s_style =  Construct_Sorting_Elem(sortingTarget)
        attriSel_markdown, attriSelArr, _ = Construct_AttriSel_DropDownElem(self.allFiveAttributes)
        funcNameArr= ["Avg", "Std", "Median", "SuccessRate", "Proportion"]
        _, attriSelArr_t2, _ = Construct_AttriSel_Tab2(self.allFiveAttributes, funcNameArr)
        proportionArr, _ =    ConstructProportion_Tab2()

        elementArr = [
            dcc.Graph(id = self.tab1GraphID,  figure=figs[self.curTabIdx]),
            lvl_markdown, html.Div(lvlSliderArr),
            uRange_markdown, html.Div(uRangeSliderArr), 
            send_markdown, html.Div(sendArr),
          

            #hide tab 2 
            html.Div(uRangeSliderArr, style = {'display': 'none'}),
            html.Div(attriSelArr_t2, style = {'display': 'none'}),
            html.Div(proportionArr, style = {'display': 'none'}),
            html.Div(sortArrTab2, style = {'display': 'none'}),
            #hide tab1
            html.Div(otherContElems, style = {'display': 'none'}),
            html.Div([filter_markdown, filterElems[0], filterElems[1], filter_content_div], style = {'display': 'none'}),
            html.Div(attriSelArr, style = {'display': 'none'}),
            html.Div(lvlSliderArr,style={'display': 'none'}),
            html.Div(percentileArr, style={'display': 'none'}),
            html.Div(sortArrTab1, style = {'display': 'none'}),
            html.Div(sendArr, style={'display': 'none'}),

            # hide tab section
            html.Div([
            dcc.Tabs(id="tabs_div", value='tab1' ),
            html.Div(id='tab_content', children = None),
            dcc.Graph(id =self.tab2GraphID,  figure=None),
            html.Div(id =self.tab3GraphID)], style = {'display': 'none'})
        
        ]
       
        self.app.layout = html.Div(elementArr)

        
        
        
        print("done load graph")
   

    def UpdateLvlSliderOutput(self, value):
        return '#### Level Selection:: Level {}'.format(value)
