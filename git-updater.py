#!/usr/bin/env python

# Copyright (c) 2012 Ryan Zec
# Licensed: MIT (see LICENSE file for details) 

import subprocess
import os
import sys
import pwd
import ConfigParser
import optparse
import getpass

def parserConfigList(configObject, section, item):
    value = configObject.get(section, item)
    if (value[0] == "[") and (value[-1] == "]"):
        return eval(value)
    else:
        return value

def inTag():
    command = subprocess.Popen('git branch', shell=True, stdout=subprocess.PIPE)
    output = command.stdout.read().strip()
    command.wait()
    branches = output.split('\n')
    currentBranch = None

    for branch in branches:
        if branch[:2] == '* ':
            currentBranch = branch[2:len(branch)]
            break

    return currentBranch == '(no branch)'

def main():
    parser = optparse.OptionParser(description='Allows you to run git pull on any repository ',
                                          prog='git-updater',
                                          version='0.1.0',
                                          usage= '%prog [options] <relative path>')

    parser.add_option("--ref", "-r",
                      type='string',
                      help="The ref you want to use to set the repository to (branch, tag, etc...)",
                      default='')

    options, arguments = parser.parse_args()

    if len(arguments) != 1:
        parser.print_help()
        sys.exit()

    currentUser = os.getenv('SUDO_USER')

    if currentUser is None:
        print 'This script must be executed with a normal user with sudo in front, ex: sudo git-updater [repository path]'
        sys.exit()
    
    configPath = os.path.dirname(__file__)
    config = ConfigParser.ConfigParser()
    config.read(['%s/git-updater.conf' % configPath])

    gitPath = config.get('config', 'gitPath')
    runAsUser = config.get('config', 'runAsUser')
    repositoryPath = arguments[0]

    #see if access control in setup for the given repository
    try:
        accessList = parserConfigList(config, repositoryPath, 'access')
        remoteName = config.get(repositoryPath, 'remoteName')
    except ConfigParser.NoOptionError:
        print 'Error: Access control not setup for the \'%s\' repository' % arguments[0]
        sys.exit()

    #see if the true user has access to the given repository
    if currentUser not in accessList:
        print 'Error: %s user does not have access to updating the %s repository' % (currentUser, arguments[0])
        sys.exit()

    if runAsUser:
        os.setuid(pwd.getpwnam(runAsUser)[2])

    stringFormat = '%s%s' if gitPath[-1] == '/' else '%s/%s'
    gitRepositoryPath = stringFormat % (gitPath, arguments[0])

    #make the repository exists
    if not os.path.isdir(gitRepositoryPath):
        print 'Error: \'%s\' is not a valid directory' % gitRepositoryPath
        sys.exit()

    os.chdir(gitRepositoryPath)

    #make sure the repository is upto date
    print 'running command: "%s"' % 'git fetch --tags --prune'
    command = subprocess.Popen('git fetch --tags --prune', shell=True, stdout=subprocess.PIPE)
    output = command.stdout.read().strip()
    command.wait()

    print 'Updating Git Repository: %s' % gitRepositoryPath

    #see if we should be switching the repository to a different ref
    if options.ref:
        commandString = 'git checkout %s' % options.ref
        print 'running command: "%s"' % commandString
        command = subprocess.Popen(commandString, shell=True, stdout=subprocess.PIPE)
        output = command.stdout.read().strip()
        command.wait()
        print output

    #if we are not in a tag, do an update
    if not inTag():
        print 'running command: "%s"' % 'git pull'
        command = subprocess.Popen('git pull', shell=True, stdout=subprocess.PIPE)
        output = command.stdout.read().strip()
        command.wait()
        print output

#makes the script run from command line
if __name__ == '__main__':
    main()
