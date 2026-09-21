def Method_CovarianceMatrix(data, numJoint, uppTriLen):
    N = len(data)
    print(f"num sample is {N} numJoint {numJoint} uppTriLen {uppTriLen}")
    final = np.zeros((N,  uppTriLen))
    
    for i in range(data.shape[0]):
        #each XYZ is  J X T
        X = np.squeeze(data[i, 0, :]).T 
        Y = np.squeeze(data[i, 1, :]).T
        Z = np.squeeze(data[i, 2, :]).T
        #print(f"x = {X.shape}\n x = {X[:5]}\n y = {Y[:5]}\n z= {Z[:5]}\n") 
       
        # Goal: construct  col vector S [x1, ..., xJ , y1, ..., yJ, z1, ..., zJ ]'
        S = np.concatenate((X, Y, Z), axis=0) # Concatenate arrays along axis 1 to interleave the rows; shape (3, 12)
        #print(f"S = {S.shape}")
        # Reshape into (3XJ, T)
        S = S.reshape(-1, X.shape[0]) # reshape into 
        #print(f"S = {S.shape}")
        C = np.cov(S, rowvar= True) # C should have 3J X 3J size

      
        upper_triangular  = C[np.triu_indices(C.shape[0])] 
        
        normalized_data = normalize(upper_triangular.reshape(1, -1), norm='max', axis=1)
        #print(f"upper_triangular ={upper_triangular } \n normalized={normalized_data}")
        #print( f"normalized_data {len(normalized_data)} {len(normalized_data[0])} " )
        final[i] =  normalized_data
    return final


def ResizeArr(arr):
    def DetermineSize(arr):
        #approach 1 find avg length
        # avg = 0
        # for i in range(len(arr)):
        #     avg += len(arr[i]) 
        # avg /= len(arr)
        # return np.ceil(avg)

        #approach 2 find the max length
        lengths = np.array([len(sublist) for sublist in arr])
      
        return np.max(lengths)
        
    avgSize = DetermineSize(arr).astype(int)
    print(f"avgSize{avgSize}")
    first = TimeSeriesResampler(sz = avgSize).fit_transform(arr[0])
    X_train = np.array(first)

    for i in range(1, len(arr)):
        #print(f"before {X_train.shape}")
        path = arr[i]
        final_path = TimeSeriesResampler(sz = avgSize).fit_transform(path)
        X_train = np.append(X_train,  final_path, axis =0)
    #print(f"after {X_train.shape}")
    return X_train



# def Preprocess_3dPos(plyr_pos, frameToSkip):
#     arr = []
#     for path in plyr_pos:
        
#         path = path[::frameToSkip]
#         xz = [[x,z] for x,y,z in path]
#         arr.append(xz)
#     return arr
    
from tslearn.datasets import CachedDatasets
from tslearn.preprocessing import TimeSeriesScalerMeanVariance, \
    TimeSeriesResampler
from tslearn.clustering import TimeSeriesKMeans
from sklearn.decomposition import PCA
from plotly.subplots import make_subplots
from sklearn.preprocessing import normalize
def cart2pol(x, y):
    '''
    Parameters:
    - x: float, x coord. of vector end
    - y: float, y coord. of vector end
    Returns:
    - r: float, vector amplitude
    - theta: float, vector angle
    '''

    z = x + y * 1j
    r,theta = np.abs(z), np.angle(z)
    return r,theta
def CalDirection(cur, prev):
    dir = np.array(cur) - np.array(prev)
    dist = np.linalg.norm(dir)
    if(np.abs(dist) < 1e-6):
        dir = np.array([0,0])
    else:
        dir = dir/dist
    return dir
# copnvert to 1d radian
def Pos2Radian(plyr_pos, frameToSkip):
    arr = []
    for path in plyr_pos:
        radian_arr = []
        path = path[::frameToSkip]
        for i in range(1, len(path)):
            
            dir = CalDirection(path[i], path[i-1])
            _, radian = cart2pol(dir[0], dir[2]) # here we only consider x,z
            radian_arr.append(radian)
        arr.append(radian_arr)
    return arr


def CalDistVelAcc(posArr, hasSkip):
    
    # time in second 
    # time = np.arange(0, len(posArr), skip)
    # time = time / skip
    #dt = np.diff(time)
    distance_vect = np.diff(np.array(posArr), axis = 0) 

    distance_mag = np.linalg.norm(distance_vect, axis =1)

    acc_dist = 0
    accumulate_distArr = []
    for v_m in distance_mag:
        acc_dist = acc_dist + v_m
        accumulate_distArr +=[acc_dist]

     # delta time bet each point = 0.05(fps) * #skip frames
    dt = np.full((len(posArr) -1), hasSkip*0.05 )
    

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

def Method_VelACC(plyr_pos, hasSkip):
    arr = []
    for path in plyr_pos:
        dir_arr = []
        
        accDist, vel, acc = CalDistVelAcc(path, hasSkip )
        #print(vel[:10])
        
        arr.append(vel)
    return arr
# convert to direction vector
def Pos2Traj(plyr_pos):

    arr = []
    for path in plyr_pos:
        dir_arr = []
        for i in range(1, len(path)):
            dir = CalDirection(path[i], path[i-1])
            
            dir_arr.append(dir)
        arr.append(dir_arr)
    return arr
def Method_ExtractXOrZPos(plyr_pos, posIdx):
    arr = []
    for path in plyr_pos:
        radian_arr = []
        
        for i in range(len(path)):
            
            t = path[i][posIdx]
            radian_arr.append(t)
        arr.append(radian_arr)
    return arr

def Method_PCA(plyr_pos):
    arr = []
    pca = PCA(n_components=1)
    
    for path in plyr_pos:
        radian_arr = []
        pca_X = pca.fit_transform(path).reshape(-1)
        pca_detail = pca.fit(path)
        print('Explained variation per principal component: {}'.format(pca_detail.explained_variance_ratio_))
        
        
        arr.append(pca_X)
    #print(arr)
    return arr
   



def Method_CovarianceMatrix(data, numJoint, uppTriLen ):
    N = len(data)
    print(f"num sample is {N} numJoint {numJoint} uppTriLen {uppTriLen}")
    final = np.zeros((N,  uppTriLen))
    for i in range(data.shape[0]):
        #each XYZ is  J X T
        X = np.squeeze(data[i, 0, :, :]).T 
        Y = np.squeeze(data[i, 1, :, :]).T
        Z = np.squeeze(data[i, 2, :, :]).T
        #print(f"x = {X.shape}\n x = {X[:5]}\n y = {Y[:5]}\n z= {Z[:5]}\n") 
       
        # Goal: construct  col vector S [x1, ..., xJ , y1, ..., yJ, z1, ..., zJ ]'
        S = np.concatenate((X, Y, Z), axis=0) # Concatenate arrays along axis 1 to interleave the rows; shape (3, 12)
        #print(f"S = {S.shape}")
        # Reshape into (3XJ, T)
        S = S.reshape(-1, X.shape[0]) # reshape into 
        #print(f"S = {S.shape}")
        C = np.cov(S, rowvar= True) # C should have 3J X 3J size

      
        upper_triangular  = C[np.triu_indices(C.shape[0])] 
        
        normalized_data = normalize(upper_triangular.reshape(1, -1), norm='max', axis=1)
        #print(f"upper_triangular ={upper_triangular } \n normalized={normalized_data}")
        #print( f"normalized_data {len(normalized_data)} {len(normalized_data[0])} " )
        final[i] =  normalized_data
    return final


























def ConstructTrainingSet(df):
    
    raw_pos = df['plyr_pos'].values
    pos_data = Preprocess_3dPos(raw_pos, frameToSkip)
    print(f"data size {pos_data.shape}")
    #approach 4 construct covariance Matrix
    J = 1
    diagnoal_len = int(3*J * (3*J +1)/2) 
    X_train = Method_CovarianceMatrix(pos_data, J, diagnoal_len)
    # # approach 1 directional unit vector over time
    #trajPath = Pos2Traj(pos_data)
    #X_train = Method_PCA(pos_data)
    
    #approach 2 only look at x pos over time
    #X_train = Method_ExtractXOrZPos(pos_data, 1)

    # ##approach 3 look at vel/acc over time
    #X_train = Method_VelACC (pos_data, frameToSkip)   
    
    # resize the arr so that each time series has same length 
    # X_train = ResizeArr(X_train)

    # r.shape
    print(f"traing set shape {X_train.shape}")
    return X_train,pos_data


j1 = [[1],[1],[1],[1],[1]] # frames infor for each joint
j2 = [[2],[3],[1],[1],[1]]
j3 = [[10],[20],[30],[1],[1]]
j4 = [[40],[4],[1],[16],[18]]

# j1 = [1] # joints infor
# j2 = [2]
# j3 = [3]""
# j4 = [4]

x1 = [j1,j2,j3,j4]#loc x,  4 joint 
y1 = [j2,j1,j3,j4]
z1 = [j4,j3,j3,j4]


s1 = [x1,y1,z1]
s2 = [x1,y1,y1]
x = np.array([s1,s2,s1]) # x contain two sampel sequences

final = dataCov(x)
final



def GraphPath(df,skipframe = -1):
    colors =["red", "green", "blue", "DarkSlateGrey","MediumPurple","LightSkyBlue", "yellow", "purple"]
    fig = go.Figure()
    for ci in range(numcluster):
            
        filter = y_predit == ci
        for fi in range(len(filter)):
           
            if(not filter[fi]): #if it is not same cluster skip current user
                continue
            #get user id 
            userID = df['userID'][fi]

            filterDf = df[(df['userID'] == userID)]
            #print(userID)
            walkPath = filterDf['plyr_pos'].values[0]
            if(skipframe != -1):
                walkPath = walkPath[::skipframe]

            distance, velocities, acceleration = CalDistVelAcc(walkPath, skipframe)

            traceName = f'user{str(userID)}_cluser{ci+1}'
            
            def GraphWalkPath(walkPath):
                x_coords = list(map(lambda pos: pos[0], walkPath))
                z_coords = list(map(lambda pos: pos[2], walkPath))
                trace = go.Scatter(
                    x =  x_coords,
                    y =  z_coords,
                    name =  f'{traceName}',
                    legendgroup= f"cluser{ci}",
                    marker=dict(size=5, color = colors[ci]),
                )
                return trace
            def GraphAccDist(distance):
                trace = go.Scatter(
                x = [ i for i in range(len(distance)) ],
                y =  distance,
                name =  f'{traceName}_dist',
                legendgroup=f"cluser{ci}",
                marker=dict(size=5, color = colors[ci]),
                )
                return trace
            def GraphAcceleration(acceleration):
                trace = go.Scatter(
                    x = [ i for i in range(len(acceleration)) ],
                    y =  acceleration,
                    name =  f'{traceName}_acc',
                    legendgroup=f"cluser{ci}",
                    marker=dict(size=5, colorscale = 'Picnic'),
                )
                return trace
            def GraphVelocity(velocities):
                trace = go.Scatter(
                    x = [ i for i in range(len(velocities)) ],
                    y =  velocities,
                    name =  f'{traceName}_vel',
                    legendgroup=f"cluser{ci}",
                    marker=dict(size=5, color = colors[ci]),
                )
                return trace
            
            trace = GraphWalkPath(walkPath)
            #trace = GraphVelocity(velocities)
            fig.add_trace(trace)
    fig.show()

GraphPath(dataset, frameToSkip)