from webdav3.client import Client
options = {
    'webdav_hostname': 'https://cumulus.dainst.org/remote.php/webdav',
    'webdav_login':    'hnebel',
    'webdav_password': '9J_m3na'
}
client = Client(options)
client.Verify = False
print(client.info("Manual"))
print(client.free())
print(client.list())
client.mkdir("Periodicals_continuously_harvested/dir4") # hier Directory mit Datum hochladen
print(client.check("Periodicals_continuously_harvested"))
client.upload(remote_path="Periodicals_continuously_harvested/dir3", local_path="records/cipeg")
# hier lokales Directory mit den erstellten Files hochpushen
# local_path MUSS ein Pfad sein! sonst funktioniert das nicht! Erst anlegen, dann hochladen, dann löschen!