# zenon-data-harvesting
Contains scripts for harvesting external bibliographic title data

**Main scripts**

_harvest_new_records_
Starts other modules to harvest metadata. Pushes created MARC-Data and logfiles to 
Cumulus.

_create_new_record_ creates MARC-Data from harvested metadata

_harvest_records_ saves and splits created MARC-Data, updates logfile

_find_reviewed_title_ searches for reviewed titles in Zenon in order to create links

_find_exisiting_doublets_ checks if metadata of manifestation is already included in zenon

**Scripts for getting metadata from publications**

aegyptiaca_modularized, antiquite_modularized, berrgk_modularized, BMCR_modularized,
cipeg_modularized, lucentum_modularized, efb_modularized, eperiodica_akb_002_modularized, eperiodica_bat_001_modularized, eperiodica_snr_003_modularized,
gerion_modularized, gnomon_modularized, groma_modularized,
hsozkult_modularized, late_antiquity_modularized_new, maa_journal_current_modularized,
sardinia_corsica_baleares_modularized, kokalos, world_prehistory,
germania_modularized, propylaeum_books,zephyrus_modularized,
athener_mitteilungen