def ResizeAndInterpolate(players_data, skipframe = -1):
        max_frames = max(len(plyr) for plyr in players_data)
        #print(f"max frame{max_frames}")
        W = []
        for plyr_pos in players_data:
            
            np_plyr_pos = np.array(plyr_pos)
            
            if len(np_plyr_pos) < max_frames:
                # Calculate interpolation indices
                indices = np.linspace(0, len(np_plyr_pos) - 1, max_frames)
                #print(f"max z coor = { max(np_plyr_pos[:, 2]) }")
                # Perform interpolation for X, Y, Z coordinates separately
                x_interp = np.interp(indices, np.arange(len(np_plyr_pos)), np_plyr_pos[:, 0])
                y_interp = np.interp(indices, np.arange(len(np_plyr_pos)), np_plyr_pos[:, 1])
                z_interp = np.interp(indices, np.arange(len(np_plyr_pos)), np_plyr_pos[:, 2])
            
                if(skipframe != -1):
                    x_interp = x_interp[::skipframe]
                    y_interp = y_interp[::skipframe]
                    z_interp = z_interp[::skipframe] 

                # Combine interpolated values into a new pose
                #column stack: task each elem from list and group them together, then stack 
                interpolated_pose = np.column_stack((x_interp, y_interp, z_interp))
                W.append(interpolated_pose)
                    
            else:
                W.append(plyr_pos)

        W = np.array(W)
        
        return W,max_frames

 
def PreprocessingData(numJoints, joint_data, skipframe = -1):

    
    interp_Arr =[]
    max_frames = 0
    numPlayer = 11
    for joint in joint_data:
        interpolate_joint_data,max_frames = ResizeAndInterpolate(joint, skipframe)
        interp_Arr.append(interpolate_joint_data)
        
    print( f"interp = {len(interp_Arr)} should == numjoints")
    #final = np.column_stack((interp_Arr[0], interp_Arr[1], interp_Arr[2]))
    
    print( f" {interp_Arr[0].shape} shouble be numplayerX numframes X 3")
    all_players = []
    for pi in range(numPlayer):
        one_player_alljoints = np.column_stack((interp_Arr[0][pi], interp_Arr[1][pi], interp_Arr[2][pi]))
        #print( f" one_player_alljoints {one_player_alljoints.shape} ")
        reshape_alljoints = one_player_alljoints.reshape(( max_frames,numJoints,3))
        all_players.append(reshape_alljoints)
    all_players = np.array(all_players)

    #print( f" {all_players.shape} shouble be numplayer X numframes X numJoints,3")
    return all_players


def Method_CovarianceMatrix(data, numJoint, uppTriLen):
    N = len(data)
    numFrames = len(data[0])
    print(f"num sample is {N} numJoint {numJoint} uppTriLen {uppTriLen} numFrames = {numFrames}")
    print(f"final upper matric size  {uppTriLen} per sample")
    final = np.zeros((N,  uppTriLen))

    for i in range(data.shape[0]): # for all player
        plyr_pos = data[i]

        xarr =  np.array([ x for x in plyr_pos[:,:, 0]]).T  # frame, joint, jointidx
        yarr = np.array([ y for y in plyr_pos[:,:, 1]]).T
        zarr = np.array([ z for z in plyr_pos[:,:, 2]]).T
       
        if(xarr.shape[0] != numJoint or xarr.shape[1] != numFrames):
            print(f"[error] xarr is not (J , numFrames); size is{ (xarr.shape)}")
        
        #construct S, each row represents a variable, with observations in the column.
        # S = should has size (3XJ, T)
        S = np.vstack((xarr, yarr, zarr))
        if(S.shape != (numJoint*3, numFrames)):
            print(f"[error] S.shape is not (3XJ, numFrames); it is{ S.shape}")
        #
        C = np.cov(S, rowvar= True) # C should have 3J X 3J size
        if(C.shape != (3*numJoint, 3*numJoint) ):
            print(f"[error] covariance matrix size not 3J X 3J; size is{ C.shape }")
        upper_triangular  = C[np.triu_indices(C.shape[0])] 
        
        normalized_data = normalize(upper_triangular.reshape(1, -1), norm='max', axis=1)

        

        #print(f"upper_triangular ={upper_triangular } \n normalized={normalized_data}")
        #print( f"normalized_data {len(normalized_data)} {len(normalized_data[0])} " )
        final[i] =  normalized_data

    return final, C



def ConstructTrainingSet(df):

    J = 3
    raw_pos = [df['plyr_pos'].values, df['l_hand_pos'].values,df['r_hand_pos'].values]
    pose_data = PreprocessingData(J, raw_pos, frameToSkip)
    # print(f"input data size {pose_data.shape}")
    
    # #approach 4 construct covariance Matrix
    
    # diagnoal_len = int(3*J * (3*J +1)/2) 
    # X_train, C = Method_CovarianceMatrix(pose_data, J, diagnoal_len)
    #print(f"traing set shape {X_train.shape}")

    #return X_train,pose_data, C
    return pose_data
