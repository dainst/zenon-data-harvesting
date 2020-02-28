from eperiodica_modularized import harvest_eperiodica
from eperiodica_modularized import create_publication_dicts


def harvest(path):
    return_string = harvest_eperiodica('records/bat_001/', 'bat_001', 'Bollettino dell’Associazione Archeologica Ticinese', create_publication_dicts, 'Associazione Archeologica Ticinese', 'Lugano', 'ita', 3, '001543081',  'ar p o||||||   a|')
    return return_string
