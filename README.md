# zenon-data-harvesting
Contains scripts for harvesting external bibliographic title data. The main script creates a log.json where it saves harvesting state information for the last succesful run. Successive script runs will always check the log.json created by the previous run and start harvest everything up to the logged state. This makes it necessary to retain a "master" log by committing the current log to the repository.

## Dockerized run
Because the python dependencies are quite complex and this project is not actively maintained, we created a [Dockerfile](Dockerfile) and [docker-compose.yml](docker-compose.yml) that let's you create a docker image with the correct dependencies installed.

Given that you have both Docker and docker-compose installed, run from the main directory:
```bash
docker-compose up
```

## Main scripts

_harvest_new_records_
Starts other modules to harvest metadata. Pushes created MARC-Data and logfiles to 
Cumulus.

_create_new_record_ creates MARC-Data from harvested metadata

_harvest_records_ saves and splits created MARC-Data, updates logfile

_find_reviewed_title_ searches for reviewed titles in Zenon in order to create links

_find_exisiting_doublets_ checks if metadata of manifestation is already included in zenon

## Scripts for getting metadata from publications

aegyptiaca_modularized, antiquite_modularized, berrgk_modularized, BMCR_modularized,
cipeg_modularized, lucentum_modularized, efb_modularized, eperiodica_akb_002_modularized, eperiodica_bat_001_modularized, eperiodica_snr_003_modularized,
gerion_modularized, gnomon_modularized, groma_modularized,
hsozkult_modularized, late_antiquity_modularized_new, maa_journal_current_modularized,
sardinia_corsica_baleares_modularized, kokalos, world_prehistory,
germania_modularized, propylaeum_books,zephyrus_modularized,
athener_mitteilungen
