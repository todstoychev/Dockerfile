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
from webdevops import Provisioner
import os
import yaml
import yamlordereddictloader
import time
import Queue
import shutil

from pprint import pprint


class GenerateProvisionCommand(Command):
    """
    Provisionning docker images

    generate:provision
        {--image=?* : filter on images name }
        {--baselayout : Build the baselayout}
        {--t|thread=1 (integer): Number of threads to run }
    """

    conf = ''

    __threads = []

    __queue = ''

    configuration = False

    def __init__(self, configuration):
        Command.__init__(self)
        self.configuration = configuration

    def handle(self):
        start = time.time()
        self.__queue = Queue.Queue()
        if Output.VERBOSITY_VERBOSE <= self.output.get_verbosity():
            self.line('<info>provision :</info> %s' % self.configuration['provisionPath'])
            self.line('<info>dockerfile :</info> %s' % self.configuration['basePath'])
            self.line('<info>baselayout :</info> %s' % self.option('baselayout'))
            self.line('<info>thread :</info> %d' % self.option('thread'))
            if 0 < len(self.option('image')):
                self.line('<info>images </info> :')
                for crit in self.option('image'):
                    self.line("\t * %s" % crit)
        self.__load_configuration()
        self.__build_base_layout()
        self.__create_thread()
        for image_name in self.conf['provision']:
            if 0 == len(self.option('image')) or image_name in self.option('image'):
                self.__queue.put({'image_name': image_name, 'image_config': self.conf['provision'][image_name]})
        self.__queue.join()
        if os.path.exists('baselayout.tar'):
            os.remove('baselayout.tar')
        end = time.time()
        print("elapsed time : %d second" % (end - start))

    def __create_thread(self):
        for i in range(self.option('thread')):
            thread_name = "Pixie_%d" % i
            if Output.VERBOSITY_VERBOSE <= self.output.get_verbosity():
                self.line("<info>*</info> -> Create thread <fg=magenta>%s</>" % thread_name)
            provisioner = Provisioner.Provisioner(
                self.configuration['basePath'],
                self.configuration['provisionPath'],
                self.__queue,
                self.output
            )
            provisioner.setDaemon(True)
            provisioner.setName(thread_name)
            provisioner.start()
            # self.__threads.append(provisioner)

    def __load_configuration(self):
        """
        Load the configuration for provisioning image
        """
        stream = open(os.path.dirname(__file__) + "/../../conf/provision.yml", "r")
        self.conf = yaml.load(stream, Loader=yamlordereddictloader.Loader)

    def __build_base_layout(self):
        """
        Build tar file from _localscripts for bootstrap containers
        """
        if self.option('baselayout'):
            if Output.VERBOSITY_NORMAL <= self.output.get_verbosity():
                self.line('<info>* </info> Building localscipts')
            base_path = os.path.abspath(os.path.dirname(__file__) +"/../../baselayout/")
            shutil.make_archive('baselayout', 'bztar', base_path)
            os.rename('baselayout.tar.bz2', 'baselayout.tar')



