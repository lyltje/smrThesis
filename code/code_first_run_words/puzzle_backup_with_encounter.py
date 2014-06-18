from __future__ import division
import math
import numpy as np
import random
import space_to_grid as stg
import bisect as bis
import datetime
import os
from collections import defaultdict
import matplotlib.pyplot as plt
from sets import Set
from operator import methodcaller
import sys
import copy
from matplotlib import cm
import prettyplotlib as ppl
import semantic_distance
import argparse
from thesis_utilities import *

input_directory_landscape = r"D:\Users\Lydia\results semantic landscape"
input_directory_cooc = r"D:\Users\Lydia\results word cooc"
output_directory = r"D:\Users\Lydia\results puzzle"
data_case_name = ""
max_closest = 0
nr_trials_check = 0
nr_trials_reinit = 0
neighbor_range_swap = [0,0]
block_ratio = 0
grid_f = defaultdict(lambda: defaultdict(lambda: None) )
data_portion = 0
nr_words_to_follow = 0
to_file_trials = 0
global_index = {}
global_name = {}
stop_nr_trials = 0
blob_neighbors = []
init_type = "probabilistic" # can be probabilistic or deterministic
log_file_n = ""
grid_input = ""
encounter = True

stress_cutoff = 1.2
figure_size = 8

class GridElem:

	def __init__(self, i, pos, name, blob_color, blob_nr=None):
		self.id = i
		self.pos = np.array(pos)
		self.closest = []
		self.dists = []
		self.followers = {}
		self.name = name
		self.blob_nr = blob_nr
		self.nr_swaps = 0
		self.sem_rep = None
	
	# n = [dist, id, x pos, y pos]
	def check_neighbor(self, n, init):
		# print "-",
		if self.id == n[1]:
			"compared to self"					
		if len(self.dists) == 0:
			self.dists.append(n[0])			
			self.closest.append([n[1], np.array(n[2:len(n)])] )
		elif n[0] < self.dists[-1] or len(self.dists) < max_closest:
			i = bis.bisect(self.dists, n[0])
			if grid_f[n[2]][n[3]].id != n[1]:
				print "WRONG CLOSEST ADDED"
				print
				sys.exit()
			if np.array(n[2:len(n)])[0]  == self.pos[0] and np.array(n[2:len(n)])[1]==self.pos[1]:
				print "closest added with own position"
				print
				sys.exit()
			if  not init and n[1] not in self.get_closest_ids(): 
				self.dists.insert(i, n[0])
				self.closest.insert( i, [n[1], np.array(n[2:len(n)])] )
				global_index[n[1]].add_follower(self.id, self.pos)
				global_index[self.closest[-1][0]].follower_unsubscribe(self.id)
				del self.dists[-1]
				del self.closest[-1]
			elif init:				
				self.dists.insert(i, n[0])
				self.closest.insert( i, [n[1], np.array(n[2:len(n)])] )
				if len(self.dists) > max_closest:
					del self.dists[-1]
					del self.closest[-1]
		# print "|",
		
		
	def has_closest(self, id_c):
		ids = [x for (x,y) in self.closest]
		return id_c in ids
			
	def get_closest(self):
		return self.closest
		
	def get_closest_ids(self):
		return [x for (x,y) in self.closest]
	
	def has_follower(self, id_f):
		return id_f in self.followers
		
	def get_followers(self):
		return self.followers
		
	def get_followers_ids(self):
		return self.followers.keys()
	
	def get_optimal(self):
		return np.mean(np.array(self.dists))
	
	def add_follower(self, id_f, pos_f):
		self.followers[id_f] = pos_f
		
	def follower_unsubscribe(self, id_f):
		del self.followers[id_f] 
	
	def add_cooc(self, sem):
		self.sem_rep = sem
	
	def init_as_follower(self):	
		for (id_c, pos_c) in self.closest:		
			global_index[id_c].add_follower(self.id, self.pos)
		
	def follower_pos_update(self, id_f, pos_f):
		self.followers[id_f] = pos_f
		
	def closest_pos_update(self, id_c, pos_c):
		found = False
		# print "closest pos update" 
		for c in self.closest:
			if c[0]==id_c:				
				c[1] = pos_c
				found = True
		if not found:
			print "closest not found: searched", id_c, "at", self.name			
			sys.exit()
	
	def get_improvement(self, new_x, new_y):
		# bereken improvement als je naar deze positie gaat
		new_pos = np.array([new_x,new_y])
		old = 0
		new = 0
		for c in self.closest:	 
			old += np.dot(self.pos-c[1], self.pos-c[1])
			new += np.dot(new_pos-c[1], new_pos-c[1])
		return old-new
		
	def change_pos(self, pos_x, pos_y):
		self.nr_swaps +=1		
		old_pos = np.array(self.pos)
		self.pos = np.array([pos_x, pos_y])
		for idX, posX in self.closest:		
			global_index[idX].follower_pos_update(self.id, self.pos)
		for idX, posX in self.followers.iteritems():
			global_index[idX].closest_pos_update(self.id, self.pos)
			
	def reset(self):
		self.closest = []
		self.dists = []
		self.followers = {}


def check_all_lists(iter):
	print_all_lists(iter)
	for elem_ci in global_index.keys():
		elem_c = global_index[elem_ci]
		followers = elem_c.get_followers_ids()
		closest = elem_c.get_closest_ids()
		for cc in closest:
			if not global_index[cc].has_follower(elem_ci):
				print "Problem closest elem:", elem_c.name, "closest:", global_index[cc].name
				print "list of follower ids of", global_index[cc].name, global_index[cc].get_followers_ids()
				sys.exit()
		for cf in followers:
			if not global_index[cf].has_closest(elem_ci):
				print "Problem follower elem:", elem_c.name, "follower:", global_index[cf].name
				print "list of closest ids of",global_index[cf].name, global_index[cf].get_closest_ids()
				sys.exit()
		
def print_all_lists(x):
	f = open(output_directory+r"\lists of closest.txt","a")
	f.write("=========" + str(x) + "========\n")
	for i in range(len(grid_f)):
		for j in range(len(grid_f)):
			if grid_f[i][j] != None:
				f.write(grid_f[i][j].name + ";" + str(grid_f[i][j].id) + " ; Closest")
				for id1 in grid_f[i][j].get_closest_ids():
					f.write(" ; " + global_index[id1].name + "-" + str(global_index[id1].id))
				f.write(" ; Followers")
				for id2 in grid_f[i][j].get_followers_ids():
					f.write(" ; " + global_index[id2].name + "-" + str(global_index[id2].id))
				f.write("\n")
	f.close()

def grid_and_blob_from_file():
	f = open(grid_input+r"\blob_file.txt")
	blob_nrs = {}
	for line in f:
		line = line.replace("\n", "")
		line = line.split(" ")
		blob_nr = int(line[0])
		del line[2]
		del line[0]
		for w in line:
			blob_nrs[w] = blob_nr
	f.close()
	
	colors = get_colors()

	landscape_file = grid_input+r"\grid_initial.txt"
	grid = grid_from_file(landscape_file)
	id = 0
	nr_words = 0
	for x, inDict in grid.iteritems():
		for y, elem in inDict.iteritems():
			if elem != None:
				# i, pos, name, blob_color, blob_nr=None
				grid_f[x][y] = GridElem(id, [x,y], elem, colors[id%len(colors)], blob_nrs[elem])				
				global_index[id] = grid_f[x][y]
				global_name[elem] = grid_f[x][y]
				id+=1
				nr_words+=1
	print "\n====\nFile read\n===="
	grid_to_file(grid_input, x+1, "test", grid_f)
	return x+1, nr_words
	
# Requires semantic representation as a list of lists of the non-zeros entries: [[name, value],[name,value]]
def distance(sem_w1, sem_w2):
	# Je kan hier ook andere afstands maten gebruiken
	return semantic_distance.cosine_distance(sem_w1, sem_w2)
	# return semantic_distance.cosine_distance_log(sem_w1, sem_w2)	


	
def stats_to_file(iter, trial, to_follow, nr_inits, grid_size, png_nr, nr_swaps):
	# followers
	image_name = output_directory + r"\follow_points_init" +str(nr_inits)+  "_tr" +str(trial)+"_it"+ str(iter)+".pdf"
	fig = plt.figure(figsize=(figure_size, figure_size))	
	colors = get_colors()
	points = []
	for i,ind in enumerate(to_follow):
		pos = global_index[ind].pos
		prop_plot = plt.scatter(pos[1], (grid_size-pos[0]-1), c=colors[i%len(colors)], marker='s')
		prop_plot.set_edgecolor("none")
		points.append((pos[0],pos[1]))
		cs = global_index[ind].get_closest()
		# print "nr closests: ", len(cs)
		for c in cs:
			# print indexes[c[0]][0],
			pos = c[1]
			fx = 1.0
			fy = 1.0
			if random.random() > 0.5:
				fx = -1.0
			if random.random() < 0.5:
				fy = -1.0
			prop_plot = plt.scatter(pos[1]+ fx*(random.random()/5+0.05), grid_size-1-(pos[0]+ fy*(random.random()/5+0.05)), c=colors[i%len(colors)], marker='.')
			prop_plot.set_edgecolor("none")
			points.append((pos[0],pos[1]))
		# print ""
	plt.title("Follow words and their most similar words trial " +str(trial) )	
	plt.axis([-1, grid_size+1, -1, grid_size+1])
	fig.savefig(image_name, bbox_inches='tight')		
	fig.savefig(output_directory+r"\points_"+ four_digit_string(png_nr) +".png")	
	plt.close()
	# grid to file 
	grid_to_file(output_directory, grid_size, "stats_init" +str(nr_inits)+  "_tr" +str(trial)+"_it"+ str(iter), grid_f)
	
	# stress measure figure
	# Make plot with vertical (default) colorbar
	fig = plt.figure(figsize=(figure_size, figure_size))
	# print "get stress values"
	stress_values, avg_opt, avg_neigh_dist = get_stress_values()
	# cmap_v = "PuRd"
	cmap_v = "RdYlGn"
	# print "make figure"
	xp, yp = np.mgrid[slice(0, grid_size, 1), slice(0, grid_size, 1)]
	if data_case_name=="test3":
		plt.pcolor(xp, yp, stress_values, cmap=cmap_v)
	else:
		zmin, zmax = 0, stress_cutoff
		plt.pcolor(xp, yp, stress_values, cmap=cmap_v, vmin=zmin, vmax=zmax)
	plt.title("Stress values at trial " + str(trial))
	plt.axis([0, grid_size-1, 0, grid_size-1])
	plt.colorbar()
	image_name = output_directory + r"\heat_map_stress_values_init" +str(nr_inits)+  "_tr" +str(trial)+"_it"+ str(iter)+".pdf"
	fig.savefig(image_name, bbox_inches='tight')
	fig.savefig(output_directory+r"\heat_map_stress_" + four_digit_string(png_nr) +".png")
	plt.close()
	
	avg_stress_value = np.mean(stress_values)
	
	f = open(output_directory + r"\stats.txt", "a")
	f.write(str(trial)+","+str(nr_swaps)+","+str(avg_stress_value)+","+str(avg_opt)+","+str(avg_neigh_dist)+"\n")
	f.close()
	
	
	
def get_stress_values():	
	# dit kan je nog faseren bij grotere dataset
	gs = len(grid_f)
	# print "get data"
	words = [x.name for x in global_index.itervalues()]
	words.sort()
	data = get_data_sample(words)
	# print "process data"
	values = np.zeros((gs,gs))
	values.fill(0.0)
	nr_elems = 0
	avg_opt, avg_neigh_dist = 0,0
	for i in range(gs):
		for j in range(gs):
			nr_n = 0
			sum_dif = 0
			elem = grid_f[i][j]
			if elem != None:
				nr_elems +=1
				for k in range(-1,2):
					for l in range(-1,2):
						if i+k>=0 and i+k<gs and j+l>=0 and j+l<gs:
							n = grid_f[i+k][j+l]
							if not k ==0 and l == 0 and n!= None:
								nr_n+=1
								sum_dif += distance(data[elem.name], data[n.name])
				xg = gs-i-1
				opt = elem.get_optimal()
				avg_opt+= opt
				if sum_dif != 0:
					values[xg,j] = opt / (sum_dif/float(nr_n))
					avg_neigh_dist += (sum_dif/float(nr_n))
					if values[xg,j] > stress_cutoff:
						values[xg,j] = stress_cutoff
				if nr_n==0:
					values[xg,j]=0.0
	# print values	
	# print "nr_elems", nr_elems
	return values, avg_opt/nr_elems, avg_neigh_dist/nr_elems

def add_all_cooc_data():
	template = input_directory_cooc + r"\complete_cooc\_"
	letters = "abcdefghijklmnopqrstuvwxyz"
	for l in letters:
		try:
			f = open(template+l+".txt", 'r')
			for line in f:
				# PROCESS LINE
				line = line.replace(";\n", "")
				line = line.split(";")
				repr = []
				word = line[0]
				del line[0]
				if len(line)>0:
					for elem in line:
						elem = elem.split(" ")
						repr.append([elem[0], float(elem[1])])
					try:
						global_name[word].add_cooc(repr)					
					except KeyError:
						None
		except IOError:
			print "file for letter", l, "not found!!! " + template+l+".txt"
	
	# CHECK
	# for id, elem in global_index.iteritems():
		# if elem.sem_rep == None:
			# print "for elem", elem.name, "no sem repr added"
		
	
def get_sem_data():
	file = open(input_directory_landscape +  r"\semantic_landscape.txt",'r')
	grid = [[],[],[],[]]
	i = 0
	j = 0
	grid_size = -1
	for line in file:
		line = line.replace("\n", "")
		instance = line.split(" ; ")		
		for elem in instance:
			if grid_size == -1:
				grid_size = len(instance)					
			if elem != "-EMPTY-" and elem != "":
				grid[0].append(i)
				grid[1].append(j)
				grid[2].append(elem)				
				grid[3].append([])			
			j+=1
		i+=1
		j=0
	file.close()
	# data = lees alle sampled dingen in
	data = {}
	f = open(input_directory_landscape + r"\sampled_coocs.txt")
	for line in f:
		line = line.replace("\n","")
		line = line.split(";")
		w = line[0]
		del line[0]
		data[w] = []
		for elem in line:
			elem = elem.split(" ")
			data[w].append( (elem[0] , float(elem[1])) )	
	return grid_size, data, grid

	
def add_to_sim_word(w1, sem_w1, data_sample, grid):	
	k = data_sample.keys()
	k.sort()
	best_index = -1
	if init_type == "deterministic":
		best_dis = float("inf")
		sem_w1 = map( methodcaller( "split"," "), sem_w1)
		sem_w1 = [[x, float(y)] for [x,y] in sem_w1]
		for index, w2 in enumerate(k):		
			sem_w2 = data_sample[w2]
			dis = distance(sem_w1, sem_w2)
			if dis < best_dis:
				best_dis = dis
				best_index = index
	elif init_type == "probabilistic":		
		best = []
		for i in range(10):
			best.append([float("inf"),-1])
		sem_w1 = map( methodcaller( "split"," "), sem_w1)
		sem_w1 = [[x, float(y)] for [x,y] in sem_w1]
		for index, w2 in enumerate(k):		
			sem_w2 = data_sample[w2]
			dis = distance(sem_w1, sem_w2)
			if dis < best[-1][0]:
				del best[-1]
				best.append( [dis,index])
				best.sort()
		sum_len = 0
		sum_dist = 0
		prev = 0
		prob = random.random()
		for cand in best:
			sum_len += 1/max(len(grid[3][cand[1]]), 0.01)
			sum_dist+= 1/cand[0]
		for cand in best:
			cumulative = ((1/cand[0])/sum_dist)*0.4 + ((1/max(0.01,len(grid[3][cand[1]])))/sum_len * 0.6) + prev
			prev = cumulative
			if prob <= cumulative:
				best_index = cand[1]
				break
	else:
		print "The initialization type for adding to similar word does not exist"
	return best_index
	
def get_grid(grid_size, data_sample, grid, nr_words):
	input_template = input_directory_cooc + r"\complete_cooc\_"
	
	if data_case_name == r"\limit1000_freq1_small_sample":
		input_template = r"D:\Users\Lydia\results word cooc\limit1000_freq1\complete_cooc\_"
	
	print "at file",
	for letter in "abcdefghijklmnopqrstuvwxyz":
		try:
			print letter,
			f = open(input_template+letter+".txt",'r')		
			line_nr = 0
			for line in f:
				line = line.replace(";\n", "")
				line = line.split(";")
				word = line[0]
				if word not in grid[2]:
					del line[0]
					if len(line) == 0:
						print word, "at line", line_nr, "in file", letter
						nr_words -= 1
					else:
						best_index = add_to_sim_word(word, line, data_sample, grid)		
						grid[3][best_index].append(word)
			f.close()
		except IOError:
			print letter, 
	print "\n New nr words:", nr_words
	del data_sample
		
		
	new_grid_size = math.ceil(math.sqrt(nr_words))
	ratio = new_grid_size/float(grid_size)	
	ratio_resize = ratio/1.2
	shift_resize_x = (new_grid_size - grid_size*ratio_resize)/2 + ratio_resize
	shift_resize_y = (new_grid_size - grid_size*ratio_resize)/2 + ratio_resize
	data_space = np.zeros((nr_words,2))
	index = 0
	blob_file = open(output_directory + r"\blob_file.txt", "w")
	for i in range(len(grid[0])):
		new_pos = np.array([ round(grid[0][i] * ratio_resize + shift_resize_x),round(grid[1][i] * ratio_resize + shift_resize_y)])
		data_space[index,:] = new_pos
		global_index[index] = [grid[2][i],i]
		index+=1		
		assigned = len(grid[3][i])
		data_space[index:index+assigned,0].fill(new_pos[0])
		data_space[index:index+assigned,1].fill(new_pos[1])
		random_dist = np.random.rand(assigned,2)
		data_space[index:index+assigned,:] = (random_dist-0.5)*ratio_resize + data_space[index:index+assigned,:]
		blob_file.write(str(i) + " " + grid[2][i] + " " + str(len(grid[3][i]))) 
		for elem in grid[3][i]:
			global_index[index] = [elem, i]
			index+=1
			blob_file.write(" " + elem)
		blob_file.write("\n")
	blob_file.close()		
	
	print "data space shape", data_space.shape
	print "last index = ", index-1 
	used_marker = "o"
	if nr_words > 1000:
		used_marker = "."	
	colors = get_colors()		
	coloring = []
	color_index = {}
	for i in range(nr_words):
		coloring.append( colors[global_index[i][1]%len(colors)] )	
		color_index[i] = colors[global_index[i][1]%len(colors)]
		
	image_name = output_directory + r"\stg_init_plot_blobColoring.pdf"	
	fig = plt.figure(figsize=(figure_size, figure_size))
	# fig = plt.figure(figsize=(figure_size, figure_size), dpi=figure_dpi)
	prop_plot = plt.scatter( data_space[:,1], new_grid_size-1-data_space[:,0], c=coloring, marker=used_marker)
	if nr_words > 1000:
		prop_plot.set_edgecolor("none")
	plt.axis([-1,new_grid_size+1, -1, new_grid_size+1])
	plt.title("Initial blob coloring")
	fig.savefig(image_name, bbox_inches='tight')
	plt.close()
	
	print "new grid size", new_grid_size
	intermediate_grids = output_directory + "\intermediate_grids" 
	if not os.path.exists(intermediate_grids):
		os.makedirs(intermediate_grids)	
		print "directory made"
	assignment, gz = stg.space_to_grid_iterative(data_space, intermediate_grids, with_figures=False, blob_nr_keeper=stg.TypeKeeper(color_index))
	del data_space
	
	print "init final grid and make figure of grid"
	image_name = output_directory + r"\stg_result_plot_blobColoring.pdf"
	# fig = plt.figure(figsize=(figure_size, figure_size), dpi=figure_dpi)
	fig = plt.figure(figsize=(figure_size, figure_size))
	for elem in assignment:
		grid_f[elem[0]][elem[1]] =  GridElem(elem[2], elem[0:2], global_index[elem[2]][0], color_index[elem[2]], global_index[elem[2]][1] )
		global_index[elem[2]] = grid_f[elem[0]][elem[1]]
		global_name[grid_f[elem[0]][elem[1]].name] = grid_f[elem[0]][elem[1]]
		prop_plot = plt.scatter(elem[1], new_grid_size-1-elem[0], c=color_index[elem[2]] , marker=used_marker)
		if nr_words > 1000:
			prop_plot.set_edgecolor("none")
	plt.axis([-1,new_grid_size, -1, new_grid_size])
	plt.title("Resulting blob coloring")
	fig.savefig(image_name, bbox_inches='tight')	
	plt.close()
	
	return new_grid_size, nr_words

def stop_condition(trial_nr):	
	# print "stop_condition not  implemented yet"
	return trial_nr > stop_nr_trials

def get_data_sample(sampled_words):
	input_letter = "a"
	input_file_temp = input_directory_cooc + r"\complete_cooc\_"
	filename = input_file_temp + input_letter + ".txt"
	f = open(filename, 'r')
	data = {}
	
	word = 	sampled_words[0]
	nr_found = 0
	while nr_found < len(sampled_words):
		if word[0] > input_letter and word[0] <= "z":		
			f.close()
			input_letter = word[0]
			f = open(input_file_temp + input_letter + ".txt", 'r')
		l = f.readline()
		items = l.replace(";\n", "")
		items = items.split(";")
		if word == items[0]:
			data[word] = []
			#process			
			del items[0]			
			for entry in items:	
				entry = entry.split(" ")
				data[word].append( [entry[0] ,float(entry[1]) ] )
			nr_found+=1		
			if nr_found < len(sampled_words):
				word = sampled_words[nr_found]
	f.close()
	return data
	
def init_closest(grid_size, old_grid_size, first):
	# als je een grotere area wil kan je de blob_size groter zetten zonder 
	# al deze shit opnieuw te doen
	blob_size = math.ceil( (grid_size*1.5)/float(old_grid_size))
	nr_blobs = int(math.floor(grid_size/blob_size))
	data_size = int(math.ceil(nr_blobs/float(data_portion)))
	grid_size = int(grid_size)
	print "grid size", grid_size, "old_grid_size", old_grid_size
	print "calculated blob size", blob_size, "nr_blobs", nr_blobs, "data_size", data_size,"data_portion", data_portion,  "grid_size", grid_size
	
	if not first and not encounter:
		for i in range(grid_size):
			for j in range(grid_size):
				if grid_f[i][j] != None:
					grid_f[i][j].reset()

	blobs = defaultdict(lambda: defaultdict(lambda: [[],[]]))
	r_b = 0
	c_b = 0
	
	for r in range(grid_size):
		if r%blob_size == 0 and r+blob_size <= grid_size and r!=0:
			r_b += 1
		for c in range(grid_size):
			if c%blob_size == 0 and c+blob_size <= grid_size and c!=0:
				c_b += 1
			if grid_f[r][c] != None:			
				blobs[r_b][c_b][0].append( grid_f[r][c].name )
				blobs[r_b][c_b][1].append( (r, c, grid_f[r][c].id) )	
		c_b = 0
		
	d_beg = 0
	d_end = 1		
	init_bool = first or not encounter
	for r_b in range(nr_blobs):
		for c_b in range(nr_blobs):
		
			if (r_b == d_end-1 or d_end == 1) and not encounter:
				d_beg = d_end-1
				d_end = min(d_end+data_size, nr_blobs)	
				words = []				
				for rb_i in range(d_beg, d_end):
					for cb_i in range(nr_blobs):
						words.extend(blobs[rb_i][cb_i][0])
				words.sort()
				if len(words) > 0:
					data = get_data_sample(words) 
				else:
					print "data of 0 words requested\n!!!!!!!!!!!!!!!"
				k = data.keys()
				k.sort()
				
			for i in range(len(blobs[r_b][c_b][0])-1):
				for j in range(i+1, len(blobs[r_b][c_b][0])):
					(r1,c1, id1) = blobs[r_b][c_b][1][i]
					(r2,c2, id2) = blobs[r_b][c_b][1][j]
					if encounter:
						d = distance(global_index[id1].sem_rep, global_index[id2].sem_rep)
					else:
						d = distance(data[blobs[r_b][c_b][0][i]], data[blobs[r_b][c_b][0][j]] )
					grid_f[r1][c1].check_neighbor([d, id2, r2, c2], init_bool)
					grid_f[r2][c2].check_neighbor([d, id1, r1, c1], init_bool)
					
			for n in blob_neighbors:
				r_b2 = n[0]+r_b
				c_b2 = n[1]+c_b
				# print "with blob", r_b2, c_b2
				if r_b2 > 0 and r_b2 < nr_blobs and c_b2 < nr_blobs:
					for i in range(len(blobs[r_b][c_b][0])):
						for j in range(len(blobs[r_b2][c_b2][0])):
							(r1,c1, id1) = blobs[r_b][c_b][1][i]
							(r2,c2, id2) = blobs[r_b2][c_b2][1][j]
							if encounter:
								d = distance(global_index[id1].sem_rep, global_index[id2].sem_rep)
							else:
								d = distance(data[blobs[r_b][c_b][0][i]], data[blobs[r_b2][c_b2][0][j]] )
							grid_f[r1][c1].check_neighbor([d, id2, r2, c2], init_bool)
							grid_f[r2][c2].check_neighbor([d, id1, r1, c1], init_bool)	
				
	# let all elements set themselves as followers
	for i in range(grid_size):
		for j in range(grid_size):
			if grid_f[i][j]!= None:
				grid_f[i][j].init_as_follower()		

	
def puzzle(grid_size, old_grid_size, nr_words):
	print "NR WORDS", nr_words
	iter = 0
	png_nr = 0
	follow_inds = Set()
	while len(follow_inds) < nr_words_to_follow:
		follow_inds.add(random.randrange(nr_words))
	follow_inds = list(follow_inds)
	
	
	
	print "\n========\nSTART PUZZLING\n===========\n"
	log_file = open(log_file_n, 'a')
	log_file.write("\n\n========\nSTART PUZZLING\n===========\n\n")	
	log_file.close()
	trial_nr = 0
	nr_inits = 0
	nr_swaps = 0
	total_nr_swaps = 0
	elem_indexes = range(nr_words)
	grid_size = int(grid_size)
	while not stop_condition(trial_nr):
		for i in range(nr_trials_check):
			if trial_nr%5 == 0:
				print "\nTRIAL", trial_nr, datetime.datetime.now()
				log_file = open(log_file_n, 'a')
				log_file.write("TRIAL " + str(trial_nr) + " " + str(datetime.datetime.now()) +"\n")
				log_file.close()
			# check if you need to reinitialize
			if iter%(nr_words*nr_trials_re_init)==0 or iter ==0:
				nr_inits+=1
				print "\ninit closest trial", trial_nr ,"     start:", datetime.datetime.now()
				log_file = open(log_file_n, 'a')
				log_file.write("init closest at "+str(datetime.datetime.now())+"\n")
				log_file.close()
				init_closest(grid_size, old_grid_size, iter==0)
				print "init closest stop:", datetime.datetime.now()
				log_file = open(log_file_n, 'a')
				log_file.write("stop init closest at "+str(datetime.datetime.now())+"\n")
				log_file.close()
			if iter == 0:
				stats_to_file("FIRST", trial_nr , follow_inds, nr_inits, grid_size, png_nr, nr_swaps)
				png_nr+=1
			# pick random element
			random.shuffle(elem_indexes)
			for elem_i in elem_indexes:
				[x,y] = list(global_index[elem_i].pos)
								
				if iter%5000 == 0:
					print "iter", iter,					
					
				# print "iter", iter
				# check_all_lists(iter)						
							
				swap_value = float("-inf")
				# check with which neighbor it wants to swap
				
				# print "check", grid_f[x][y].name, "with",
				for nx in range( max(0,neighbor_range_swap[0]+x) , min(neighbor_range_swap[1]+x, grid_size-1)):
					for ny in range( max(0,neighbor_range_swap[0]+y) , min(neighbor_range_swap[1]+y, grid_size-1)):
						if x!=nx or y!=ny:
							# print nx, ny,							
							if grid_f[nx][ny] != None:
								# print grid_f[nx][ny].name,
								v = grid_f[x][y].get_improvement(nx, ny) + grid_f[nx][ny].get_improvement(x, y)
								# Check if they are closest neighbors: n = [dist, id, x pos, y pos]
								d = distance(grid_f[x][y].sem_rep, grid_f[nx][ny].sem_rep)
								repl1 = grid_f[nx][ny].check_neighbor([d, grid_f[x][y].id, x, y], False)
								repl2 = grid_f[x][y].check_neighbor([d, grid_f[nx][ny].id, nx, ny], False)
							else:
								v = grid_f[x][y].get_improvement(nx, ny)
							if v > swap_value:
								# process swap value
								swap_value = v
								swap_x = nx
								swap_y = ny
				# print
				
				if swap_value > 0:
					nr_swaps+=1
					xy = grid_f[x][y]
					xy_swap = grid_f[swap_x][swap_y]
					grid_f[x][y] = xy_swap
					grid_f[swap_x][swap_y] = xy
					xy.change_pos(swap_x,swap_y)
					if xy_swap!=None:
						xy_swap.change_pos(x,y)						
				elif swap_value == float("-inf"):
					print "-inf"
					
						
				iter+=1
			
			# figures and stats to file
			if trial_nr%to_file_trials == 0 and trial_nr != 0:
				stats_to_file(iter, trial_nr, follow_inds, nr_inits, grid_size, png_nr, nr_swaps)
				total_nr_swaps += nr_swaps
				nr_swaps = 0
				png_nr+=1
			trial_nr+=1
	stats_to_file("LAST", trial_nr, follow_inds, nr_inits, grid_size, png_nr, nr_swaps)
	f = open(output_directory + "\stats.txt", "a")
	f.write("total number of swaps " + str(total_nr_swaps))
	
def build_final_grid(nr_words, process, old_grid_size = -1):
	if process == "all" or process == "initial_grid":
		log_file = open(log_file_n, 'a')
		print "get data", datetime.datetime.now()
		log_file.write("get data " + str(datetime.datetime.now()) + "\n")
		log_file.close()
		(old_grid_size, data_sample, grid_sample) = get_sem_data()
		print "get initial grid", datetime.datetime.now()
		log_file = open(log_file_n, 'a')
		log_file.write("get initial grid " + str(datetime.datetime.now()) + "\n")
		log_file.close()
		(new_grid_size, nr_words) = get_grid(old_grid_size, data_sample, grid_sample, nr_words)
		log_file = open(log_file_n, 'a')		
		log_file.write("initial grid finished " + str(datetime.datetime.now()) + "\n")
		log_file.close()
		grid_to_file(output_directory, new_grid_size, "initial", grid_f)
	elif process == "only_puzzle":
		(new_grid_size, nr_words) = grid_and_blob_from_file()
		print "nr words grid from file", nr_words
		grid_to_file(output_directory, new_grid_size, "as_from_file", grid_f)
	else:
		print "unrecognized process type"
		log_file = open(log_file_n, 'a')
		log_file.write("unrecognized process type\n")
		log_file.close()
	if process == "all" or process == "only_puzzle":
		if encounter:
			add_all_cooc_data()
			print "all cooc data added"
			log_file = open(log_file_n, 'a')		
			log_file.write("all coocs added to grid elems " + str(datetime.datetime.now()) + "\n")
			log_file.close()
		puzzle(new_grid_size, old_grid_size, nr_words)
			
			
if __name__ == "__main__":


	neighbor_range_swap = [-1,2]
	blob_neighbors = [(0,1),(1,-1),(1,0),(1,1)]
	
	parser = argparse.ArgumentParser(description='Run puzzle algorithm')
	# '''parser.add_argument(<naam>, type=<type>, default=<default>, help=<help message>)'''
	parser.add_argument("case_name", help="Name of the data case that you want to process")
	parser.add_argument("nr_words", type=int ,help="The number of words in the data case")
	parser.add_argument("--process", default=["all"] , nargs='*',help="What parts of the algorithm you want to execute")
	parser.add_argument("--max_closest", type=int , nargs='*',default=[8] ,help="number of closest words taken into account")
	parser.add_argument("--nr_trials_check", type=int ,nargs='*',default=[1] ,help="bla")
	parser.add_argument("--nr_trials_re_init", type=int ,nargs='*',default=[250] ,help="bla")
	parser.add_argument("--stop_nr_trials", type=int ,nargs='*',default=[500] ,help="bla")
	parser.add_argument("--block_ratio", type=int ,default=[2] ,nargs='*',help="bla")
	parser.add_argument("--data_portion", type=int ,default=[5] ,nargs='*',help="bla")
	parser.add_argument("--nr_words_to_follow", type=int ,default=[20] ,nargs='*',help="bla")
	parser.add_argument("--to_file_trials", type=int ,default=[20] ,nargs='*',help="bla")
	parser.add_argument("--old_grid_size", type=int , nargs='*',default=[-1] , help = "If you do only puzzle you have to provide the grid_size of the sample input")
	parser.add_argument("--dif_output_dir", nargs='*', default=[None])
	parser.add_argument("--encounter", nargs='*', default=[True])
	
	args = parser.parse_args()
	kwargs = vars(args)	
	
	print "\n\n\n"
	print kwargs
	
	data_case_name = "\\" + kwargs["case_name"]
	nr_words = kwargs["nr_words"]
	
	process = kwargs["process"][0]
	max_closest = kwargs["max_closest"][0]
	nr_trials_check = kwargs["nr_trials_check"][0]
	nr_trials_re_init = kwargs["nr_trials_re_init"][0]
	stop_nr_trials = kwargs["stop_nr_trials"][0]
	block_ratio = kwargs["block_ratio"][0]
	data_portion = kwargs["data_portion"][0]
	nr_words_to_follow = kwargs["nr_words_to_follow"][0]
	to_file_trials = kwargs["to_file_trials"][0]
	old_grid_size = kwargs["old_grid_size"][0]
	dif_output_dir = kwargs["dif_output_dir"][0]
	if kwargs["encounter"] == "no":
		encounter = False
	
	input_directory_landscape = input_directory_landscape + data_case_name
	input_directory_cooc = input_directory_cooc + data_case_name
	print dif_output_dir
	if dif_output_dir == None:
		output_directory = output_directory + data_case_name
		grid_input = output_directory
	else:
		grid_input = output_directory + data_case_name
		output_directory = output_directory +  "\\" + dif_output_dir  
	if not os.path.exists(output_directory):
		os.makedirs(output_directory)	
		print "directory made"
	
	f = open(output_directory + r"\stats.txt", "w")
	f.write("trial_nr , nr of swaps , avg stress value, avg optimal dist, avg neigh dist \n")
	f.close()
	
	log_file_n = output_directory+r"\log_file.txt"
	log_file = open(log_file_n, 'w')
	log_file.write("=====START SETTINGS=====\n")
	for key, value in kwargs.iteritems():		
		log_file.write(key+ ": " + str(value) +"\n")
	log_file.write("=====END  SETTINGS=====\n\n")
	log_file.write("START\n")
	log_file.close()
	
	f = open(output_directory+r"\lists of closest.txt","w")
	f.close()	
	build_final_grid(nr_words, process, old_grid_size)