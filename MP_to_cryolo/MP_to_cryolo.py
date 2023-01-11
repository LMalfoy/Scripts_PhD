import os
import pandas as pd
import numpy as np
import glob

'''
GOAL
    - DONE Read .star file and create internal data structure
    - DONE Write internal data structures into a .star file
    - DONE Use pandas dataframes as internal structure

USAGE
    - Copy script into folder containing relion Manualpicked fibril coordinates
    - Run with python3: python3 MP_to_cryolo.py ./*star
    - Will output *.cbox files, that can be used to train cryolo networks in fibrillar mode

'''


class Star:

    def __init__(self, filename=''):
        # Initialize parser
        self.lines = list()
        self.datablocks = list()
        self.datapairs = dict()
        self.filename = filename
        self.dataframes = list()
        # Read .star file
        if filename != '':
            self.read()
        # Set intersegment distance to 20 px
        self.distance = 20
        # Set box size to 200
        self.width = 200.0
        self.height = 200.0
        # Create cryolo compatible dataframe, including calculation of individual segment coordinates.
        self.cryolo_dataframe = self.create_cryolo_dataframe()
        # Write out .cbox file compatible with cryolo
        self.write_cryolo_dataframe()

    def __str__(self):
        print(self.dataframes)
        print(self.dataframe_to_string(self.dataframes[0]))
        return ':)'

    def read(self):
        # Reads rln star file and saves coordinates (and other, useless data) into an internal dataframe.
        self.read_file(self.filename)
        self.parse_lines()
        self.parse_datablocks()

    def read_file(self, file):
        # Read file and saves lines in lines and orig_lines
        with open(file) as fin:
            self.lines = fin.readlines()

    def parse_lines(self):
        # Parses lines for loops
        datablock = []
        in_datablock = False
        for line in self.lines:
            line = line.strip()
            if line == "loop_":
                in_datablock = True
                datablock = []
                continue
            if line == '' and in_datablock:
                in_datablock = False
                self.datablocks.append(datablock)
                continue
            if line == '':
                continue
            if in_datablock:
                datablock.append(line)
                continue
        if in_datablock:
            self.datablocks.append(datablock)

    def parse_datablocks(self):
        # Converts .star loop into a panda dataframe
        for datablock in self.datablocks:
            loop = dict()
            col_names = []
            for line in datablock:
                line = line.strip()
                if line[0] == '_':
                    col_names.append(line[1:])
                    loop[line[1:]] = []
                else:
                    values = line.split()
                    for i in range(len(col_names)):
                        loop[col_names[i]].append(values[i])
            df = pd.DataFrame(loop)
            self.dataframes.append(df)

    def dataframe_to_string(self, dataframe):
        # Converts dataframe into a .star file compatible string
        # Conversion of dataframe into fragments
        columns = [*dataframe]
        tostring = ''
        tostring = 'data_global\n\n_cbox_format_version 1.0\n\ndata_cryolo\n\nloop_' + '\n'
        for colname in columns:
            tostring += '_' + colname + '\n'
        tostring += dataframe.to_string(index=False, header=False)
        tostring += '\n\ndata_cryolo_include\n\nloop_\n_slice_index #1\n\n'
        return tostring

    def get_next_point(self, x1, y1, x2, y2, distance):
        # Calculates next point given p1 and p2 connected via straight line. Next point is distance distance
        # away from point1. Calculates directional vector connecting two points, then normalizes to unit vector
        # and calculates point based on distance * unit vector starting at p1.
        point1 = (x1, y1)
        point2 = (x2, y2)
        v = np.array(point1, dtype=float)
        u = np.array(point2, dtype=float)
        n = v - u
        n /= np.linalg.norm(n, 2)
        point = v - distance * n
        return point

    def calculate_coordinates(self, x1, y1, x2, y2, distance):
        # Calculates points along a line (filament) with a distance "distance" from first point x1, y1 given
        # a second point x2, y2.
        print("Calculating coordinates..")
        coordinates = [(x1, y1)]
        point1 = [x1, y1]
        point2 = [x2, y2]
        while True:
            new_coord = self.get_next_point(point1[0], point1[1], point2[0], point2[1], distance)
            coordinates.append((new_coord[0], new_coord[1]))
            point1 = new_coord
            if x1 < x2 and new_coord[0] > x2:
                break
            elif x1 > x2 and new_coord[0] < x2:
                break
            if y1 < y2 and new_coord[1] > y2:
                break
            elif y1 > y2 and new_coord[1] < y2:
                break
        print("Done.")
        return coordinates


    def create_cryolo_dataframe(self):
        # Creates dataframe containing columns and default values for cryolo filament coordinates.
        # Converts pairs of relion filament coordinates (START-END) to individual particle coordinates.
        # Control distance between individual filament segments with distance parameter (set to 20 px).
        cryolo_dict = dict()
        col_names = [
            'CoordinateX',  # 1
            'CoordinateY',  # 2
            'CoordinateZ',  # 3
            'Width',  # 4
            'Height',  # 5
            'Depth',  # 6
            'EstWidth',  # 7
            'EstHeight',  # 8
            'Confidence',  # 9
            'NumBoxes',  # 10
            'Angle',  # 11
            'filamentid'  # 12
        ]
        default_values = [
            'X',
            'Y',
            '<NA>',
            self.width,
            self.height,
            1.0,
            '<NA>',
            '<NA>',
            1.0,
            '<NA>',
            '<NA>',
            'FIL_ID'
        ]
        relion_df = self.dataframes[0]
        for col_name in col_names:
            cryolo_dict[col_name] = []
        fil_counter = 0
        for i in range(0, relion_df.shape[0] - 1, 2):
            x1 = float(relion_df.iloc[i][0])
            x2 = float(relion_df.iloc[i + 1][0])
            y1 = float(relion_df.iloc[i][1])
            y2 = float(relion_df.iloc[i + 1][1])
            # Distance set to 20 px
            coords = self.calculate_coordinates(x1, y1, x2, y2, distance=self.distance)
            for coordinate in coords:
                # CBOX files do not save coordinates as center of the image, but as bottom left corner of image!!
                # Thats why I need to substract from the image coordinate half of the box size in X and Y!!
                x = coordinate[0] - (self.width / 2)
                y = coordinate[1] - (self.height / 2)
                for i in range(len(col_names)):
                    if col_names[i] == 'CoordinateX':
                        cryolo_dict[col_names[i]].append(x)
                        continue
                    if col_names[i] == 'CoordinateY':
                        cryolo_dict[col_names[i]].append(y)
                        continue
                    if col_names[i] == 'filamentid':
                        cryolo_dict[col_names[i]].append(fil_counter)
                        continue
                    cryolo_dict[col_names[i]].append(default_values[i])
            fil_counter += 1
        cryolo_dataframe = pd.DataFrame(cryolo_dict)
        return cryolo_dataframe

    def write_cryolo_dataframe(self):
        # Writes cryolo dataframe into a .cbox file, compatible with cryolo's training algorithm
        print("Writing file..")
        outfile = self.filename.split('.')[0] + '.cbox'
        outstring = self.dataframe_to_string(self.cryolo_dataframe)
        with open(outfile, 'w') as fout:
            fout.write(outstring)
            print("Done.")

if __name__ == '__main__':
    for file in glob.glob("*.star"):
        print(file)
        parser = Star(filename=file)
