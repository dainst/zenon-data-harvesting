#!/bin/bash

if [[ -z ${KOHA_BASIC_INSTALL_ROOT:+x} ]] ;
then
    echo "Please set KOHA_BASIC_INSTALL_ROOT!"
    exit 1
fi

if [[ -z ${MACHINE_NAME:+x} ]] ;
then
    MACHINE_NAME="Unnamed machine"
fi

mkdir -p "$KOHA_BASIC_INSTALL_ROOT/export/log/"
LOG="$KOHA_BASIC_INSTALL_ROOT/export/log/`date +\%Y-\%m-\%d`.log"

"$KOHA_BASIC_INSTALL_ROOT/export/export_updated_marc_data.sh" `date +\%Y-\%m-\%d -d "-1 day"` /var/www/download/exports/`date +\%Y-\%m-\%d` &> "$LOG"

if grep --ignore-case -q error "$LOG";
then
    cat "$LOG" | mail -s "[$MACHINE_NAME] marc data export -- ERROR" -a "From: zenonmailagent@dainst.de" zenondai@dainst.org
else
    cat "$LOG" | mail -s "[$MACHINE_NAME] marc data export -- SUCCESS" -a "From: zenonmailagent@dainst.de" zenondai@dainst.org
fi
