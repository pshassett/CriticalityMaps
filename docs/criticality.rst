Criticality Analysis
====================
The criticality analysis options currently supported in criticalityMaps
are fire and pipe criticality analysis.

Fire Criticality
^^^^^^^^^^^^^^^^
Fire criticality analysis is an assessment of the expected impact of
firefighting demands at a given location.  The analysis process consists of 
applying a fire fighting demand and measuring the impact on surrounding 
customers for all possible firefighting points in the system. Key parameters
to customize this analysis are:

* the firefighting demand (defaults to 1500 gpm)
* the duration of the fire demand (defaults to 2 hr)
* the diameter tresholds that define which pipes will have fire demands applied (defaults to all pipes between 6 and 8in in diameter)
 
See the fire_criticality_analysis in the api documentation for more details on
the customization options.


Pipe Criticality
^^^^^^^^^^^^^^^^
Pipe criticality analysis provides insight on where the most critical 
pipes of the system are. To determine the criticality of a single pipe, the 
pipe is closed during a simulation and the impact on surrounding customers 
is measured. This process is then repeated for all pipes of interest 
in the system.  Key parameters to customize this analysis are:

* The duration of the pipe closure (defaults to 48 hr)
* The diameter tresholds that define which pipes will have pipe closures applied (defaults to all pipes greater than 12in in diameter)

See the pipe_criticality_analysis in the api documentation for more details on
the customization options.

Multiprocessing
^^^^^^^^^^^^^^^
CriticalityMaps has the built-in ability to execute criticality 
analysis with mulitiprocessing, enabling multiple processors to work
on a set of simulations at once.  This offers a significant speedup in 
execution time, especially in cases with a large number of simulations and
on machines with extra computing capacity available.

To enable multiprocessing on your criticlaity analysis, in addition to setting
the multiprocess keyword argument to True, the code the criticality analysis
must be wrapped in a if name == "__main__" block as shown below.
    
    if __name__ == "__main__":
        criticalityMaps.criticality.fire_criticality_analysis(wn, multiprocess=True)

By default criticalityMaps will use about 2/3 of the machine's cpu. This 
behavior can be overridden by designating a value for `num_processors` to
either increase or decrease the amount of cpu's used.

