# icube-relax-python
Unofficial python implementation of icube-relax [SIGMOD'00]

This is an unofficial implementation of the RELAX operator proposed by Sunita Sarawagi et al. in "i3: intelligent, interactive investigation of OLAP data cubes". You can refer [https://www.cse.iitb.ac.in/~sunita/icube/](https://www.cse.iitb.ac.in/~sunita/icube/) for official implementation.


```
@article{sarawagi2000i3,
  title={i3: intelligent, interactive investigation of OLAP data cubes},
  author={Sarawagi, Sunita and Sathe, Gayatri},
  journal={ACM SIGMOD Record},
  volume={29},
  number={2},
  pages={589},
  year={2000},
  publisher={ACM New York, NY, USA}
}
```

## Instruction

The implementation is based on MySQL. However, the query interface can be easily extended to other databases as we decompose many nested queries in the official implementation. The implementation only accepts one table for RELAX operator. You may construct a database view in case you need to link multiple tables.

You need to install MySQL and necessary python packages (```pip install -r requirements.txt```). Then, you need to modify ```spec.json``` based on your analytical tasks.

```
{
    "hostname": "localhost", // MySQL hostname
    "username": "root", // MySQL username
    "passwd": "123456", // MySQL password
    "database": "icube", // MySQL database name
    "table": "so2", // MySQL table/view name
    "measure":"SUM(SO2__KT_)", // desired measure
    "subspaces": [ // a pair of targeted subspace
        {
            "PRODUCER_TYPE": "Electric Utility", 
            "ENERGY_SOURCE": "Coal", 
            "YEAR": "1992"
        },
        {
            "PRODUCER_TYPE": "Electric Utility", 
            "ENERGY_SOURCE": "Coal", 
            "YEAR": "1993"
        }
    ],
    "threshold": 0.1, // threshold for generalization
    "topk": 10 // maximal allowed output results
}
```

Run ```python relax.py``` and it will output a list of common subspaces. For example,

```
For every ENERGY_SOURCE where PRODUCER_TYPE: Electric Utility,  the relationship value under YEAR: [1992, 1993] looks similar.
Besides, we also found the following individual entries looks similar.
{'PRODUCER_TYPE': 'Industrial Cogen', 'ENERGY_SOURCE': 'Petroleum'}
{'PRODUCER_TYPE': 'Industrial Cogen', 'ENERGY_SOURCE': 'Coal'}
{'PRODUCER_TYPE': 'Industrial Cogen', 'ENERGY_SOURCE': 'Natural Gas'}
{'PRODUCER_TYPE': 'Industrial Cogen', 'ENERGY_SOURCE': 'Other'}
{'PRODUCER_TYPE': 'Industrial Cogen', 'ENERGY_SOURCE': 'Geothermal'}
{'PRODUCER_TYPE': 'Industrial Cogen', 'ENERGY_SOURCE': 'Other Biomass'}
{'PRODUCER_TYPE': 'Industrial Cogen', 'ENERGY_SOURCE': 'Wood and Wood Derived Fuels'}
{'PRODUCER_TYPE': 'Industrial Cogen', 'ENERGY_SOURCE': 'Other Gases'}
{'PRODUCER_TYPE': 'Industrial Cogen', 'ENERGY_SOURCE': '*'}
{'PRODUCER_TYPE': 'Utility Sector Cogen', 'ENERGY_SOURCE': 'Petroleum'}
```