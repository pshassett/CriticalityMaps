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
            for fire in bench.keys():
                if isinstance(bench[fire], dict):
                    for node, p in bench[fire].items():
                        p_float = round(float(p), 1)
                        bench[fire][node] = p_float                
            with open(os.path.join(testdir, "pipe_criticality_test.yml"), 'r') as fp:
                test = yaml.load(fp, Loader=yaml.BaseLoader)
            for fire in test.keys():
                if isinstance(test[fire], dict):
                    for node, p in test[fire].items():
                        p_float = round(float(p), 1)
                        test[fire][node] = p_float                
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
            for pipe in bench.keys():
                if isinstance(bench[pipe], dict):
                    for node, p in bench[pipe].items():
                        p_float = round(float(p), 1)
                        bench[pipe][node] = p_float
            with open(os.path.join(testdir, "fire_criticality_test.yml"), 'r') as fp:
                test = yaml.load(fp, Loader=yaml.BaseLoader)
            for pipe in test.keys():
                if isinstance(test[pipe], dict):
                    for node, p in test[pipe].items():
                        p_float = round(float(p), 1)
                        test[pipe][node] = p_float
            # Assert the results are equal
            self.assertDictEqual(bench, test)
        except Exception as e:
            raise e

    def test_segment_criticality(self):
        try:
            G = self.wn.get_graph()
            valve_layer = self.wntr.network.generate_valve_layer(self.wn, n=2, seed=123)
            node_segments, link_segments, seg_sizes = self.wntr.metrics.valve_segments(G, valve_layer)
            
            # Run segment criticality with minimal output.
            self.cm.segment_criticality_analysis(self.wn, link_segments, 
                                                 node_segments, valve_layer,
                                                 post_process=False,
                                                 output_dir=testdir,
                                                 summary_file="segment_criticality_test.yml"
                                                 )
            # Open the output and the benchmark yml files.
            with open(os.path.join(datadir, "segment_criticality_benchmark.yml"), 'r') as fp:
                bench = yaml.load(fp, Loader=yaml.BaseLoader)
            for segment in bench.keys():
                if isinstance(bench[segment], dict):
                    for node, p in bench[segment].items():
                        p_float = round(float(p), 1)
                        bench[segment][node] = p_float
            with open(os.path.join(testdir, "segment_criticality_test.yml"), 'r') as fp:
                test = yaml.load(fp, Loader=yaml.BaseLoader)
            for segment in test.keys():
                if isinstance(test[segment], dict):
                    for node, p in test[segment].items():
                        p_float = round(float(p), 1)
                        test[segment][node] = p_float
            # Assert the results are equal
            self.assertDictEqual(bench, test)
        except Exception as e:
            raise e

if __name__ == '__main__':
    unittest.main()
#    with open(os.path.join(datadir, "fire_criticality_benchmark.yml"), 'r') as fp:
#        bench = yaml.load(fp, Loader=yaml.BaseLoader)    
#    with open(os.path.join(testdir, "segment_criticality_test.yml"), 'r') as fp:
#        test = yaml.load(fp, Loader=yaml.BaseLoader)
