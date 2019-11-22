# txt2hpo
`txt2hpo` is a Python library for extracting HPO-encoded phenotypes from text.
`txt2hpo` recognizes differences in inflection (e.g. hypotonic vs. hypotonia), is able to parse complex multi-word phenotypes with differing word order (e.g. developmentally delayed vs. developmental delay) and comes with a built-in medical spellchecker. 

# Installation

Install using pip:
```bash
pip install txt2hpo
```

Install from GitHub
```bash

git clone https://github.com/GeneDx/txt2hpo.git
cd txt2hpo
python setup.py install

```

# Library usage

```python 
from txt2hpo.extract import hpo

hpo_ids = hpo("patient with developmental delay and hypotonia")

print(hpo_ids)

[{"hpid": ["HP:0001290"], "index": [37, 46], "matched": "hypotonia"}, 
 {"hpid": ["HP:0001263"], "index": [13, 32], "matched": "developmental delay"}]
    
```

`txt2hpo` will attempt to correct spelling errors by default, at the cost of slower processing speed.
This feature can be turned off by setting the `correct_spelling` flag to `False`. 

```python 
from txt2hpo.extract import hpo

hpo_ids = hpo("patient with devlopental delay and hyptonia", correct_spelling=True)

print(hpo_ids)

[{"hpid": ["HP:0001290"], "index": [37, 46], "matched": "hypotonia"}, 
 {"hpid": ["HP:0001263"], "index": [13, 32], "matched": "developmental delay"}]
    
```

`txt2hpo` outputs a valid JSON string, use`json.loads` to convert `txt2hpo` output to JSON/python list.

```python
import json
from txt2hpo.extract import hpo
hpo_ids = json.loads(hpo(text_string))
```


