import os, sys

#create agendas, minutes, board actions, voting results directories, and in each of those directories, create text and pdf directories
base = "/sandag scraping"
existing_directories = ["borders", "executive", "public safety", "regional planning", "transportation"] # existing directories that I had in my filesystem
d_to_add = ["agendas", "minutes", "board actions", "voting results"] # subdirectories to add to above directories
subd_to_add = ["text", "pdf"] # subdirectories to add to above directories

for d in existing_directories:
	for dt in d_to_add:
		path = base + "/" + d + "/" + dt
		os.mkdir( path);
		for sd in subd_to_add:
			spath = path + "/" + sd
			os.mkdir( spath);
