# txt2hpo
`txt2hpo` is a Python package for extracting HPO-encoded phenotypes from text, [Human Phenotype Ontology (HPO)](https://hpo.jax.org/app/).
`txt2hpo` accounts for inflection, is able to parse complex multi-word phenotypes and comes with a built-in medical spellchecker. 

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

hpos = hpo("patient with developmental delay and hypotonia")
print(hpos)


[   {'hpid': ['HP:0001290'], 'index': [5], 'matched': 'hypotonia'},
    {'hpid': ['HP:0001263'], 'index': [2, 3], 'matched': 'developmental delay'}]
    
    
```

`txt2hpo` will attempt to correct spelling errors by default, at the cost of slower processing speed.
This feature can be turned off by setting the `correct_spelling` flag to `False`. 

```python 
from txt2hpo.extract import hpo
import pprint
pp = pprint.PrettyPrinter(indent=4)

hpos = hpo("patient with devlopental delay and hyptonia", correct_spelling=True)
pp.pprint(hpos)


[   {'hpid': ['HP:0001290'], 'index': [5], 'matched': 'hypotonia'},
    {'hpid': ['HP:0001263'], 'index': [2, 3], 'matched': 'developmental delay'}]
    
```




