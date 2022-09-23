import pdb
from classes.Solution import Configuration, Result, EliteResults
import output_yaml_generator
import system_file_json_generator
import input_json_generator
from classes.Logger import Logger
from classes.System import System
from classes.Algorithm import Algorithm, RandomGreedy, Tabu_Search
import time
import sys
import os
import json
import numpy as np
import multiprocessing as mpp
from multiprocessing import Pool
import functools
import argparse


## Function to create a directory given its name (if the directory already
# exists, nothing is done)
#   @param directory Name of the directory to be created
def createFolder (directory):
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
    except OSError:
        print ("Error: Creating directory. " +  directory)


## Function to create the pure json file from system description by removing
# the comments lines
#   @param main_json_file Name of the file with the system description
#   @return Name of the pure json file with the system description
def create_pure_json(main_json_file):

    data = []

    # read file
    with open(main_json_file,"r") as fp:
        Lines = fp.readlines()

    # loop over lines and drop portions preceded by '#'
    for line in Lines:
        idx = line.find('#')
        if (idx != -1):
            last = line[-1]
            line = line[0:idx]
            if last == "\n":
                line = line+last
        data.append(line)

    # write data on the new json file
    pure_json = 'pure_json.json'
    filehandle = open(pure_json, "w")
    filehandle.writelines(data)
    filehandle.close()

    return pure_json


## Function to generate the output json file as the optimal placement for a
# specified Lambda
#   @param Lambda incoming workload rate
#   @param result The optimal Solution.Result returned by fun_greedy
#   @param S An instance of System.System class including system description
#   @param onFile True if the result should be printed on file (default: True)
def generate_output_json(Lambda, result, S, onFile = True):

    # generate name of output file (if required)
    if onFile:
        output_json = "Output_Files/Lambda_" + \
                        str(round(float(Lambda), 10)) + \
                            '_output_json.json'
    else:
        output_json = ""

    result.print_result(S, solution_file=output_json)


## Function to create an instance of Algorithm class and run the random greedy
# method
#   @param core_params Tuple of parameters required by the current core:
#                      (number of iterations, seed, logger)
#   @param S An instance of System.System class including system description
#   @param verbose Verbosity level
#   @return The results returned by Algorithm.RandomGreedy.random_greedy
def fun_greedy(core_params, S, verbose):
    core_logger = Logger(verbose=verbose)
    if core_params[2] != "":
        log_file = open(core_params[2], "a")
        core_logger.stream = log_file
    GA = RandomGreedy(S,seed=core_params[1], log=core_logger)
    result = GA.random_greedy( MaxIt=core_params[0], K=2)
    if core_params[2] != "":
        log_file.close()
    return result


## Function to get a list whose n-th element stores a tuple with the number
# of iterations to be performed by the n-th cpu core and the seed it should
# use for random numbers generation
#   @param iteration Total number of iterations to be performed
#   @param seed Seed for random number generation
#   @param cpuCore Total number of cpu cores
#   @param logger Current logger
#   @return The list of parameters required by each core (number of
#           iterations, seed and logger)
def get_core_params(iteration, seed, cpuCore, logger):
    core_params = []
    local = int(iteration / cpuCore)
    remainder = iteration % cpuCore
    for r in range(cpuCore):
        if logger.stream != sys.stdout:
            if cpuCore > 1 and logger.verbose > 0:
                log_file = ".".join(logger.stream.name.split(".")[:-1])
                log_file += "_" + str(r) + ".log"
            else:
                log_file = logger.stream.name
        else:
            log_file = ""
        r_seed = r * r * cpuCore * cpuCore * seed
        if r < remainder:
            core_params.append((local + 1, r_seed, log_file))
        else:
            core_params.append((local, r_seed, log_file))
    return core_params

def Random_Greedy_run(system_file,iteration_number_RG,seed,Max_time_RG,Lambda,K=1):

    with open(system_file, "r") as a_file:
         json_object = json.load(a_file)

    json_object["Lambda"] = Lambda
    S = System(system_json=json_object)
    RG=RandomGreedy(S,seed)
    best_result_no_update, elite, random_params=RG.random_greedy(K=K,MaxIt = iteration_number_RG, MaxTime= Max_time_RG)

    RG_cost=elite.elite_results[0].solution.objective_function(S)
    RG_solution=elite.elite_results[0].solution
   # np.save(output_folder + "/random_greedy_" + str(round(float(Lambda), 5))+".npy",Max_time_RG)
   # np.save(output_folder + "/random_greedy_cost_" +str(round(float(Lambda), 5))+".npy",RG_cost)
   # np.save(output_folder + "/random_greedy_solution_" + str(round(float(Lambda), 5))+".npy",RG_solution ,allow_pickle=True)
    elite_sol=[]
    if len(elite.elite_results)<K:
        K=len(elite.elite_results)
    for i in range(K):
        elite_sol.append(elite.elite_results[i].solution)
    return elite_sol

def TabuSearch_run(system_file,iteration_number_RG, max_iterations,
                 seed,Max_time_RG, Max_time, Lambda, K=1, besties_RG=None):


              with open(system_file, "r") as a_file:
                 json_object = json.load(a_file)
              json_object["Lambda"] = Lambda
              S = System(system_json=json_object)
              method_list=["best"]# ,"random"

              for method in method_list:

                  #  start=time.time()
                   # proc = mpp.current_process()
                   # pid = proc.pid
                   # seed=seed*pid

                   # GA=RandomGreedy(S,2)
                    #random_greedy_result=GA.random_greedy( MaxIt=iteration_number_RG)
                    # initial_solution=random_greedy_result[1].elite_results[0].solution
                    # initial_cost=random_greedy_result[1].elite_results[0].solution.objective_function(S)

                    #
                    #x=GA.change_component_placement(initial_solution)
                    # y=GA.get_partitions_with_j(initial_solution,x[0])



                    tabu_memory=50
                    #pdb.set_trace()
                    start=time.time()

                    TS_Solid= Tabu_Search(iteration_number_RG,seed,system=S,Max_time_RG=Max_time_RG,K=K, besties_RG=besties_RG)
                    best_solution, best_cost,current_cost_list,best_cost_list, time_list=TS_Solid.run_TS (method, tabu_memory, min_score=None, max_steps=max_iterations,Max_time=Max_time)
                    TS_time=time.time()-start
                    #print()
              result = Result()
              result.solution=best_solution
              result.objective_function(S)
              feasible = result.check_feasibility(S)
              return result



def main(application_dir):
    error = Logger(stream = sys.stderr, verbose=1, error=True)
    input_json_path = input_json_generator.make_input_json(application_dir)
    with open(input_json_path) as a_file:
        input_json = json.load(a_file)
    if "Methods" in input_json.keys():
        Methods=input_json["Methods"]
        if "method1" in Methods.keys():
            name=Methods["method1"]["name"]
            if name == "RandomGreedy":
                iteration_number_RG=Methods["method1"]["iterations"]
                Max_time_RG=Methods["method1"]["duration"]
        else:
            error.log("{} does not exist".format("Methods"))
            sys.exit(1)
    else:
        error.log("{} does not exist".format("Methods"))
        sys.exit(1)
    if "method2" in Methods.keys():
        name=Methods["method2"]["name"]
        startingPointNumber=Methods["method2"]["startingPointNumber"]
        max_iteration_number=Methods["method2"]["iterations"]
        Max_time=Methods["method2"]["duration"]
    print("\nStart parsing YAML files... ")
    system_file = system_file_json_generator.make_system_file(application_dir)
    #system_file = input_dir+"/SystemFile-Demo.json"#"ConfigFiles/RG-MaskDetection.json" # "ConfigFiles/Random_Greedy.json"



    start_lambda = 0.0000014
    end_lambda = 0.0000015
    step = 0.0000001
    seed = 2
    Lambda = start_lambda
    # system_file = create_pure_json(system_file_path)
    with open(system_file, "r") as a_file:
        json_object = json.load(a_file)
    json_object["Lambda"] = Lambda

    print("\n Start parsing config files... ")
    S = System(system_json=json_object)#, log=Logger(verbose=2))
    print("\n Start searching by  Random Greedy ... ")
    starting_points=Random_Greedy_run(system_file,iteration_number_RG,seed,Max_time_RG,Lambda,startingPointNumber)
    print("\n Start searching by  Local search ... ")
    result=TabuSearch_run(system_file,iteration_number_RG, max_iteration_number, seed,Max_time_RG, Max_time,Lambda, besties_RG=starting_points)

    output_json=application_dir + "/space4ai-d" "/Output.json"
    result.print_result(S,output_json)
    output_yaml_generator.main(application_dir)



if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="SPACE4AI-D")

    parser.add_argument("-C", "--config_file",
                        help="System configuration file")
    parser.add_argument('-O', "--output_file",
                        help="Output folder")


    args = parser.parse_args()

    # initialize error stream
    error = Logger(stream = sys.stderr, verbose=1, error=True)
    dic={}
    # check if the system configuration file exists
    if not os.path.exists(args.config_file):
        error.log("{} does not exist".format(args.config_file))
        sys.exit(1)
    else:
        input_dir=args.config_file

    if not os.path.exists(args.output_file):
        error.log("{} does not exist".format(args.output_file))
        sys.exit(1)
    else:
        output_dir=args.output_file
    #output_dir="OutputFiles_demo"
    #input_dir="ConfigFiles_demo"
    main("Demo_project")#input_dir,output_dir)
