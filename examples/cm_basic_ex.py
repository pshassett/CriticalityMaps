import wntr
import criticalityMaps as cm

# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger()
inp_file = 'Net3.inp'
wn = wntr.network.WaterNetworkModel(inp_file)
longlat_points = {'10': (-100.125, 40.125),
                  '213': (-99.875, 39.875)}
wn = wntr.morph.convert_node_coordinates_to_longlat(wn, longlat_points)

# Fire criticality example.
#cm.criticality.fire_criticality_analysis(wn, multiprocess=False,
#                                         output_dir='./fire_criticality'
#                                         )
#cm.mapping.make_criticality_map(wn, './fire_criticality/fire_criticality_summary.yml')

# Pipe criticality example.
#cm.criticality.pipe_criticality_analysis(wn, multiprocess=False,
#                                         output_dir='./pipe_criticality')
cm.mapping.make_criticality_map(wn,
                                './pipe_criticality/pipe_criticality_summary.yml')

'''
# Multiprocessing example
if __name__ == '__main__':
    cm.criticality.pipe_criticality_analysis(wn, multiprocess=False,
                                             output_dir='./pipe_criticality')
    cm.mapping.make_criticality_map(wn,
                                    './pipe_criticality/pipe_criticality_summary.yml')

    cm.criticality.fire_criticality_analysis(wn, multiprocess=False,
                                             output_dir='./fire_criticality')
    cm.mapping.make_criticality_map(wn,
                                    './fire_criticality/fire_criticality_summary.yml')

'''
# Dataframe-mapping example
pipe_diam = wn.query_link_attribute('diameter')
junction_demand = wn.query_node_attribute('base_demand',
                                          node_type=wntr.network.Junction)
node_elevation = wn.query_node_attribute('elevation')
wn_df = cm.mapping.wn_dataframe(wn,
                                node_data={'Base Demand': junction_demand,
                                           'Elevation': node_elevation},
                                link_data={'Diameter': pipe_diam}
                                )
wn_df.make_map(map_columns=['Base Demand', 'Elevation', 'Diameter'])
