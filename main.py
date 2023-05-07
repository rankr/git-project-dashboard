#coding: utf-8
import os
import argparse
import sys
from gpd import add_repo, list_repo, remove_repo, calculate_repo
#from test import getidx

def initParse():

    parser = argparse.ArgumentParser()
    
    #add project path to git-project-dashboard
    parser.add_argument('-a', '--add', type=str, help = "add project path to git-project-dashbaord")
    
    #list project
    parser.add_argument('-l', '--list', help = "list project", action='store_true')

    #remove project path from git-project-dashboard
    parser.add_argument('-r', '--remove', type=str, help = "remove project path", nargs = "?")

    #re-calculate project-dashboard of specified project
    parser.add_argument('-c', '--calculate', type=str, help = "re-calculate project-dashboard of specified project")

    #for developer's testing
    parser.add_argument('-t', '--test', help = "for developer's testing")
    
    return parser


if __name__ == '__main__':
    #parsing the argus
    parser = initParse()
    args = vars(parser.parse_args())

    if args['test']:
        exit()
    if args['add']:
        add_repo.add_path(os.path.abspath(args['add']))
        exit()
    if args['list']:
        list_repo.list_path()
        exit()
    if args['remove']:
        remove_repo.remove_path(os.path.abspath(args['remove']))
        exit()  
    if args['calculate']:
        calculate_repo.calculate(os.path.abspath(args['calculate']))
        exit()
        
        