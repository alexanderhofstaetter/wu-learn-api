# WU Learn API

Eine Python API für das E-Learning System der WU Wien "[Learn@WU](https://learn.wu.ac.at/)". Die API verwendet python.requests und BeautifulSoup um die Daten zu parsen und liefert die extrahiertem Daten anschließend im JSON Format zurück.

Die Plattform Learn@WU basiert auf [DotLRN](http://www.dotlrn.org/)

## Dependencies (u.a.)

`pip install python-dateutil beautifulsoup4 requests argparse lxml dill`

## Authentifizierung

Entweder über die parameter --username und --password die Zugangsdaten übermitteln, oder alternativ ein CredentialsFile mit --credfile angeben.

Das credfile muss folgendes Format aufweisen.

```
username=_USER_
password=_PASS_
```

## Programmaufruf

python api.py --username=_USER_ --password=_PASS_ --action=_ACTION_

Als Action stehen folgende Optionen zur Verfügung.

### lvs()
Liefert alle aktuellen und aktiven Lehrveranstaltungen.

``` json
	"data": {
		"1234.18s": {
			"gradebook": "0", 
			"key": "1234.18s", 
			"name": "Accounting & Management Control III", 
			"number": "1234", 
			"semester": "18s", 
			"url": "https://learn.wu.ac.at/dotlrn/classes/amc3/1234.18s/", 
            "url_gradebook": "https://learn.wu.ac.at/dotlrn/classes/amc3/1234.18s/gradebook/student/"
		}
	}
```


### grades()
Liefert alle Noten in den Notenbücher der LVs.
```
	"grades": {
		"0": {
			"comments": "", 
			"date": "01.03.2018 09:00:00", 
			"entry_date": "01.05.2018 14:00:000", 
			"points_max": "12,00", 
			"points_sum": "12,00", 
			"source_id": "Manuell", 
			"teacher_name": "Vorname Nachname", 
			"title": "Mitarbeitspunkte", 
			"type": "Regulär"
		}
	}
```

### exams()
Liefert alle vorhanden Prüfungen aus der Prüfungseinsicht zurück.
```
	"1": {
            "date": "30.01.2018", 
            "number": "581234", 
            "pdf": "JVBERi0xajQKJeLjz92323MKMSAwIG9iajw8L1BA2R1Y2VyKGh0bWxkb2MgMS4ALjI4IENvcHlyaWdodCAxOTk3LTIwAYgRWFzeSBTb2Z0d2FyZSBQcm9kdWN0cywgQWxsIFJpZ2h0cyadasBSZXNlcndZlZC...", 
            "title": "Einführung in die Betriebswirtschaft"
	}, 
```

### exams()
Liefert alle sichtbaren Ankündigungen.
```
	"data": {
        "0": {
            "author": "Vorname Nachname", 
            "date": "01. Juni 2018", 
            "lv": "1234.18", 
            "number": "271234567", 
            "title": "Lehrtutor/in gesucht!", 
            "url": "https://learn.wu.ac.at/dotlrn/classes/fin/1234.18s/news/item?item_id=271234567"
        }
    } 

```

## Caching
Die API speichert die aktuelle session in einem File und setzt, sofern diese gültig ist, bei einem neuen Aufruf die alte Session fort.

# Copyright & License

Copyright (c) 2018 Alexander Hofstätter - Released under the [MIT license](LICENSE.md).