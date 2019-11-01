# txt2hpo
`txt2hpo` is a Python package for extracting phenotypes and encoding them as HPO ids, [Human Phenotype Ontology (HPO)](https://hpo.jax.org/app/).
`txt2hpo` understands inflection, extracts phenotypes consisting of multiple words arbitrary word order. 

# Installation

Install from GitHub
```bash

git clone https://github.com/GeneDx/txt2hpo.git
cd txt2hpo
python setup.py install

```

# Library usage

```python 
from txt2hpo.extract import hpo
import pprint
pp = pprint.PrettyPrinter(indent=4)

hpos = hpo("patient with developmental delay and hypotonia")
pp.pprint(hpos)


[   {'hpid': ['HP:0001290'], 'index': [5], 'matched': 'hypotonia'},
    {'hpid': ['HP:0001263'], 'index': [2, 3], 'matched': 'developmental delay'}]
    
    
```

By default `txt2hpo` will check spelling using a spellchecker trained on medical literature.
This feature can be turned off using the `correct_spelling` flag. Turning off spellchecker speeds up extraction.

```python 
from txt2hpo.extract import hpo
import pprint
pp = pprint.PrettyPrinter(indent=4)

hpos = hpo("patient with devlopental delay and hyptonia", correct_spelling=True)
pp.pprint(hpos)


[   {'hpid': ['HP:0001290'], 'index': [5], 'matched': 'hypotonia'},
    {'hpid': ['HP:0001263'], 'index': [2, 3], 'matched': 'developmental delay'}]
    
```




