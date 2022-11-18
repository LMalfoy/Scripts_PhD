import os
import subprocess
from datetime import date

class Project:
    '''
    Represents the workflow based on a set of 2D class averages.
    '''

    def __init__(self):
        '''
        Things needed for initialization:
            Project folder
                User settings
                2DCs (with link to original file)
                Inimodel (master folder of different inimodel runs with different settings)
                    inimodel_1 --> log file of command, submission file
                    inimodel_2
                    ...
                3DRefine
                    3dr_1 --> log file of command, submission file
                    3dr_2
                    ...
        '''

        # Initialize project folder
        self.workdir = os.getcwd()
        self.date = self.set_date()

        project_folders = self.find_project_folders()
        if len(project_folders) > 0:
            # List project folders, ask user which one to load
            print("Found the following project folders: ")
            for i in range(1, len(project_folders) + 1):
                print(str(i) + ". " + project_folders[i - 1])
            target_project = int(input("Which project to load? ")) - 1
            # Load project
            self.project_folder = project_folders[target_project]
            self.name = self.project_folder.split('_')[1]
        else:
            print("Found no project folder. Creating new project.")
            self.name = input("Project name: ")
            self.project_folder = self.date + '_' + self.name + '_INI3DR'

        # Check if project folder exists, if not create one
        self.projectdir = os.path.join(self.workdir, self.project_folder)
        self.is_exist = os.path.exists(self.projectdir)

        # Set folder locations
        self.settings_folder = os.path.join(self.projectdir, 'project')
        self.classes_folder = os.path.join(self.projectdir, '2dclasses')
        self.inimodel_folder = os.path.join(self.projectdir, 'inimodel')
        self.refine_folder = os.path.join(self.projectdir, '3drefine')
        self.archive_folder = os.path.join(self.projectdir, 'archive')

        if not self.is_exist:
            # Create project folder
            os.mkdir(self.project_folder)
            print('Created project folder ' + self.project_folder)
            # Create subfolders
            os.mkdir(self.settings_folder)
            print('Created project settings folder ' + self.settings_folder)
            os.mkdir(self.classes_folder)
            print('Created 2D classes folder ' + self.classes_folder)
            os.mkdir(self.inimodel_folder)
            print('Created inimodel folder ' + self.inimodel_folder)
            os.mkdir(self.refine_folder)
            print('Created 3drefine folder ' + self.refine_folder)
        else:
            print('Project folder ' + self.project_folder + ' already exists. Skipping folder creation.')

        # Check user settings
        self.settings = dict(
            # General settings
            general_px_size = '',
            general_ca_location = '',
            general_ca_mrc_location = '',
            # Initial model settings
            inimodel_crossover_range_min = '',
            inimodel_crossover_range_max='',
            inimodel_crossover_step = '',
            inimodel_iter = 10,
            inimodel_mask = 200,
            inimodel_shift = 3,
            inimodel_angle = 1,
            inimodel_angle_step = 1,
            inimodel_sym = 2,
            inimodel_max_res = 5,
            inimodel_cpus = 24
            # 3DR settings
            # WIP
        )

        # Check if user settings are present, if yes load them, if not write them
        self.settings_path = os.path.join(self.settings_folder, 'user_settings.txt')
        if os.path.exists(self.settings_path):
            # Reading general settings
            print('Found user settings. Loading the following settings.')
            self.read_settings()
            print(self.settings)
        else:
            # Writing general settings
            print('No user settings found. Please provide general information.')
            while True:
                try:
                    self.settings["general_px_size"] = input('Pixel size: ')
                    self.settings["general_px_size"] = float(self.settings["general_px_size"])
                    break
                except:
                    print('Pixel size must be a float!')
            self.settings["general_ca_location"] = input('Class average star file: ')
            self.settings["general_ca_mrc_location"] = self.settings["general_ca_location"][:-4] + 'mrcs'
            self.manipulate_ca_starfile()
            self.write_settings()

        # Check if job counters are present, if yes load them, if not write them
        self.job_counter_path = os.path.join(self.settings_folder, 'job_counters.txt')
        self.job_counters = dict(
            inimodel_counter=0,
            refine_counter=0
        )
        if os.path.exists(self.job_counter_path):
            self.read_jobcounter()
        else:
            self.write_jobcounter()

        # Eventually, create an archive to store jobs that have been completed
        # self.refine_jobs = dict()
        # self.inimodel_jobs = dict()

        # Check what to run
        self.get_job()

        if self.job == "inimodel":
            self.inimodel()
        elif self.job == "refine":
            self.refine()

    ## Functions

    # General functions
    def find_project_folders(self):
        projects = []
        for object in os.listdir(os.getcwd()):
            if 'INI3DR' in object and os.path.isdir(object):
                projects.append(object)
        return projects

    def set_date(self):
        today = date.today()
        date_string = today.strftime("%y%m%d")
        return date_string

    def write_settings(self):
        # Writes settings found in dictionary into file
        sorted_dict = {key: value for key, value in sorted(self.settings.items())}
        output = ''
        for k, v in sorted_dict.items():
            output += '{} = {}'.format(k, v) + '\n'
        with open(self.settings_path, 'w') as fout:
            fout.write(output)

    def read_settings(self):
        # Reads settings found in the user_settings.txt
        with open(self.settings_path) as fin:
            lines = fin.readlines()
            for line in lines:
                key, value = line.strip().split('=')[0].strip(), line.strip().split('=')[1].strip()
                self.settings[key] = value

    def write_jobcounter(self):
        # Writes settings found in dictionary into file
        sorted_dict = {key: value for key, value in sorted(self.job_counters.items())}
        output = ''
        for k, v in sorted_dict.items():
            output += '{} = {}'.format(k, str(v)) + '\n'
        with open(self.job_counter_path, 'w') as fout:
            fout.write(output)

    def read_jobcounter(self):
        # Reads settings found in the user_settings.txt
        with open(self.job_counter_path) as fin:
            lines = fin.readlines()
            for line in lines:
                key, value = line.strip().split('=')[0].strip(), int(line.strip().split('=')[1].strip())
                self.job_counters[key] = value

    def get_job(self):
        while True:
            print('What job do you want to run?' + '\n' + '1. Initial model generation' + '\n' + '2. Refinement')
            try:
                contract = int(input('[1, 2]: '))
                if contract == 1:
                    self.job = "inimodel"
                    break
                elif contract == 2:
                    self.job = "refine"
                    break
                else:
                    raise ()

            except:
                print('Please specify with "1" or "2"!')

    def write_file(self, string, file):
        with open(file, 'w') as fout:
            fout.write(string)

    def manipulate_ca_starfile(self):
        # Have to do this, since relion programs all need to be run from toplevel folder :l
        with open(self.settings['general_ca_location']) as fin:
            print(self.settings['general_ca_location'])
            lines = fin.readlines()
            lines_out = []
            for line in lines:
                if '@' in line:
                    to_replace = line.strip().split()[0].split('@')[1]
                    lines_out.append(line.replace(to_replace, self.settings['general_ca_mrc_location']))
                else:
                    lines_out.append(line)
            with open(self.settings['general_ca_location'], 'w') as fout:
                output = ''
                for line in lines_out:
                    output += line
                print(output)
                fout.write(output)

    # Initial model functions
    def inimodel(self):
        '''
        # Initiate and submit inimodel generation
        # Check if necessary settings are present, if not ask; if yes, confirm
        # Then create new running-folder in inimodel folder, user counter & date for multiple runs
        # Make sure to save inimodel_settings as log in that folder
        # Write submission file for hpc
        # Submit to hpc, wait for results
        # If results are present, load their location, so that 3DR processes eventually can access them
        '''
        # CHECK IF OLD RUNS ARE AVAILABLE; IF SO; ASK IF USER WANTS TO LOAD SETTINGS

        # Initializing settings
        print('Initializing inimodel settings.')
        self.initialize_inimodel()
        # Write submission file
        # set correct results folder
        # write log with command (or just write submission script)
        # use absolute paths!
        # nice to have:
        #   - Write into project file, archive settings / results
        #   - Wait for results to finish, notify once done

        # For each step in ini model range, create a folder, then create submission file
        self.inimodel_submission_file_paths = []
        for i in range(int(self.settings['inimodel_crossover_range_min']),
                       int(self.settings['inimodel_crossover_range_max']) +
                       int(self.settings['inimodel_crossover_step']),
                       int(self.settings['inimodel_crossover_step'])):
            inimodel_run_name = str(i) + 'co'
            inimodel_run_folder = os.path.join(self.inimodel_runs_master, inimodel_run_name)
            os.mkdir(inimodel_run_folder)
            submission_file = self.write_inimodel_submission(directory=inimodel_run_folder, crossover=i)
            self.inimodel_submission_file_paths.append(submission_file)

        # Submit submission files to hpc
        self.inimodel_submit()
        #self.save_inimodel()

    def initialize_inimodel(self):
        # Check if necessary settings are present, if not ask; if yes, confirm
        # Then create new running-folder in inimodel folder, user counter & date for multiple runs
        # Make sure to save inimodel_settings as log in that folder
        inimodel_settings = [
            'inimodel_cpus',
            'inimodel_crossover_range_min',
            'inimodel_crossover_range_max',
            'inimodel_crossover_step',
            'inimodel_iter',
            'inimodel_mask',
            'inimodel_shift',
            'inimodel_angle',
            'inimodel_angle_step',
            'inimodel_sym',
            'inimodel_max_res'
        ]
        # Checking setting
        for setting in inimodel_settings:
            if self.settings[setting] == '':
                print('Please specify ' + setting + ':')
                self.settings[setting] = input('')
        self.write_settings()
        # Confirm settings
        print('Found the following initial model settings:')
        for setting in inimodel_settings:
            print(setting + ' = ' + str(self.settings[setting]))
        print('Modify settings in the settings file (' + self.settings_path + ')')
        # Create new inimodel folder for the run
        # Set folder name
        self.date = self.set_date()
        inimodel_runs_name = self.date + '_inimodel_' + self.settings['inimodel_crossover_range_min'] + \
            '_to_' + self.settings['inimodel_crossover_range_max'] + 'co_' + str(self.job_counters['inimodel_counter'])
        self.inimodel_runs_master = os.path.join(self.inimodel_folder, inimodel_runs_name)
        # Create folder if it does not exist
        if not os.path.exists(self.inimodel_runs_master):
            os.mkdir(self.inimodel_runs_master)
        # Increase inimodel counter and save it
        self.job_counters['inimodel_counter'] += 1
        self.write_jobcounter()

    def write_inimodel_submission(self, directory, crossover):
        co = str(crossover)
        # Build output string
        submissionstring = '#!/bin/bash -l' + '\n'
        submissionstring += '#SBATCH -D ' + directory + '/\n'
        submissionstring += '#SBATCH -J inimodel' + '\n'
        submissionstring +='#SBATCH -C scratch' + '\n'
        submissionstring +='#SBATCH --partition=medium' + '\n'
        submissionstring +='#SBATCH --error=' + directory + '/inimodel_' + co + 'co.err' + '\n'
        submissionstring +='#SBATCH --output=' + directory + '/inimodel_' + co + 'co.out' + '\n'
        submissionstring +='#SBATCH --ntasks=' + str(self.settings['inimodel_cpus']) + '\n'
        submissionstring +='#SBATCH -t 02:00:00' + '\n'
        submissionstring +='#SBATCH --qos=short' + '\n'
        # Load relion module. Syntax might change in the future.
        submissionstring +='module purge' + '\n'
        submissionstring +='shopt -s expand_aliases' + '\n'
        submissionstring +='source /usr/users/rubsak/sw/rubsak.bashrc' + '\n'
        submissionstring +='use_relion4' + '\n'
        submissionstring +='# load relion/4.0.0' + '\n'
        submissionstring +='echo - e "$(hostname) modules: $(module list 2>&1 | grep relion --color=never)"' + '\n'
        # Get & write initial model command
        submissionstring += self.write_inimodel_command(crossover)
        # Write submission file
        submission_file_name = self.date + '_' + co + 'co_submission.sh'
        submission_file_path = os.path.join(directory, submission_file_name)
        with open(submission_file_path, 'w') as fout:
            fout.write(submissionstring)
        return submission_file_path

    def write_inimodel_command(self, crossover, inimodel_name=''):
        # Get values
        iter = self.settings['inimodel_iter']
        mask = self.settings['inimodel_mask']
        shift = self.settings['inimodel_shift']
        angle = self.settings['inimodel_angle']
        step = self.settings['inimodel_angle_step']
        sym = self.settings['inimodel_sym']
        max_res = self.settings['inimodel_max_res']
        px_size = self.settings['general_px_size']
        class_averages = self.settings['general_ca_location']
        cpus = self.settings['inimodel_cpus']
        # If not specified, set output-model name
        if inimodel_name == '':
            inimodel_name = str(crossover) + 'co_initial_model'
        # Build command
        inimodel_command = 'relion_helix_inimodel2d ' + '\\\n'
        inimodel_command += '--i ' + class_averages + ' \\\n'
        inimodel_command += '--o ' + inimodel_name + ' \\\n'
        inimodel_command += '--angpix ' + str(px_size) + ' \\\n'
        inimodel_command += '--iter ' + str(iter) + ' \\\n'
        inimodel_command += '--mask_diameter ' + str(mask) + ' \\\n'
        inimodel_command += '--search_shift ' + str(shift) + ' \\\n'
        inimodel_command += '--search_angle ' + str(angle) + ' \\\n'
        inimodel_command += '--step_angle ' + str(step) + ' \\\n'
        inimodel_command += '--sym ' + str(sym) + ' \\\n'
        inimodel_command += '--maxres ' + str(max_res) + ' \\\n'
        inimodel_command += '--j ' + str(cpus) + ' \n'
        # Write command into log file of master folder
        log_file_name = os.path.join(self.inimodel_runs_master, 'command.log')
        self.write_file(inimodel_command, log_file_name)
        return inimodel_command

    def inimodel_submit(self):
        for file in self.inimodel_submission_file_paths:
            print("Submitting " + file + " to hpc.")
            cmd_string = 'sbatch ' + file
            subprocess.run(cmd_string, shell=True, text=True, check=True)


    def refine(self):
        return




if __name__ == '__main__':
    project = Project()
    work_dir = project.workdir
    date = project.date
