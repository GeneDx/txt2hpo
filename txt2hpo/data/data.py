
import json
import os
from txt2hpo.config import logger

__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))
try:
    with open(os.path.join(__location__,"spellcheck_vocab.json"), 'r') as fh:
        spellcheck_data = json.load(fh)
except(FileNotFoundError, PermissionError, ValueError) as e:
    logger.critical("spellcheck is not available or corrupted")
    exit(1)
