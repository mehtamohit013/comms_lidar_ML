from controller import  Robot
import numpy as np
import time
import os
import math
import pickle

#Location of transmitter in lat and lon
tx = [38.8939600,-77.0782300,0]

#Data path
dpath = '/home/iiti/webots/data/dicts'
os.makedirs(dpath,exist_ok=True)

time_lim = 30
start = time.time()

robot = Robot()
car = robot.getName()
print(f'Starting subprocess for car {car}')
timestep = 1280

lidar = robot.getDevice('Velo')
gps = robot.getDevice('gps')
gps.enable(timestep)
lidar_timestep = np.zeros((288000,3)) # For velodyne
data = dict()

def enable_lidar(lidar):
    lidar.enable(timestep)
    lidar.enablePointCloud()

def disable_lidar(lidar):
    lidar.disablePointCloud()
    lidar.disable()

def dist_gps(gps1,gps2):
    lat1,lon1,_ = gps1
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
    return R*c

while robot.step(timestep)!=-1:
    gps_val = gps.getValues()
    dist = dist_gps(gps_val,tx)

    if dist<100:
        print(f'Car {car} is in range of tx')
        if not lidar.isPointCloudEnabled():
            enable_lidar(lidar)
        else:
            data['gps']=gps_val
            cloud = lidar.getPointCloud()
            k = 0
            for i in range(0, 288000):
                if np.isfinite(cloud[i].x) and np.isfinite(cloud[i].y) and np.isfinite(cloud[i].z):
                    lidar_timestep[k, 0] = cloud[i].x
                    lidar_timestep[k, 1] = cloud[i].y
                    lidar_timestep[k, 2] = cloud[i].z
                    k += 1
            lidar_data = lidar_timestep[:k, :]
            data['lidar'] = lidar_data
            with open(dpath+f'/{car}_{((dist/100)+time.time()-start):.2f}.txt','wb') as a:
                pickle.dump(data,a)
        
    else:
        if lidar.isPointCloudEnabled():
            disable_lidar(lidar)

print(f'Subprocess ended for car {car} after time {(time.time()-start):.2f}')
