# -*- coding: utf-8 -*-
"""Monte Carlo Simulation.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/16En8qrNK-S_z8pSTJhULAiQS9KM8eaOr
"""

import random
import numpy as np 
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import time
import cv2
from numba import njit
import os
print(os.getcwd())

img=mpimg.imread('SKIN_IMAGE.png')
print(img.shape)
plt.rcParams["figure.figsize"] = (18,18)
plt.imshow(img)
plt.xticks([])
plt.yticks([])
plt.show()

mua_d = np.array([0,0.2,0.15,0.2,0.8,2,0.1])
mus_d = np.array([2000,350,50,120,90,120,100])
g_d = np.array([0.9999,0.90,0.95,0.85,0.9,0.95,0.9])
n_d = np.array([1,1.49,1.38,1.36,1.4,1.35,1.4])
d = 0.04
l = 0.05
w = 0.05
radius = 0.005
Nphotons = 50000
dr = w/1000
dz = d/400
NX = int(w/dr)
NY = int(l/dr)
NZ = int(d/dz)
threshold = 0.00001
m = 10

TISSUE = np.zeros(NX*NZ)
img_ravel = img.reshape(NX*NZ,4)
TISSUE[np.sum(img_ravel == [1,0,0,1],axis=1) == 4] = 0
TISSUE[np.sum(img_ravel == [1,1,0,1],axis=1) == 4] = 1
TISSUE[np.sum(img_ravel == [0,1,0,1],axis=1) == 4] = 2
TISSUE[np.sum(img_ravel == [0,0,1,1],axis=1) == 4] = 3
TISSUE[np.sum(img_ravel == [0,1,1,1],axis=1) == 4] = 4
TISSUE[np.sum(img_ravel == [1,0,1,1],axis=1) == 4] = 5
TISSUE[np.sum(img_ravel == [1,1,1,1],axis=1) == 4] = 6
TISSUE = TISSUE.reshape(NZ,NX)
TISSUE = np.int_(TISSUE.T).ravel()
print(TISSUE.shape)

@jit()
def Monte_Carlo(num,w,l,d,dr,dz,radius,mua_d,mus_d,g_d,threshold,m):
    x = np.random.rand(num) * w
    y = np.random.rand(num) * l
    z = np.zeros(num)
    s_total = np.zeros(num)
    W = np.ones(num)
    ux = np.zeros(num)
    uy = np.zeros(num)
    uz = np.ones(num)
    UZ = np.zeros(num)
    NX = np.int_(w/dr)
    NY = np.int_(l/dr)
    NZ = np.int_(d/dz)
    iteration = 1000
    F = np.zeros(NX*NZ)
    REF = 0
    state = np.ones(num, dtype=bool)
    ref_state = np.zeros(num, dtype=bool)
    exist_num = np.int_(np.sum(state))
    """ Monte Carlo Major Cycle """
    for i in range(iteration):
        exist_num = np.int_(np.sum(state))
        """if all the photon DEAD --> output result"""
        if(i%10==0):
            print(exist_num)
        if(exist_num==0):
            print(i)
            #TIME = time.time()-start
            break
        """move the photon"""
        NOW_a = np.int_(x[state]/dr)
        NOW_c = np.int_(z[state]/dz)
        NOW_INDEX = np.int_(NOW_a*NZ+NOW_c)
        mua = mua_d[TISSUE[NOW_INDEX]] 
        mus = mus_d[TISSUE[NOW_INDEX]] 
        g = g_d[TISSUE[NOW_INDEX]]
        sleft = -np.log(np.random.rand(exist_num))
        s = sleft/mus 
        temp_x = x[state] + s*ux
        temp_y = y[state] + s*uy
        temp_z = z[state] + s*uz
        INDEX = np.argwhere(state).ravel()
        pre_state = state.copy()
        while(np.sum(sleft!=0)!=0):
            pre_x = x.copy()
            pre_y = y.copy()
            pre_z = z.copy()
            sleft_INDEX = np.argwhere(sleft!=0).ravel()
            sleft_INDEX_w = INDEX[sleft_INDEX]
            """previous step tissue type"""
            PRE_a = np.int_(x[sleft_INDEX_w]/dr)
            PRE_b = np.int_(y[sleft_INDEX_w]/dr)
            PRE_c = np.int_(z[sleft_INDEX_w]/dz)
            PRE_INDEX = PRE_a*NZ+PRE_c
            """current step tissue type"""
            CUR_a = np.int_(temp_x[sleft_INDEX]/dr)
            CUR_b = np.int_(temp_y[sleft_INDEX]/dr)
            CUR_c = np.int_(temp_z[sleft_INDEX]/dz)
            CUR_INDEX = CUR_a*NZ+CUR_c
            """boolen for change of tissue type"""
            SAME_TYPE = (CUR_INDEX == PRE_INDEX)
            """current voxel == previous voxel"""
            sleft_INDEX_w_ST = sleft_INDEX_w[SAME_TYPE]
            sleft_INDEX_ST = sleft_INDEX[SAME_TYPE]
            x[sleft_INDEX_w_ST] = temp_x[sleft_INDEX_ST]
            y[sleft_INDEX_w_ST] = temp_y[sleft_INDEX_ST]
            z[sleft_INDEX_w_ST] = temp_z[sleft_INDEX_ST]
            absorb = W[sleft_INDEX_w_ST]*(1-np.exp(-mua[sleft_INDEX_ST]*sleft[sleft_INDEX_ST]))
            W[sleft_INDEX_w_ST] -= absorb
            F[PRE_INDEX[SAME_TYPE]] += absorb
            sleft[sleft_INDEX_ST] = 0
            """current voxel != previous voxel"""
            sleft_INDEX_w_DT = sleft_INDEX_w[~SAME_TYPE]
            sleft_INDEX_DT = sleft_INDEX[~SAME_TYPE]
            CHANGE_TYPE_INDEX = np.argwhere(~SAME_TYPE).ravel()
            CHANGE_TYPE_NUMBER = len(CHANGE_TYPE_INDEX)
            ix2 = np.zeros(CHANGE_TYPE_NUMBER)
            iy2 = np.zeros(CHANGE_TYPE_NUMBER)
            iz2 = np.zeros(CHANGE_TYPE_NUMBER)
            bool_ux = (ux[sleft_INDEX_DT]>=0)
            bool_uy = (uy[sleft_INDEX_DT]>=0)
            bool_uz = (uz[sleft_INDEX_DT]>=0)
            ix2[bool_ux] = PRE_a[CHANGE_TYPE_INDEX[bool_ux]]+1
            ix2[~bool_ux] = PRE_a[CHANGE_TYPE_INDEX[~bool_ux]]
            iy2[bool_uy] = PRE_b[CHANGE_TYPE_INDEX[bool_uy]]+1
            iy2[~bool_uy] = PRE_b[CHANGE_TYPE_INDEX[~bool_uy]]
            iz2[bool_uz] = PRE_c[CHANGE_TYPE_INDEX[bool_uz]]+1
            iz2[~bool_uz] = PRE_c[CHANGE_TYPE_INDEX[~bool_uz]]
            ux[sleft_INDEX_DT] += 10**-7
            uy[sleft_INDEX_DT] += 10**-7
            uz[sleft_INDEX_DT] += 10**-7
            xs = abs((ix2*dr - x[sleft_INDEX_w_DT])/ux[sleft_INDEX_DT])
            ys = abs((iy2*dr - y[sleft_INDEX_w_DT])/uy[sleft_INDEX_DT])
            zs = abs((iz2*dz - z[sleft_INDEX_w_DT])/uz[sleft_INDEX_DT])
            s_t = 10**-7+np.minimum(np.minimum(xs,ys),zs)
            absorb = W[sleft_INDEX_w_DT]*(1-np.exp(-mua[sleft_INDEX_DT]*s_t))
            W[sleft_INDEX_w_DT] -= absorb
            F[PRE_INDEX[~SAME_TYPE]] += absorb
            x[sleft_INDEX_w_DT] += s_t * ux[sleft_INDEX_DT]
            y[sleft_INDEX_w_DT] += s_t * uy[sleft_INDEX_DT]
            z[sleft_INDEX_w_DT] += s_t * uz[sleft_INDEX_DT]
            sleft[sleft_INDEX_DT] -=  s_t*mus[sleft_INDEX_DT]
            BOOL_CHECK = sleft[sleft_INDEX_DT] <= 10**-7
            sleft[sleft_INDEX_DT[BOOL_CHECK]] = 0
            UPD_a = np.int_(x[sleft_INDEX_w_DT]/dr)
            UPD_b = np.int_(y[sleft_INDEX_w_DT]/dr)
            UPD_c = np.int_(z[sleft_INDEX_w_DT]/dz)
            UPD_INDEX = np.int_(UPD_a*NZ+UPD_c)
            CROSS_BOUND = (UPD_INDEX<NX*NZ)
            mua[sleft_INDEX_DT[CROSS_BOUND]] = mua_d[TISSUE[UPD_INDEX[CROSS_BOUND]]]
            mus[sleft_INDEX_DT[CROSS_BOUND]] = mus_d[TISSUE[UPD_INDEX[CROSS_BOUND]]]
            g[sleft_INDEX_DT[CROSS_BOUND]] = g_d[TISSUE[UPD_INDEX[CROSS_BOUND]]]
            """Compute Total Step Size"""
            s_total += np.sqrt((x-pre_x)**2 + (y-pre_y)**2 + (z-pre_z)**2)
            """check for boundary"""
            case1 = UPD_a>=NX
            case2 = UPD_a<0
            case3 = UPD_b>=NY
            case4 = UPD_b<0
            case5 = UPD_c>=NZ
            case6 = UPD_c<0
            ref_state[sleft_INDEX_w_DT[case6]] = True
            UZ[sleft_INDEX_w_DT[case6]] = uz[sleft_INDEX_DT[case6]]
            REF += len(sleft_INDEX_w_DT[case6])
            all_case = (case1 | case2 | case3 | case4 | case5 | case6)
            state[sleft_INDEX_w_DT[all_case]] = False
            sleft[sleft_INDEX_DT[all_case]] = 0
            """reflect"""
            """
            pre_a_index = np.int_(pre_x[state]/dr)
            pre_c_index = np.int_(pre_z[state]/dz)
            n1 = n_d[TISSUE[pre_a_index*NZ+pre_c_index]]
            cur_a_index = np.int_(x[state]/dr)
            cur_c_index = np.int_(z[state]/dz)
            n2 = n_d[TISSUE[cur_a_index*NZ+cur_c_index]]
            cross_bound_index = np.array(np.where(n1!=n2)).ravel()
            normal = np.array(uz[cross_bound_index] > (1-10**-12), dtype=bool) 
            paralell = np.array(uz[cross_bound_index] < 10**-6, dtype=bool)
            uz[cross_bound_index[paralell]] = 0
            others = np.logical_and(~normal, ~paralell)
            costheta1 = uz[cross_bound_index[others]]
            sintheta1 = np.sqrt(1 - costheta1 * costheta1)
            sintheta2 = n1[cross_bound_index[others]] * sintheta1 / n2[cross_bound_index[others]]
            total_reflect = (sintheta2 >= 1)
            uz[(cross_bound_index[others])[total_reflect]] = 0
            costheta2 = np.sqrt(1 - sintheta2[~total_reflect] * sintheta2[~total_reflect])
            uz[(cross_bound_index[others])[~total_reflect]] = costheta2
            """
        """update the direction"""
        state_temp = state[pre_state]
        ux = ux[state_temp]
        uy = uy[state_temp]
        uz = uz[state_temp]
        mua = mua[state_temp]
        mus = mus[state_temp]
        g = g[state_temp]
        exist_num = np.sum(state)
        psi = 2*np.pi*np.random.rand(exist_num)
        temp = (1.0 - g * g) / (1.0 - g + 2 * g * np.random.rand(exist_num))
        costheta = (1.0 + g * g - temp * temp) / (2.0 * g)
        sintheta = np.sqrt(1-costheta**2)
        cospsi = np.cos(psi)
        psi_bool = psi < np.pi
        sinpsi = np.zeros(exist_num)
        cospsi_2 = cospsi*cospsi
        sinpsi[psi_bool] = np.sqrt(1.0 - cospsi_2[psi_bool])
        sinpsi[~psi_bool] = -np.sqrt(1.0 - cospsi_2[~psi_bool])
        uxx=np.zeros(exist_num)
        uyy=np.zeros(exist_num)
        uzz=np.zeros(exist_num)
        perpend = abs(uz) > 0.99999
        uxx[perpend] = sintheta[perpend] * cospsi[perpend]
        uyy[perpend] = sintheta[perpend] * sinpsi[perpend]
        uzz[perpend] = costheta[perpend] * np.sign(uz[perpend]) * uz[perpend]
        temp = np.sqrt(1.0 - uz[~perpend] * uz[~perpend])
        uxx[~perpend] = sintheta[~perpend] * (ux[~perpend] * uz[~perpend] * cospsi[~perpend] - uy[~perpend] * sinpsi[~perpend])/ temp + ux[~perpend] * costheta[~perpend]
        uyy[~perpend] = sintheta[~perpend] * (uy[~perpend] * uz[~perpend] * cospsi[~perpend] + ux[~perpend] * sinpsi[~perpend]) / temp + uy[~perpend] * costheta[~perpend]
        uzz[~perpend] = -sintheta[~perpend] * cospsi[~perpend] * temp + uz[~perpend] * costheta[~perpend]
        ux = uxx
        uy = uyy
        uz = uzz
        """roulette"""
        weight_bool = W[state] < threshold
        num_low = np.sum(weight_bool)
        if(num_low>0):
            check = np.random.rand(num_low) < 1/m
            pre_index = np.argwhere(state).ravel()[weight_bool]
            state_temp = state[state]
            W[pre_index[check]] *= m
            W[pre_index[~check]] = 0
            state[pre_index[~check]] = False
            index = np.argwhere(weight_bool).ravel()[~check]
            state_temp[index] = False
            ux = ux[state_temp]
            uy = uy[state_temp]
            uz = uz[state_temp]
            mua = mua[state_temp]
            mus = mus[state_temp]
            g = g[state_temp]
    return F, W, x, s_total, ref_state, UZ

start = time.time()
F, W, x, s_total, ref_state, UZ = Monte_Carlo(500000,w,l,d,dr,dz,radius,mua_d,mus_d,g_d,threshold,m)
print(time.time()-start)

plt.rcParams["figure.figsize"] = (18,9)
F_log = F.copy()/Nphotons+1
F_log = F_log.reshape(NX,NZ)
F_log = np.log(F_log)
plt.imshow(F_log.T,cmap="gray")
plt.xticks([])
plt.yticks([])
plt.show()

k= np.arange(np.int_(2*np.pi/0.000089),np.int_(2*np.pi/0.000079),10)
OCT_IMAGE = np.zeros((4470,NX))
ACCEPT_ANGLE = abs(UZ[ref_state])>=np.sin(np.pi*50/180)
ref_index = np.argwhere(ref_state).ravel()
x_ref = x[ref_index[ACCEPT_ANGLE]]
s_total_ref = s_total[ref_index[ACCEPT_ANGLE]]
W_ref = W[ref_index[ACCEPT_ANGLE]]
for i in range(NX):
    BOOL = (np.int_(x_ref/dr) == i)
    OCT_signal = np.dot(np.exp(1j*np.outer(k,s_total_ref[BOOL])),np.sqrt(W_ref[BOOL]))
    OCT_signal = OCT_signal / np.sum(BOOL);
    I = (abs(OCT_signal+1))**2 - (abs(OCT_signal -1))**2
    I = I*np.hamming(len(k))
    M10 = len(I)*10
    Y10 = np.fft.fft(I,M10)
    Y10 = Y10[:np.int_(len(Y10)/2)]
    Y10 = np.log(Y10+1)
    OCT_IMAGE[:,i] = Y10
plt.figure(figsize = (18,9))
plt.imshow(OCT_IMAGE[:1000,:],cmap="gray")
plt.xticks([])
plt.yticks([])
plt.show()
plt.plot(np.arange(4470),OCT_IMAGE[:,500])
plt.show()

