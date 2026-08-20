# Surveillance Optimization For Early Wildfire Detection

## Metadata
- Author: [Mert Ali Yiğit](mailto:mertaliyigit06@gmail.com), [Erdi Daşdemir](mailto:edasdemir@hacettepe.edu.tr) (Corresponding), [Çağrı Koç](mailto:cagri.koc@hacettepe.edu.tr)
- Weblink:
[https://github.com/Agoraaa/wildfire-surveillance-2026](https://github.com/Agoraaa/fire-surveillance-2026)

## Summary
This repository contains all the code related to the accompanying paper, aiming to enhance its extendability and ease of applicability.

## File list
- The following python code is provided in `src`
    - `src/automatic_generator.py`: Script for generating instances.
    - `src/model.py`: Class structure to store the problem data.
    - `src/main.py`: Main entrypoint of the code.
    - `src/solver.py`: Code related to the mathematical model.
    - `src/simulator.py`: Code related to the simulation algorithm.
- `example_instance.xlsx`: Provided instance as an example.
- `example_instance_output.xlsx`: Already solved solution of the example instance. 
- `requirements.txt`: Text file containing required Python modules

## Usage
For necessary modules, type
> pip install -r requirements.txt

to your terminal. 


If you additionally want to use `automatic_generator.py` script, additionally install [this](https://github.com/pvigier/perlin-numpy) package in the GitHub repository by
> pip install git+https://github.com/pvigier/perlin-numpy 



You can solve singular problem files by typing
> python src/main.py <instance_name.xlsx>

to your terminal, provided that `<instance_name.xlsx>` is a valid input file (e.g `example_instance.xlsx`). You can batch solve instances by providing a folder instead of a file.


For generating instances, set the parameters in `automatic_generator.py` and executing it by calling
> python automatic_generator.py

which will generate the input format in the current directory.

## Acknowledgements
This work was supported by the Scientific and Technological Research Council of Türkiye (TÜBİTAK)
under grant number 125R171. The third author was supported by the Turkish Academy of Sciences
(TÜBA). These supports are gratefully acknowledged.

## License and Referencing
The code is licensed under GNU General Public License, which can be accessed [here](/LICENSE). If you in any way use this
code for research that results in publications, please cite our original
article listed above.

You can use the following BibTeX entry
```
<placeholder>
```
