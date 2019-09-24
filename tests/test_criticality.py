# -*- coding: utf-8 -*-
"""
Created on Tue Sep 24 10:27:50 2019

@author: PHassett
"""
import unittest
import os
import yaml

# Get the current directory
testdir = os.path.dirname(os.path.abspath(str(__file__)))
datadir = os.path.join(testdir, 'data')
net3 = os.path.join(testdir, '..', 'examples', 'Net3.inp')


# run fire and pipe criticality and compare the results files to the expected result
class TestCriticality(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        import criticalityMaps as cm
        import wntr
        self.cm = cm
        self.wntr = wntr
        self.wn = self.wntr.network.WaterNetworkModel(net3)

    @classmethod
    def tearDownClass(self):
        pass

    def test_pipe_criticality(self):
        try:
            # Run pipe criticality with minimal output.
            self.cm.pipe_criticality_analysis(self.wn, post_process=False,
                                              output_dir=testdir,
                                              summary_file="pipe_criticality_test.yml")
            # Open the output and the benchmark yml files.
            with open(os.path.join(datadir, "pipe_criticality_benchmark.yml"), 'r') as fp:
                bench = yaml.load(fp, Loader=yaml.BaseLoader)
            with open(os.path.join(testdir, "pipe_criticality_test.yml"), 'r') as fp:
                test = yaml.load(fp, Loader=yaml.BaseLoader)
            # Assert the results are equal
            self.assertDictEqual(bench, test)
        except Exception as e:
            raise e

    def test_fire_criticality(self):
        try:
            # Run pipe criticality with minimal output.
            self.cm.fire_criticality_analysis(self.wn, post_process=False,
                                              output_dir=testdir,
                                              summary_file="fire_criticality_test.yml")
            # Open the output and the benchmark yml files.
            with open(os.path.join(datadir, "fire_criticality_benchmark.yml"), 'r') as fp:
                bench = yaml.load(fp, Loader=yaml.BaseLoader)
            with open(os.path.join(testdir, "fire_criticality_test.yml"), 'r') as fp:
                test = yaml.load(fp, Loader=yaml.BaseLoader)
            # Assert the results are equal
            self.assertDictEqual(bench, test)
        except Exception as e:
            raise e


if __name__ == '__main__':
    unittest.main()
