#! /usr/bin/env python

import docker
import os
import json
import time
import sys
import re
import copy
from doit.task import dict_to_task
from doit.cmd_base import TaskLoader
from doit.doit_cmd import DoitMain

DOCKER_LATEST_TAG = 'ubuntu-16.04'
DOCKER_REPOSITORY = 'webdevops'
DOCKER_CLIENT = docker.from_env(assert_hostname=False)

DOCKER_FROM_REGEX = re.compile(ur'FROM\s+(?P<image>[^\s:]+)(:(?P<tag>.+))?', re.MULTILINE)

def findDockerfiles(basePath):
    ret = []
    for imageName in os.listdir(basePath):
        latestTagFound = False
        autoLatestDefinition = False

        for imageTag in os.listdir(os.path.join(basePath, imageName)):
            dockerImagePath = os.path.join(basePath, imageName, imageTag)
            dockerfilePath = os.path.join(dockerImagePath, 'Dockerfile')
            if os.path.isfile(dockerfilePath):
                dependency = False

                if imageTag == 'latest':
                    latestTagFound = True

                with open(dockerfilePath, 'r') as fileInput:
                    DockerfileContent = fileInput.read()
                    data = ([m.groupdict() for m in DOCKER_FROM_REGEX.finditer(DockerfileContent)])[0]

                    if data['image'].startswith(DOCKER_REPOSITORY + '/'):
                        dependency = data['image'] + ":" + data['tag']

                dockerDefinition = {
                    'dockerfile': dockerfilePath,
                    'path': dockerImagePath,
                    'image': {
                        'fullname': DOCKER_REPOSITORY + '/' + imageName + ':' + imageTag,
                        'name': DOCKER_REPOSITORY + '/' + imageName,
                        'tag':  imageTag,
                        'repository': DOCKER_REPOSITORY
                    },
                    'dependency': dependency
                }

                if imageTag == DOCKER_LATEST_TAG:
                    autoLatestDefinition = copy.deepcopy(dockerDefinition)
                    autoLatestDefinition['image']['fullname'] = DOCKER_REPOSITORY + '/' + imageName + ':latest'
                    autoLatestDefinition['image']['tag'] = 'latest'

                ret.append(dockerDefinition)

        if not latestTagFound and autoLatestDefinition:
            ret.append(autoLatestDefinition);

    for dockerfile in ret:
        if dockerfile['dependency']:
            print dockerfile['image']['fullname'] + ' --> ' + dockerfile['dependency']
        else:
            print dockerfile['image']['fullname']
    return ret

def dockerBuild(task, noCache=False):
    print task['image']['fullname']
    return

    response = DOCKER_CLIENT.build(
        path=task['path'],
        tag=task['image']['fullname'],
        pull=False,
        nocache=True,
        quiet=False,
        decode=True
    )
    for line in response:
        sys.stdout.write(line['stream'])
    return True

def taskTitle(task):
    return "Building %s" % task.name

def dockerAutobuild(repository):
    targets = dockerListDockerfiles(repository)
    for target in targets:
        yield {
            'basename': repository,
            'name': target['image']['fullname'],
            'title': taskTitle,
            'actions': [(dockerBuild, [target])],
            'targets': [target['dockerfile']],
            'verbosity': 2
        }

class DockerTaskLoader(TaskLoader):
    @staticmethod
    def load_tasks(cmd, opt_values, pos_args):
        taskList = []
        config = {'verbosity': 2}

        for dockerfile in findDockerfiles('./docker'):
            task = {
                'name': dockerfile['image']['fullname'],
                'title': taskTitle,
                'actions': [(dockerBuild, [dockerfile])],
                'targets': [dockerfile['image']['fullname']],
                'task_dep': []
            }

            if dockerfile['dependency']:
                task['task_dep'].append(dockerfile['dependency']);

            taskList.append(dict_to_task(task))
        return taskList, config

if __name__ == "__main__":
    argv = sys.argv[1:]

    if '--no-cache' in argv:
        argv.pop(argv.index('--no-cache'))

    sys.exit(DoitMain(DockerTaskLoader()).run(argv))
