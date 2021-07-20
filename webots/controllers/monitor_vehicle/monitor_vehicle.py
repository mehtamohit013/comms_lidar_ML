from controller import Supervisor
import numpy as np
import time
import os
import math
import scipy.io
import pandas as pd

# Data paths
HOME = os.environ['HOME']
dpath = f'{HOME}/webots_code/data/samples'
lpath = f'{HOME}/webots_code/data/lidar_samples'
gpath = f'{HOME}/webots_code/data/gps_pd.xz'

os.makedirs(dpath, exist_ok=True)
os.makedirs(lpath, exist_ok=True)

start = time.time()

robot = Supervisor()
car = robot.getName()
car_model = robot.getModel()
print(f'Starting subprocess for car {car}')


'''
Simulation timestep
    Smaller the simulation timestep, higher the accuracy for calculating power 
    using matlab,but bigger the stored file
Data Collection timestep
'''
timestep = 128
data_timestep = 1280
prev_time = 0

# Extracting the Supervisor Node
car_node = robot.getSelf()

# Base Station location in [Lat,Lon,Height]
# NUmber of Base Stations = 3
BS = np.array([
    [38.89328,-77.07611,5],
    [38.89380,-77.07590,5],
    [38.89393,-77.07644,5]
])
antenna_range = 100

lidar = robot.getDevice('Velo')
gps = robot.getDevice('gps')
gps.enable(timestep)

# Enabling Lidar
def enable_lidar(lidar):
    lidar.enable(timestep)
    lidar.enablePointCloud()

# Disabling lidar
def disable_lidar(lidar):
    lidar.disablePointCloud()
    lidar.disable()

# Determining the distance between car and transmitter in meter
# TO-DO : Consider height while calculating distance
def dist_gps(gps1, gps2):
    lat1, lon1, _ = gps1
    lat2, lon2, _ = gps2
    R = 6371000  # radius of Earth in meters
    phi_1 = math.radians(lat1)
    phi_2 = math.radians(lat2)

    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + \
        math.cos(phi_1) * math.cos(phi_2) * \
        math.sin(delta_lambda / 2.0) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

# Function for reading and saving data
def read_save_data(lidar, gps_val,BS:np.ndarray,BS_Range:np.ndarray,
                 car_model:str, car_node):
    lidar_timestep = np.zeros((288000, 3), dtype=np.float32)  # For velodyne
    cloud = lidar.getPointCloud()
    k = 0

    for i in range(0, 288000):
        if np.isfinite(cloud[i].x) and np.isfinite(cloud[i].y) and np.isfinite(cloud[i].z):
            lidar_timestep[k, 0] = float(cloud[i].x)
            lidar_timestep[k, 1] = float(cloud[i].y)
            lidar_timestep[k, 2] = float(cloud[i].z)
            k += 1
    lidar_data = lidar_timestep[:k, :]

    siml_time = robot.getTime()
    rotation = car_node.getField('rotation')

    np.savez(lpath + f'/{car}{siml_time:.1f}.npz',
             lidar=lidar_data,
             translation=car_node.getPosition(),
             rotation=rotation.getSFRotation(),
             sites = BS_Range)

    scipy.io.savemat(dpath + f'/{car}{siml_time:.1f}.mat',
                     dict(gps=gps_val, BS=BS,
                          BS_Range = BS_Range,
                          car_model=car_model,
                          siml_time = siml_time))

# Saving GPS data at every time instant
# To be used for constructing vehicular objects in MATLAB
# Using pandas to save data in a pickled format
def save_gps(timestep:float,gps_val,car_model:str):
    
    try:
        gps_pd = pd.read_pickle(gpath)
        ind = gps_pd.index.values[-1]+1
    except:
        gps_pd = pd.DataFrame(columns=['timestep','gps','model'])
        ind = 0
    
    gps_pd.loc[ind,'timestep'] = timestep
    gps_pd.loc[ind,'gps'] = gps_val
    gps_pd.loc[ind,'model'] = car_model

    gps_pd.to_pickle(gpath)


while robot.step(timestep) != -1:
    
    gps_val = gps.getValues()
    BS_dist = np.ndarray((BS.shape[0],))

    # Saving values of gps for all timesteps
    save_gps(robot.getTime(),gps_val,car_model)

    for i in range(0,BS.shape[0]):
        BS_dist[i] = dist_gps(gps_val,BS[i])

    BS_Range = (BS_dist < antenna_range).astype(int)

    if sum(BS_Range)== 3 :
        if(robot.getTime()-prev_time>(data_timestep/1000.000)):
            print(f'Car {car} is in range of {BS_Range}->[BS1,BS2,BS3]')
            prev_time = robot.getTime()
            if not lidar.isPointCloudEnabled():
                enable_lidar(lidar)
            else:
                read_save_data(lidar, gps_val,BS,BS_Range, car_model, car_node)

    else:
        if lidar.isPointCloudEnabled():
            disable_lidar(lidar)

print(f'Subprocess ended for car {car} after time {(time.time()-start):.2f}')