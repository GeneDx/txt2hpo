# txt2hpo
`txt2hpo` is a Python library for extracting HPO-encoded phenotypes from text.
`txt2hpo` recognizes differences in inflection (e.g. hypotonic vs. hypotonia), handles negation and comes with a built-in medical spellchecker. 

# Installation

Install from GitHub
```bash

git clone https://github.com/GeneDx/txt2hpo.git
cd txt2hpo
python setup.py install

```

# Library usage

```python 
from txt2hpo.extract import Extractor
extract = Extractor()

result = extract.hpo("patient with developmental delay and hypotonia")

print(result.hpids)


["HP:0001263", "HP:0001290"]
    
```

`txt2hpo` will attempt to correct spelling errors by default, at the cost of slower processing.
This feature can be turned off by setting the `correct_spelling` flag to `False`. 

```python 
from txt2hpo.extract import Extractor
extract = Extractor(correct_spelling = False)
result = extract.hpo("patient with devlopental delay and hyptonia")

print(result.hpids)

[]
 
    
```

`txt2hpo` handles negation using negspacy. To remove negated phenotypes set `remove_negeted` flag to True.
 

```python 
from txt2hpo.extract import Extractor
extract = Extractor(remove_negated=True)
result = extract.hpo("patient has developmental delay but no hypotonia")

print(result.hpids)

["HP:0001263"]
 
    
```

`txt2hpo` picks the longest overlapping phenotype by default. To disable this feature set `remove_overlapping` flag to False.
 

```python 
from txt2hpo.extract import Extractor
extract = Extractor(remove_overlapping=False)
result = extract.hpo("patient with polycystic kidney disease")

print(result.hpids)

["HP:0000113", "HP:0000112"]


extract = Extractor(remove_overlapping=True)
result = extract.hpo("patient with polycystic kidney disease")

print(result.hpids)

["HP:0000113"]
 
    
```


`txt2hpo` outputs a valid JSON string.

```python 
from txt2hpo.extract import Extractor
extract = Extractor()

result = extract.hpo("patient with developmental delay and hypotonia")

print(result.json)


'[{"hpid": ["HP:0001290"], "index": [37, 46], "matched": "hypotonia"}, 
{"hpid": ["HP:0001263"], "index": [13, 32], "matched": "developmental delay"}]'

    
```

