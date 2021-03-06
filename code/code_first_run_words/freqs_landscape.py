import argparse
import sys
import datetime
from collections import defaultdict
from thesis_utilities import *
import numpy as np
import unicodedata
import math
import matplotlib.pyplot as plt
import copy
import os
lib_path = r"K:\Lydia\smrThesis\code\snowballstemmer-1.1.0\src"
print( lib_path)
sys.path.append(lib_path)
import snowballstemmer

output_path = r"D:\Users\Lydia\results_freqs"
input_path = r"D:\Users\Lydia\results_freqs\freqs_per_day"
landscape_path = r"D:\Users\Lydia\results puzzle"
use_stemmer = False
log_correlation = False
empty_value = 0
local_sum_devide = False
local_max_devide = False
subtract_local_mean = False
subtract_global_mean = False
use_patches = True
nr_patches = -1
overlap = -1
use_log_transform = False
log_and_scale = False

use_strict = True

def read_landscape(landscape_file):
    grid = grid_from_file(landscape_file)
    
    loc = "C:\\Users\\lydia\\temp_weird_words.txt"
    weird_words = get_word_list(loc)
    print("landscape_file", landscape_file)
    
    nr_words = 0
    word_dict = defaultdict(lambda: (False,-1,-1))
    grid_size = 0
    for x, grid_d in grid.items():
        grid_size+=1
        for y, elem in grid_d.items():
            if elem != None:
                nr_words+=1
                word_dict[elem] = (True, x, y)
                # if elem in weird_words:
                    # print(elem)
    # print("landscape read")
    # sys.exit()
    return grid, word_dict, grid_size, nr_words

def get_frequencies(word_dict, date, max_date):
    stemmer = snowballstemmer.stemmer('dutch')    
    freqs = defaultdict(lambda: defaultdict(int))
    freqs_per_day = defaultdict(lambda: defaultdict(int))
    oneday = datetime.timedelta(1)

    # print("min", date, "\nmax", max_date)
    current_year = date.year
    print("current year", current_year)
    
    while date <= max_date:
        # print("current date", date)
        has_file = True
        if current_year!=date.year:
            current_year = date.year
            print("current year", current_year)
        try:
            f_in = open(input_path+r"\words"+str(date)+".txt", "r")
        except IOError:
            # print("File not found\n", input_path+r"\words"+str(date)+".txt")
            has_file = False
        if has_file:
            for line in f_in:
                line = line.replace("\n", "")
                line = line.split(";")
                word = line[0]
                freq = int(line[1])                
                if use_stemmer:
                    word = stemmer.stemWord(word)
                if word_dict[word][0]:
                    if log_correlation:
                        freqs[word][date] = freq
                    freqs_per_day[date][word] = freq                      
            f_in.close()
        date+=oneday
                            
    return freqs, freqs_per_day

def freqs_overview_to_file(freqs, min_date, max_date, landscape):    
    pass
    
def build_freq_vect(f, min_date, max_date):
    dt = datetime.timedelta(1)
    if f != None:        
        vec_len = (max_date-min_date).days+1
        if (max_date-min_date).seconds > 0:
            vec_len+=1
        vect = np.zeros(vec_len)
        cur_date = copy.deepcopy(min_date)
        # print (vec_len, max_date, min_date, (max_date-min_date).days)
        index = 0
        while cur_date <= max_date and index<vec_len:
            if math.isnan(f[cur_date]):
                print( "nan found")
                sys.exit()
            vect[index] = f[cur_date]
            if f[cur_date] == 0:
                del f[cur_date]
            cur_date=cur_date+dt
            index+=1
        if any([math.isnan(x) for x in vect]):
            print("vect contains nan")
            sys.exit()
        if np.sum(vect)== 0.0:
            # print("vector with only zeros")
            vect[0]=0.1
            return [vect, "only_zeros"]
        return vect

    return None


def calc_correlations(freqs, min_date, max_date, landscape, grid_size):
    freqs[None] = None
    neighs = [[0,1],[1,1],[1,0]]    
    # correlations = [sum corr coeff, nr_neighbors]
    correlations = defaultdict(lambda: np.array([0,0]))
    avg_corr = 0
    nr_words = 0
    nr_all_zeros = 0
    nr_non_zero_corr = 0
    repr = defaultdict(lambda: defaultdict(lambda: None))
    for i in range(grid_size-1):
        repr[0][0] = build_freq_vect(freqs[landscape[i][0]], min_date, max_date)
        if isinstance(repr[0][0], list):
            nr_all_zeros += 1
            repr[0][0] = repr[0][0][0]
            print(landscape[i][0])
        repr[1][0] = build_freq_vect(freqs[landscape[i+1][0]], min_date, max_date)
        if isinstance(repr[1][0], list):
            nr_all_zeros += 1
            repr[1][0] = repr[1][0][0]
            print(landscape[i+1][0])
        for j in range(grid_size-1):
            repr[0][1] = build_freq_vect(freqs[landscape[i][j+1]], min_date, max_date)
            if isinstance(repr[0][1], list):
                nr_all_zeros += 1
                repr[0][1] = repr[0][1][0]
                print(landscape[i][j+1])
            repr[1][1] = build_freq_vect(freqs[landscape[i+1][j+1]], min_date, max_date)
            if isinstance(repr[1][1], list):
                nr_all_zeros += 1
                repr[1][1] = repr[1][1][0]
                print(landscape[i+1][j+1])
            if landscape[i][j]!=None:
                nr_words+=1
                for [ni, nj] in neighs:
                    # calc correlations if neighbor niet = None
                    if repr[ni][nj]!= None:
                        result = np.array([0,1])
                        temp = np.corrcoef(repr[0][0], y = repr[ni][nj])[0,1]
                        if temp != 0.0:
                            nr_non_zero_corr+=1
                        if math.isnan(temp):
                            result[0] = 0.0
                            print("has nan")
                        else:
                            result[0] = temp
                        correlations[landscape[i][j]] += result
                        correlations[landscape[i+ni][j+nj]] += result
                correlations[landscape[i][j]] = correlations[landscape[i][j]][0]/correlations[landscape[i][j]][1] 
                avg_corr += correlations[landscape[i][j]]
            repr[0][0] = repr[0][1]
            repr[1][0] = repr[1][1]
    #process edges!!!!
    print("nr non-zero correlations", nr_non_zero_corr)
    print("nr all zero vectors:", nr_all_zeros)
    
    for i in range(grid_size):
        if landscape[i][grid_size-1]!= None:
            nr_words+=1
            correlations[landscape[i][grid_size-1]] = correlations[landscape[i][grid_size-1]][0]/correlations[landscape[i][grid_size-1]][1] 
            avg_corr += correlations[landscape[i][grid_size-1]]
        if landscape[grid_size-1][i]!= None and i!=grid_size-1:
            nr_words+=1
            correlations[landscape[grid_size-1][i]] = correlations[landscape[grid_size-1][i]][0]/correlations[landscape[grid_size-1][i]][1] 
            avg_corr += correlations[landscape[grid_size-1][i]]
    return correlations, avg_corr/nr_words

def to_file_correlations(corr, avg_corr, word_dict, grid_size):
    f = open(output_path + r"\correlations.txt", "w")
    f.write("average correlation,"+str(avg_corr)+"\n")
    # grid_size = int(np.ceil(np.sqrt(len(corr))))
    figv = np.zeros((grid_size,grid_size))
    for k, v in corr.items():
        f.write(k+","+str(v)+"\n")
        figv[word_dict[k][1],word_dict[k][2]] = v
    f.close()
    
    figure_size = 4
    fig = plt.figure(figsize=(figure_size, figure_size))
    # cmap_v = "PuRd"
    cmap_v = "RdYlGn"
    xp, yp = np.mgrid[slice(0, grid_size, 1), slice(0, grid_size, 1)]
    zmin, zmax = 0, np.max(figv)
    plt.pcolor(xp, yp, figv, cmap=cmap_v, vmin=zmin, vmax=zmax)
    plt.title("correlations over landscape")
    plt.axis([0, grid_size-1, 0, grid_size-1])
    plt.colorbar()
    image_name = output_path + r"\correlations_heatmap.pdf"
    fig.savefig(image_name, bbox_inches='tight')
    fig.savefig(image_name.replace(".pdf", ".png"))
    plt.close()

def landscape_patches(landscape):
    landscape_size = len(landscape)
    size = int(landscape_size/nr_patches)
    patch_path = output_path+r"\daily_freqs\patches"
    for r in range(nr_patches):
        for c in range(nr_patches):
            rf = max(r*size-overlap, 0)
            cf = max(c*size-overlap, 0)
            rt = min((r+1)*size+overlap, landscape_size)
            ct = min((c+1)*size+overlap, landscape_size)
            f = open(patch_path+r"\landscape_patch_"+str(r)+"_"+str(c)+".txt","w")           
            for i in range(rf,rt):
                for j in range(cf,ct):
                    if landscape[i][j] != None:
                        f.write(landscape[i][j])
                    else:
                        f.write("-EMPTY-")
                    if j != landscape_size-1:
                        f.write(",")
                f.write("\n")
            f.close()           
    
def day_freq_to_file_patches(out_path, date, freqs):    
    size = freqs.shape[0]/nr_patches
    
    for r in range(nr_patches):
        for c in range(nr_patches):
            rf = max(r*size-overlap, 0)
            cf = max(c*size-overlap, 0)
            rt = min((r+1)*size+overlap, freqs.shape[0])
            ct = min((c+1)*size+overlap, freqs.shape[0])
            # print("row from", rf, "to", rt, "\ncolumn from", cf, "to", ct)
            patch = freqs[rf:rt,cf:ct]    
            patch_path = out_path + r"\day" + str(date)
            if not os.path.exists(patch_path):
                os.makedirs(patch_path) 
            f = open(patch_path+r"\patch_"+str(r)+"_"+str(c)+".txt","w")
            for i in range(patch.shape[0]):
                for j in range(patch.shape[1]):
                    f.write(str(patch[i,j]))
                    if j != patch.shape[1]-1:
                        f.write(",")
                f.write("\n")
            f.close()  

            f = open(out_path+r"\patch_"+str(r)+"_"+str(c)+"_info.txt","w")
            f.write("nr rows input:  " + str(rt-rf)+"\n")
            f.write("nr cols input:  " + str(ct-cf)+"\n")
            f.write("nr rows output: " + str(size)+"\n")
            f.write("nr cols output: " + str(size))            
            f.close()  
           
def day_freq_to_file_patches_fill(out_path, date, freqs):    
    size = freqs.shape[0]/nr_patches
    # if overlap != 1:
        # print("not allowed to use to file patches fill, value is not 1")
        # sys.exit()
    
    for r in range(nr_patches):
        for c in range(nr_patches):
            patch = np.zeros((size+(2*overlap), size+(2*overlap)))
            rf = max(r*size-overlap, 0)
            cf = max(c*size-overlap, 0)
            rt = min((r+1)*size+overlap, freqs.shape[0])
            ct = min((c+1)*size+overlap, freqs.shape[0])
            # print("row from", rf, "to", rt, "\ncolumn from", cf, "to", ct)
            rfp = max((r*size-overlap)*-1, 0)
            cfp = max((c*size-overlap)*-1, 0)
            rtp = rfp + (rt-rf)
            ctp = cfp + (ct-cf)
            
            patch[rfp:rtp,cfp:ctp] = freqs[rf:rt,cf:ct]    
            patch_path = out_path + r"\day" + str(date)
            if not os.path.exists(patch_path):
                os.makedirs(patch_path) 
            f = open(patch_path+r"\patch_"+str(r)+"_"+str(c)+".txt","w")
            for i in range(patch.shape[0]):
                for j in range(patch.shape[1]):
                    f.write(str(patch[i,j]))
                    if j != patch.shape[1]-1:
                        f.write(",")
                f.write("\n")
            f.close()  

            f = open(out_path+r"\patch_"+str(r)+"_"+str(c)+"_info.txt","w")
            f.write("nr rows input:  " + str(size+(2*overlap))+"\n")
            f.write("nr cols input:  " + str(size+(2*overlap))+"\n")
            f.write("nr rows output: " + str(size)+"\n")
            f.write("nr cols output: " + str(size))            
            f.close()  

def day_freq_to_file_whole(log_folder, date, freqs):
    f = open(log_folder+r"\day"+str(date)+".txt","w")
    for i in range(freqs.shape[0]):
        for j in range(freqs.shape[1]):
            f.write(str(freqs[i,j]))
            if j != freqs.shape[1]-1:
                f.write(",")
        f.write("\n")
    f.close()
    
def day_freq_to_file_whole_fill(log_folder, date, freqs):
    new_size = freqs.shape[0]+2*overlap
    # print("new size", new_size)
    filled_freqs = np.zeros((new_size,new_size))
    # print("f freqs size",filled_freqs.shape) 
    filled_freqs[overlap:overlap+freqs.shape[0],overlap:overlap+freqs.shape[0]] = freqs
    day_freq_to_file_whole(log_folder, date, filled_freqs)
    

def day_freq_to_file(log_folder, date, freqs):
    if use_patches:
        patch_path = log_folder+r"\patches"
        if not os.path.exists(patch_path):
            os.makedirs(patch_path) 
        if use_strict:
            day_freq_to_file_patches_fill(patch_path, date, freqs)
        else:
            day_freq_to_file_patches(patch_path, date, freqs)
    else:
        if use_strict:
            day_freq_to_file_whole_fill(log_folder, date, freqs)
        else:
            day_freq_to_file_whole(log_folder, date, freqs)
    
    
def log_daily_freqs(freqs_per_day, landscape, grid_size, nr_words):
    log_scale = 0.1
    print("log daily freqs")
    
    log_folder = output_path + r"\daily_freqs"
    if not os.path.exists(log_folder):
        os.makedirs(log_folder)
        
    keys = list(freqs_per_day.keys())
    keys.sort()
    nr_days = len(keys)
    print("nr of days", nr_days)
    repeat = 1
    if subtract_global_mean:
        global_sum = np.zeros((grid_size, grid_size))    
        repeat = 2

    if use_log_transform:
        f_log = open(output_path+r"\info.txt","a")
        f_log.write("\n\n log verschuiving voor log apply: "+str(log_scale)+"\n")
        f_log.close()
    
    for n in range(repeat):
        for date in keys:
            f_dict = freqs_per_day[date]            
            values = np.zeros((grid_size, grid_size))
            for i in range(grid_size):
                for j in range(grid_size):
                    elem = landscape[i][j]
                    if elem != None:
                        values[i,j]=f_dict[elem]                    
                    else:
                        values[i,j]=empty_value
            # if n == 0:
                # day_freq_to_file(log_folder, "rawValues_" + str(date), values)
            if local_sum_devide:
                values = values/np.sum(values)
                # day_freq_to_file(log_folder, "localSumDevide_" + str(date), values) 
            if local_max_devide and (not use_log_transform or (not log_and_scale and use_log_transform)) :
                values = values/np.max(values)
                # day_freq_to_file(log_folder, "localMaxDevide_" + str(date), values)
            if subtract_local_mean:
                values = values - (np.sum(values) / nr_words)
                # day_freq_to_file(log_folder, "localMeanSubtract_" + str(date), values)                
            if subtract_global_mean and n == 0:
                global_sum += values
            if subtract_global_mean and n == 1:
                values = values - global_sum/nr_days
                
            if use_log_transform:
                values = values + log_scale
                values = np.log(values)
                if np.isnan(np.sum(values)):
                    print("values contains nan")
                    sys.exit()                    
                if np.sum(values) == float("inf"):
                    print("values contains inf")
                    sys.exit()                    
                if np.sum(values) == float("-inf"):
                    print("values contains -inf")
                    sys.exit()                                    
                if log_and_scale:
                    f_log = open(output_path+r"\info.txt","a")
                    f_log.write("min verschuiving na log apply, "+str(np.min(values))+", "+str(date)+", "+str(log_scale)+"\n")
                    f_log.close()
                    values = values - np.min(values)
                    f_log = open(output_path+r"\info.txt","a")
                    f_log.write("max schaling na log apply, "+str(np.max(values))+", "+str(date)+", \n")
                    f_log.close()
                    values = values/np.max(values)
                    
                
            if subtract_global_mean and n == 1 or not subtract_global_mean and n == 0:
                day_freq_to_file(log_folder, date, values)
    
    if use_patches:
        landscape_patches(landscape)
            
                

def evaluate_sem(landscape_file, min_date, max_date):
    landscape, word_dict, grid_size, nr_words = read_landscape(landscape_file)
    freqs, freqs_per_day = get_frequencies(word_dict, min_date, max_date)
    if log_correlation != "only":
        log_daily_freqs(freqs_per_day, landscape, grid_size, nr_words)
    if log_correlation != "no":
        freqs_overview_to_file(freqs, min_date, max_date, landscape)
        corr, avg_corr = calc_correlations(freqs, min_date, max_date, landscape, grid_size)
        to_file_correlations(corr, avg_corr, word_dict, grid_size)




if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run puzzle algorithm')
    parser.add_argument("freqs_folder")
    parser.add_argument("landscape_folder")
    parser.add_argument("output_folder")
    parser.add_argument("stemmer", help="yes or no")
    correlation_options = ["yes","no","only"]
    parser.add_argument("correlation", help="Types: yes or no or only (no logging the freqs")
    parser.add_argument("normalisation_type",help="Types: max, sum or none")
    parser.add_argument("use_patches", help="Types: yes or no")    
    parser.add_argument("use_log_transform", help="Types: yes or no")    
    parser.add_argument("--min_day", type=int, default = 1)
    parser.add_argument("--min_month", type=int, default =10)
    parser.add_argument("--min_year", type=int, default =2007)
    parser.add_argument("--max_day", type=int, default =5)
    parser.add_argument("--max_month", type=int, default =7)
    parser.add_argument("--max_year", type=int, default =2014)
    parser.add_argument("--empty_value", type=float, default=None)
    parser.add_argument("--subtract_local_mean",default=None)
    parser.add_argument("--subtract_global_mean", default=None)
    parser.add_argument("--nr_patches", type=int, default=None)
    parser.add_argument("--overlap", type=int, default=None)
    parser.add_argument("--use_strict",  default=None)
    parser.add_argument("--log_and_scale",  default=None)
    
        
    args = parser.parse_args()
    kwargs = vars(args)    
    
    
    min_date = datetime.date(kwargs["min_year"], kwargs["min_month"], kwargs["min_day"])
    max_date = datetime.date(kwargs["max_year"], kwargs["max_month"], kwargs["max_day"])
        
    if kwargs["stemmer"] == "yes":
        use_stemmer = True
    elif kwargs["stemmer"] != "no":
        print("unvalid value stemmer")
        sys.exit()
        
    if kwargs["use_strict"] == "no":
        use_strict = True
    elif not( kwargs["use_strict"] == "yes" or kwargs["use_strict"] == None) :
        print("unvalid value use strict")
        sys.exit()
        
    log_correlation = kwargs["correlation"]
    if log_correlation not in correlation_options:
        print("unvalid value correlation")
        sys.exit()

    if kwargs["normalisation_type"] == "sum":
        local_sum_devide = True
    elif kwargs["normalisation_type"] == "max":
        local_max_devide = True
    elif kwargs["normalisation_type"] != "none":
        print("unrecognised normalisation type")
        sys.exit()
    
    if kwargs["use_log_transform"] == "yes":
        use_log_transform = True
        if kwargs["log_and_scale"]==None:
            print("when using the log transform log and scale needs to be defined")
            sys.exit()
        elif  kwargs["log_and_scale"]=="yes":
            log_and_scale = True
        elif kwargs["log_and_scale"] !="no":
            print("unvalid value for log_and_scale")
            sys.exit()
        
    elif kwargs["use_log_transform"] != "no":
        print("unvalid value use_log_transform")
        sys.exit() 
   
    if kwargs["subtract_local_mean"] == "no":
        subtract_local_mean = False
    elif kwargs["subtract_local_mean"] != None:
        print("invalid value subtract_local_mean")
        sys.exit()
    if kwargs["subtract_global_mean"] == "yes":
        subtract_global_mean = True
    elif kwargs["subtract_global_mean"] != None:
        print("invalid value subtract_global_mean")
        sys.exit()
    
    if kwargs["use_patches"] == "yes":
        use_patches = True
        if kwargs["nr_patches"] == None or kwargs["overlap"] == None:
            print("Additional parameters for using patches not provided")
            sys.exit()
        nr_patches = kwargs["nr_patches"]
    elif kwargs["use_patches"] == "no":
        use_patches = False
    else:
        print("invalid value use_patches")
        sys.exit()
    
    if kwargs["overlap"] == None and kwargs["use_strict"]!="no":
        print("when using strict overlap needs to be defined")
        sys.exit()
    if kwargs["overlap"] != None:
        overlap = kwargs["overlap"]
    
    if kwargs["empty_value"]!=None:
        empty_value = kwargs["empty_value"]
    
    output_path = output_path+"\\"+kwargs["output_folder"]
    if not os.path.exists(output_path):
        os.makedirs(output_path)    
    print( "directory made"    )
    input_path = input_path+"\\"+kwargs["freqs_folder"]
    landscape_file = landscape_path+"\\"+ kwargs["landscape_folder"] + r"\grid_final.txt"
    
    f_log = open(output_path+r"\info.txt","w")   
    for k in kwargs.keys():
        f_log.write(k + " " + str(kwargs[k])+"\n")
    f_log.write("\n\n")
    f_log.close()
    
    evaluate_sem(landscape_file, min_date, max_date)    
    