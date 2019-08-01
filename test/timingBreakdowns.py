#!/usr/bin/env python3

'''
A script to run a seris of finufftGuru_tests with varying parameters
Captures the stdout, parses it for timing statistics, and graphs speedup
ratio trends. 
'''

import math
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
import re
import subprocess

M_srcpts = 1e5
tolerance = 1e-6
debug = 1

#modes array.
#first dimension counts are in modes[0,1,2]
#second dimension: modes[3,4,5]
#3rd dimension [6,7,8]
modes = [1e5,1,1,1e2,1e2,1,1e2,1e2,1e1]

dimensions = [1,2,3]
types = [1,2,3] 
n_trials = [1,4,10]


#data capture arrays
#Datapoints are speedup ratio := oldImplementationTime/newImplentationTime
totalTimeT1=[]
totalTimeT2=[]
totalTimeT3=[]
spreadT1=[]
spreadT2=[]
spreadT3=[]
fftwPlanT1=[]
fftwPlanT2=[]
fftwPlanT3=[]
fftT1=[]
fftT2=[]
fftT3=[]

for dim in dimensions:
    for ftype in types:
        for trial in n_trials:

            #execute the test for this set of parameters
            out =  subprocess.run(["./finufftGuru_test", str(trial), str(ftype), str(dim), 
                                  str(modes[3*(dim-1)]),str(modes[3*(dim-1)+1]),  str(modes[3*(dim-1)+2]), 
                                  str(M_srcpts), str(tolerance), str(debug)], 
                                 stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

            strOut = out.stdout.decode() #convert bytes to string

            #print(strOut)

            
            #parse the output and syphon into data arrays

            decimalMatchString = "\d+\.?\d+" #regular expression to match a decimal number
            sciNotString = "(\d*.?\d*e-\d* s)" #regular expression to match a number in scientificNotation

            ###############################################################################
            #total time speedup
            lineMatch = re.search(r'=.*$',strOut) #speedup line is the only one with an "="
            totalSpeedup = re.search(decimalMatchString, lineMatch.group(0))
            if(not totalSpeedup): #whole number speedup edge case
                totalSpeedup = re.search("\d+", lineMatch.group(0))
            totalSpeedup = float(totalSpeedup.group(0))
            
            if(ftype == 1):
                totalTimeT1.append(totalSpeedup)
            elif(ftype == 2):
                totalTimeT2.append(totalSpeedup)
            else:
                totalTimeT3.append(totalSpeedup)

            ###############################################################################
                
            #spread (old) / [sort+spread]  (new)

            newSort = 0
            lineMatch = re.findall('.*finufft_setpts.*sort.*',strOut)
            for match in lineMatch:
                sortVal = re.search(sciNotString, match)
                if(not sortVal):#search failed- try decimal format
                    sortVal = re.search(decimalMatchString, match)
                newSort = newSort + float(sortVal.group(0).split('s')[0].strip()) #trim off " s"
            
            #collect spreading if any
            newSpread=0
            lineMatch = re.search('.*finufft.*exec.*spread.*',strOut)
            if(lineMatch):
                spreadVal = re.search(sciNotString, lineMatch.group(0))
                if(not spreadVal): #search failed- try decimal format
                    spreadVal = re.search(decimalMatchString, lineMatch.group(0))
                newSpread = float(spreadVal.group(0).split('s')[0].strip())  #trim off " s"

            #collect interp if any
            newInterp=0
            lineMatch = re.search('.*finufft.*exec.*interp.*',strOut)
            if(lineMatch):
                interpVal = re.search(sciNotString, lineMatch.group(0))
                if(not interpVal): #search failed- try decimal format
                    interpVal = re.search(decimalMatchString, lineMatch.group(0))
                newInterp = float(interpVal.group(0).split('s')[0].strip())  #trim off " s"
            
            #collect the spread timings for each trial of old
            totalOldSpread=0   
            lineMatch = re.findall('.*spread.*ier.*', strOut) #gets spread AND unspread (i.e. interpolation)
            if(lineMatch):
                for match in lineMatch:
                    if(match):
                        oldSpreadVal = re.search(sciNotString, match)
                        if(not oldSpreadVal): #search failed- try decimal format
                            oldSpreadVal = re.search(decimalMatchString, match)
                        oldSpreadVal = oldSpreadVal.group(0).split('s')[0].strip() #trim off " s"
                        totalOldSpread = totalOldSpread + float(oldSpreadVal)
                                    
            spreadRatio = round((totalOldSpread)/(newSort + newSpread + newInterp),3)

            if(ftype == 1):
                spreadT1.append(spreadRatio)
            elif(ftype == 2):
                spreadT2.append(spreadRatio)
            else:
                spreadT3.append(spreadRatio)
            ###############################################################################

            #fftw_plan(old) / fftw_plan(new)

            #RE for scientific notation specific to plan line  (don't want to catch the "64")
            planSciNotString = '(\(64\)[ \t]+)(\d*.?\d*e-\d* s)'
            #RE for decimal notatino specific to plan line
            planDecimalMatchString= '(\(64\)[ \t]+)(\d*\.?\d*)'
            
            #collect new fftw_plan time
            new_fftwPlan=0
            lineMatch = re.search(".*make plan.*fftw plan \(64\).*",strOut)
            if(lineMatch):
                fftwPlanVal = re.search(planSciNotString, lineMatch.group(0))
                if(not fftwPlanVal): #search failed- try decimal format
                    fftwPlanVal = re.search(planDecimalMatchString, lineMatch.group(0))
                new_fftwPlan = float(fftwPlanVal.group(2).split('s')[0])  #strip off s

            #collect the fftw_plan timings for each trial of old
            totalOldfftwPlan=0
            #all fftw plan lines that don't include "make plan" indicating old implementation
            lineMatch = re.findall('(?<!\(make plan\))fftw plan \(64\).*', strOut) 
            if(lineMatch):
                for match in lineMatch:
                    if(match):
                        oldfftwPlanVal = re.search(planSciNotString, match)
                        if(not oldfftwPlanVal): #search failed- try decimal format
                            oldfftwPlanVal = re.search(planDecimalMatchString, match)
                        oldfftwPlanVal = float(oldfftwPlanVal.group(2).split('s')[0]) #trim off " s"
                        totalOldfftwPlan = totalOldfftwPlan + oldfftwPlanVal
            
            fftwPlanRatio = round(totalOldfftwPlan/new_fftwPlan,3)
            
            if(ftype == 1):
                fftwPlanT1.append(fftwPlanRatio)
            elif(ftype == 2):
                fftwPlanT2.append(fftwPlanRatio)
            else:
                fftwPlanT3.append(fftwPlanRatio)
            
            
            ###############################################################################

            #fftw_exec(old) / fftw_exec(new)

            #collect new fft time
            new_fft=0
            lineMatch = re.search(".*finufft_exec.*fft.*",strOut)
            if(lineMatch):
                fftVal = re.search(sciNotString, lineMatch.group(0))
                if(not fftVal):
                    fftVal = re.search(decimalMatchString, lineMatch.group(0))
                new_fft = float(fftVal.group(0).split('s')[0])  #strip off s

            #collect the fftw_plan timings for each trial of old
            totalOldfft=0   
            lineMatch = re.findall(".*fft \(\d threads\).*", strOut) 
            if(lineMatch):
                for match in lineMatch:
                    if(match):
                        oldfftVal = re.search(sciNotString, match)
                        if(not oldfftVal): #search failed
                            oldfftVal = re.search(decimalMatchString, match)
                        oldfftVal = float(oldfftVal.group(0).split('s')[0]) #trim off " s"
                        totalOldfft = totalOldfft + oldfftVal
            
            fftRatio = round(totalOldfft/new_fft,3)
            
            if(ftype == 1):
                fftT1.append(fftRatio)
            elif(ftype == 2):
                fftT2.append(fftRatio)
            else:
                fftT3.append(fftRatio)
            
            ###############################################################################


#Construct the bar graph 
barWidth = 0.25
barDepth = 0.25

_t1ys = dimensions
_t2ys = [y + barWidth for y in _t1ys]
_t3ys = [y + barWidth for y in _t2ys]

_t1xs = n_trials 
_t2xs = [x + barDepth for x in _t1xs]
_t3xs = [x + barDepth for x in _t2xs]

_t1xx, _t1yy = np.meshgrid(_t1xs,_t1ys)
t1x,t1y = _t1xx.ravel(), _t1yy.ravel()

_t2xx, _t2yy = np.meshgrid(_t2xs,_t2ys)
t2x,t2y = _t2xx.ravel(), _t2yy.ravel()

_t3xx, _t3yy = np.meshgrid(_t3xs,_t3ys)
t3x,t3y = _t3xx.ravel(), _t3yy.ravel()

zbot = np.zeros(len(t1x)) #z translation always 0
widths = [barWidth]*len(t1x)
depths = [barDepth]*len(t1x)

fig = plt.figure()
#create legend
t1_proxy = plt.Rectangle((0,0),1,1,fc="r")
t2_proxy = plt.Rectangle((0,0),1,1,fc="b")
t3_proxy = plt.Rectangle((0,0),1,1,fc="g")


##################TotalSpeed BAR GRAPH####################################################
print("TotalTime T1 " + str(totalTimeT1))
print("TotalTime T2 " + str(totalTimeT2))
print("TotalTime T3 " + str(totalTimeT3))

ax1 = fig.add_subplot(221,projection='3d')

logTotalTimeT1 = np.zeros(len(totalTimeT1))
logTotalTimeT2 = np.zeros(len(totalTimeT1))
logTotalTimeT3 = np.zeros(len(totalTimeT1))
for i in range(len(totalTimeT1)):
    logTotalTimeT1 = math.log(totalTimeT1[i])
    logTotalTimeT2 = math.log(totalTimeT2[i])
    logTotalTimeT3 = math.log(totalTimeT3[i])
    

ax1.bar3d(t1x, t1y, zbot, widths, depths, logTotalTimeT1, shade=True, color='r', label='type1', alpha='1')
ax1.bar3d(t2x, t2y, zbot, widths, depths, logTotalTimeT2, shade=True, color='b', label='type2', alpha='1')
ax1.bar3d(t3x, t3y, zbot, widths, depths, logTotalTimeT3, shade=True, color='g', label='type3', alpha='1')

ax1.legend([t1_proxy,t2_proxy,t3_proxy], ['type1','type2','type3'])

plt.xlabel('n_trials')
plt.ylabel('Dimensions')
plt.yticks([y+barWidth+1 for y in range(len(t1y))], ['1', '2', '3'])
plt.title('totalOldTime/totalNewTime')


##################SPREADING BAR GRAPH####################################################
print("Spreading T1 " + str(spreadT1))
print("Spreading T2 " + str(spreadT2))
print("Spreading T3 " + str(spreadT3))


logSpreadT1 = np.zeros(len(spreadT1))
logSpreadT2 = np.zeros(len(spreadT1))
logSpreadT3 = np.zeros(len(spreadT1))
for i in range(len(spreadT1)):
    logSpreadT1 = math.log(spreadT1[i])
    logSpreadT2 = math.log(spreadT2[i])
    logSpreadT3 = math.log(spreadT3[i])


ax2 = fig.add_subplot(222,projection='3d')

ax2.bar3d(t1x, t1y, zbot, widths, depths, logSpreadT1, shade=True, color='r', label='type1', alpha='1')
ax2.bar3d(t2x, t2y, zbot, widths, depths, logSpreadT2, shade=True, color='b', label='type2', alpha='1')
ax2.bar3d(t3x, t3y, zbot, widths, depths, logSpreadT3, shade=True, color='g', label='type3', alpha='1')

ax2.legend([t1_proxy,t2_proxy,t3_proxy], ['type1','type2','type3'])

plt.xlabel('n_trials')
plt.ylabel('Dimensions')
plt.yticks([y+barWidth+1 for y in range(len(t1y))], ['1', '2', '3'])
plt.title('oldSpreadTime/NewSpreadTime')



##################Total FFTW Plan BAR GRAPH####################################################

print("FFTW Plan T1 " + str(fftwPlanT1))
print("FFTW Plan T2 " + str(fftwPlanT2))
print("FFTW Plan T3 " + str(fftwPlanT3))


logfftwPlanT1 = np.zeros(len(fftwPlanT1))
logfftwPlanT2 = np.zeros(len(fftwPlanT1))
logfftwPlanT3 = np.zeros(len(fftwPlanT1))
for i in range(len(fftwPlanT1)):
    logfftwPlanT1 = math.log(fftwPlanT1[i])
    logfftwPlanT2 = math.log(fftwPlanT2[i])
    logfftwPlanT3 = math.log(fftwPlanT3[i])

ax3 = fig.add_subplot(223,projection='3d')

ax3.bar3d(t1x, t1y, zbot, widths, depths, logfftwPlanT1, shade=True, color='r', label='type1', alpha='1')
ax3.bar3d(t2x, t2y, zbot, widths, depths, logfftwPlanT2, shade=True, color='b', label='type2', alpha='1')
ax3.bar3d(t3x, t3y, zbot, widths, depths, logfftwPlanT3, shade=True, color='g', label='type3', alpha='1')

ax3.legend([t1_proxy,t2_proxy,t3_proxy], ['type1','type2','type3'])

plt.xlabel('n_trials')
plt.ylabel('Dimensions')
plt.yticks([y+barWidth+1 for y in range(len(t1y))], ['1', '2', '3'])
plt.title('totalOldFFtwPlan/NewFftwPlan')


##################Total FFT Exec BAR GRAPH####################################################

print("FFT Exec T1 " + str(fftT1))
print("FFT Exec T2 " + str(fftT2))
print("FFT Exec T3 " + str(fftT3))

logfftT1 = np.zeros(len(fftT1))
logfftT2 = np.zeros(len(fftT1))
logfftT3 = np.zeros(len(fftT1))
for i in range(len(fftT1)):
    logfftT1 = math.log(fftT1[i])
    logfftT2 = math.log(fftT2[i])
    logfftT3 = math.log(fftT3[i])


ax4 = fig.add_subplot(224,projection='3d')

ax4.bar3d(t1x, t1y, zbot, widths, depths, logfftT1, shade=True, color='r', label='type1', alpha='1')
ax4.bar3d(t2x, t2y, zbot, widths, depths, logfftT2, shade=True, color='b', label='type2', alpha='1')
ax4.bar3d(t3x, t3y, zbot, widths, depths, logfftT3, shade=True, color='g', label='type3', alpha='1')

ax4.legend([t1_proxy,t2_proxy,t3_proxy], ['type1','type2','type3'])

plt.xlabel('n_trials')
plt.ylabel('Dimensions')
plt.yticks([y+barWidth+1 for y in range(len(t1y))], ['1', '2', '3'])
plt.title('totalOldFFtwExec/NewFftwExec')

plt.show()














