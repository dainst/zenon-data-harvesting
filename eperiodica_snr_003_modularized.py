from eperiodica_modularized import harvest_eperiodica
from eperiodica_modularized import create_publication_dicts


def harvest(path):
    return_string = harvest_eperiodica('records/snr_003/', 'snr_003', 'Schweizerische numismatische Rundschau', create_publication_dicts, 'Schweizerische Numismatische Gesellschaft', 'Bern', 'ger', 3, '001570578', 'ar p o||||||   a|')
    return return_string
