#!/usr/bin/env/python
# -*- coding: utf-8 -*-
#
# (c) 2016 WebDevOps.io
#
# This file is part of Dockerfile Repository.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the "Software"), to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and
# to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial portions
# of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
# THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS
# OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

from cleo import Command, Output
from jinja2 import Environment, FileSystemLoader
from webdevops import Dockerfile
from webdevops import DockerBuildTaskLoader
from webdevops import DockerfileUtility
from doit.doit_cmd import DoitMain

import sys

class DockerBuildCommand(Command):
    """
    Build images

    docker:build
        {--dry-run               : show only which images will be build}
        {--no-cache              : build without caching}
        {--t|threads=1           : threads}
        {--push                  : Push Dockerfiles }
        {--whitelist=?*          : image/tag whitelist }
        {--blacklist=?*          : image/tag blacklist }
    """

    configuration = False

    def __init__(self, configuration):
        Command.__init__(self)
        self.configuration = configuration

    def handle(self):
        doitOpts = []


        configuration = self.configuration

        # Enable docker build
        configuration['dockerBuild']['enabled'] = True
        configuration['dockerBuild']['noCache'] = self.option('no-cache')

        # Enable docker push if --push is added
        configuration['dockerPush']['enabled'] = self.option('push')

        configuration['threads'] = max(1, self.option('threads'))

        configuration['whitelist'] = self.option('whitelist')
        configuration['blacklist'] = self.option('blacklist')

        configuration['dryRun'] = self.option('dry-run')

        if self.output.is_verbose():
            configuration['verbosity'] = 2

        if self.option('dry-run'):
            configuration['threads'] = 1
            configuration['verbosity'] = 2

        if configuration['threads'] > 1:
            doitOpts.extend(['-n', configuration['threads'], '-P' 'thread'])

        sys.exit(DoitMain(DockerBuildTaskLoader.DockerBuildTaskLoader(configuration)).run(doitOpts))



