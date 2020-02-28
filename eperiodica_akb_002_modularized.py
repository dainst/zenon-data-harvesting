from eperiodica_modularized import harvest_eperiodica
from eperiodica_modularized import create_publication_dicts


def harvest(path):
    return_string = harvest_eperiodica('records/akb_002/', 'akb_002', 'Archäologie Bern', create_publication_dicts, 'Archäologischer Dienst des Kantons Bern', 'Bern', 'ger', 2, '000855529', 'ar p o||||||   a|')
    return return_string
