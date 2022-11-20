import os
import pandas as pd

'''
GOAL
    - DONE Read .star file and create internal data structure
    - Write internal data structures into a .star file
    - DONE Use pandas dataframes as internal structure

USAGE
    - get dataframe = parser.read("file)
    - safe into file = parser.write(dataframe, dictionary)
'''


class Star:

    def __init__(self, filename=''):
        self.lines = list()
        self.datablocks = list()
        self.datapairs = dict()
        self.filename = filename
        self.dataframes = list()

        if filename != '':
            self.read()

    def __str__(self):
        print(self.dataframes)
        print(self.datapairs)

        print(self.datapair_to_string())
        print(self.dataframe_to_string(self.dataframes[0]))
        return ':)'

    def read(self):
        self.read_file(self.filename)
        self.parse_lines()
        self.parse_datablocks()

    def read_file(self, file):
        # Read file and saves lines in lines and orig_lines
        with open(file) as fin:
            self.lines = fin.readlines()

    def parse_lines(self):
        # Parses lines for loops and datapairs
        datablock = []
        in_datablock = False
        for line in self.lines:
            line = line.strip()
            if line == "loop_":
                in_datablock = True
                datablock = []
                continue
            if line == '':
                in_datablock = False
                self.datablocks.append(datablock)
                continue
            if in_datablock:
                datablock.append(line)
                continue
            if line[0] == '_':
                key, value = line[1:].split()[0], line[1:].split()[1]
                self.datapairs[key] = value

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

    def datapair_to_string(self):
        # Converts datapairs into a .star file compatible string
        sorted_dict = {key: value for key, value in sorted(self.datapairs.items())}
        tostring = '# data pairs \n'
        for k, v in sorted_dict.items():
            tostring += '_{} {}'.format(k, v) + '\n'
        return tostring

    def dataframe_to_string(self, dataframe):
        # Converts dataframe into a .star file compatible string
        # Conversion of dataframe into fragments
        columns = [*dataframe]
        tostring = 'loop_' + '\n'
        for colname in columns:
            tostring += '_' + colname + '\n'
        tostring += dataframe.to_string(index=False, header=False)
        return tostring

if __name__ == '__main__':
    parser = Star(filename='file.star')
    print(parser)




