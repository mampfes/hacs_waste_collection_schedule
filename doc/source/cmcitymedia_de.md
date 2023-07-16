# CM City Media - Müllkalender

Support for schedules provided by [CM City Media - Müllkalender](https://sslslim.cmcitymedia.de/v1/). The official homepage is using the URL [cmcitymedia.de](https://www.cmcitymedia.de/de/startseite) instead.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: cmcitymedia_de
      args:
        hpid: 1
        realmid: 1
        district: 1
```

### Configuration Variables

**hpid**  
*(integer) (required)*

**realmid**  
*(integer) (optional) (automatic grab default one)*

**district**  
*(integer) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: cmcitymedia_de
      args:
        hpid: 415
        district: 1371
```

## Config Attributes
<!-- cmcitymedia_de -->
### www.buehlerzell.de - Müllkalender
* HPID: 1
#### Available Waste Types
* Bio- und Restmüllabfuhr (60 l/120 l/240 l/1,1 m³) 
* Gelbe Säcke 
* Papiertonne 
 
#### Districts (Name -> ID) 
* Bühlerzell -> 172 
 
### www.lrasha.de - Müllkalender
* HPID: 95
#### Available Waste Types
* Bio- und Restmüllabfuhr (60 l/120 l/240 l/1,1 m³) 
* Gelbe Säcke 
* Papiertonne 
 
#### Districts (Name -> ID) 
* Blaufelden -> 124 
* Braunsbach -> 110 
* Bühlertann -> 104 
* Bühlerzell -> 105 
* Crailsheim - Bezirk 1 -> 98 
* Crailsheim - Bezirk 2 -> 100 
* Crailsheim - Bezirk 3 -> 101 
* Crailsheim - Bezirk 4 -> 102 
* Crailsheim - Bezirk 5 -> 103 
* Fichtenau -> 95 
* Fichtenberg -> 92 
* Frankenhardt -> 96 
* Gaildorf - Stadt -> 85 
* Gaildorf - Teilorte -> 86 
* Gerabronn -> 115 
* Ilshofen -> 114 
* Kirchberg/Jagst -> 75 
* Kreßberg -> 97 
* Langenburg -> 129 
* Mainhardt -> 87 
* Michelbach/Bilz -> 89 
* Michelfeld -> 90 
* Oberrot -> 93 
* Obersontheim -> 106 
* Rosengarten -> 91 
* Rot am See -> 76 
* Satteldorf -> 77 
* Schrozberg -> 119 
* Schwäb. Hall 1 (Papier/Gelber Sack) -> 1267 
* Schwäb. Hall 1 (Rest/Bio) -> 79 
* Schwäb. Hall 2 (Papier/Gelber Sack) -> 1266 
* Schwäb. Hall 2 (Rest/Bio) -> 80 
* Schwäb. Hall 3 (Papier/Gelber Sack) -> 1265 
* Schwäb. Hall 3 (Rest/Bio) -> 81 
* Schwäb. Hall 4 (Papier/Gelber Sack) -> 1264 
* Schwäb. Hall 4 (Rest/Bio) -> 82 
* Schwäb. Hall 5 (Papier/Gelber Sack) -> 1262 
* Stimpfach -> 99 
* Sulzbach-Laufen -> 94 
* Untermünkheim -> 112 
* Vellberg  -> 109 
* Wallhausen -> 78 
* Wolpertshausen -> 113 
 
### www.hohenlohekreis.de - Müllkalender
* HPID: 168
#### Available Waste Types
* Bioenergietonne 
* Christbaumsammlung 
* Restmülltonne 
* Wertstofftonne Altpapier 
* Wertstofftonne Verpackung 
 
#### Districts (Name -> ID) 
* Bretzfeld 1 -> 146 
* Bretzfeld 2 -> 162 
* Dörzbach -> 147 
* Forchtenberg -> 148 
* Ingelfingen -> 149 
* Krautheim 1 -> 150 
* Krautheim 2 -> 168 
* Künzelsau 1 -> 151 
* Künzelsau 2 -> 163 
* Künzelsau 3 -> 164 
* Kupferzell -> 152 
* Mulfingen -> 153 
* Neuenstein -> 154 
* Niedernhall -> 155 
* Öhringen Stadt Nord -> 156 
* Öhringen Stadt Süd -> 165 
* Öhringen Teilorte -> 166 
* Pfedelbach 1 -> 157 
* Pfedelbach 2 -> 167 
* Schöntal -> 158 
* Waldenburg -> 159 
* Weißbach -> 160 
* Zweiflingen -> 161 
 
### Deggenhausertal App - Müllkalender
* HPID: 225
#### Available Waste Types
* Altmetallsammlung Vereine 
* Bioabfall 2-wöchentlich 
* Christbaumsammlung 
* Gartenabfall 
* Gelber Sack 
* Papier 4-wöchentlich 
* Papiercontainer 2-wöchentlich nur nach Anmeldung 
* Papiersammlung Vereine 
* Problemstoffsammlung 
* Restmüll 2-wöchentlich 
* Restmüll 4-wöchentlich 
 
#### Districts (Name -> ID) 
* Deggenhausertal -> 1350 
 
### kraichtal.de - Müllkalender 1
* HPID: 233
#### Available Waste Types
* Altpapier 
* Reststoff 
* Schadstoff 
* Wertstoff 
 
#### Districts (Name -> ID) 
* Alle Stadtteile -> 144 
* Bahnbrücken (Ba) -> 137 
* Bruchsal -> 145 
* Gochsheim (Go) -> 138 
* Landshausen (La) -> 139 
* Menzingen (Me) -> 140 
* Münzesheim (Mü) -> 135 
* Neuenbürg (Ne) -> 141 
* Oberacker (Oa) -> 136 
* Oberöwisheim (Oö) -> 134 
* Unteröwisheim (Uö) -> 142 
 
### www.kappelrodeck.de - Müllkalender
* HPID: 248
#### Available Waste Types
* Bio- und Restmüllabfuhr (60 l/120 l/240 l/1,1 m³) 
* Gelbe Säcke 
* Papiertonne 
 
#### Districts (Name -> ID) 
* Kappelrodeck -> 1287 
* Waldulm -> 1351 
 
### www.schutterwald.de - Müllkalender
* HPID: 331
#### Available Waste Types
* Bio- und Restmüllabfuhr (60 l/120 l/240 l/1,1 m³) 
* Gelbe Säcke 
* Papiertonne 
 
#### Districts (Name -> ID) 
* Schutterwald  -> 1268 
* Schutterwald-Höfen -> 1288 
* Schutterwald-Langhurst -> 1289 
 
### www.aschheim.de - Müllkalender
* HPID: 374
#### Available Waste Types
* Biomüll 
* Biotonnenreinigung 
* Gelber Sack 
* Giftmobil 
* Häckselaktion 
* Papier Aschheim 
* Papier Dornach 
* Restmüll Nord 
* Restmüll Süd 
* Sonderleerung 
 
#### Districts (Name -> ID) 
* Aschheim und Dornach -> 171 
 
### Mittelbiberach App - Müllkalender
* HPID: 390
#### Available Waste Types
* Bio- und Restmüllabfuhr 
* Gelbe Säcke 
* Papiertonne 
 
#### Districts (Name -> ID) 
* Mittelbiberach -> 1352 
 
### www.ehingen.de - Müllkalender
* HPID: 391
#### Available Waste Types
* Biotonne 
* Blaue Tonne 
* Christbaum 
* Gartenabraum 
* Gelber Sack 
* Hausmüll 
* Vereinssammlung Papier 
* Vereinssammlung Papier und Kartonagen 
 
#### Districts (Name -> ID) 
* Altbierlingen -> 1330 
* Altsteußlingen -> 1345 
* Berg -> 1331 
* Berkach -> 1325 
* Berkacher Grund -> 1313 
* Blienshofen -> 1327 
* Bockighofen -> 1332 
* Briel -> 1346 
* Dächingen -> 1347 
* Deppenhausen -> 1337 
* Dettingen -> 1322 
* Dintenhofen -> 1321 
* Ehingen -> 1312 
* Ehingen und alle Teilorte -> 1348 
* Erbstetten -> 1317 
* Ernsthof -> 1315 
* Frankenhofen -> 1323 
* Gamerschwang -> 1328 
* Granheim -> 1343 
* Herbertshofen -> 1320 
* Heufelden -> 1329 
* Kirchbierlingen -> 1326 
* Kirchen -> 1338 
* Mühlen -> 1339 
* Mundingen -> 1344 
* Nasgenstadt -> 1314 
* Rißtissen -> 1342 
* Schaiblishausen -> 1334 
* Schlechtenfeld -> 1340 
* Sontheim -> 1333 
* Stetten -> 1341 
* Tiefenhülen -> 1324 
* Unterwilzingen -> 1318 
* Vogelhof -> 1319 
* Volkersheim -> 1335 
* Weisel -> 1336 
 
### Blankenheim App - Müllkalender
* HPID: 415
#### Available Waste Types
* Altpapier 
* Biomüll 
* Grüngut 
* Leichtverpackungen 
* Restmüll 
* Sondermüll 
* Sondermüll Rewe-Parkplatz 
 
#### Districts (Name -> ID) 
* Bezirk A: Ahrdorf -> 1366 
* Bezirk B: Ahrhütte -> 1367 
* Bezirk C: Alendorf, Dollendorf, Hüngersdorf,
Ripsdorf, Waldorf -> 1368 
* Bezirk D: Blankenheim, Freilingen -> 1369 
* Bezirk E: Blankenheimerdorf, Nonnenbach -> 1370 
* Bezirk F: Lindweiler, Rohr -> 1371 
* Bezirk G: Lommersdorf -> 1372 
* Bezirk H: Mülheim -> 1373 
* Bezirk I: Reetz -> 1374 
* Bezirk J: Uedelhoven -> 1375 
 
### Senden (Westfalen) App - Müllkalender
* HPID: 420
#### Available Waste Types
* Biotonne 
* gelbe Tonne/säcke 
* Häcksler - Auf der Horst 
* Häcksler - Drachenwiese, Droste-zu-Senden-Str. 
* Häcksler - Gemeindl. Bauhof 
* Häcksler - Parkplatz Havixbecker Str. 
* Häcksler - Spielplatz Siebenstücken 
* Papiertonne 
* Restmülltonne 
* Schadstoffmobil 
 
#### Districts (Name -> ID) 
* Außenbereiche -> 1299 
* Ortsteil Bösensell -> 1300 
* Ortsteil Ottmarsbocholt -> 1301 
* Ortsteil Senden -> 1302 
 
### KEPTN App - Müllkalender
* HPID: 421
#### Available Waste Types
* Gelber Sack (Gelbe Tonne) 
* Papier, Pappe, Karton (Blaue Tonne) 
* Restabfall (Graue Tonne) 
 
#### Districts (Name -> ID) 
* Altstadt -> 1250 
* Amtsgerichtsviertel und Ringstraße / Am Tonnenhof -> 1249 
* AOK-Viertel / Großfaldern -> 1246 
* Barenburg / Harsweg -> 1242 
* Conrebbersweg -> 1241 
* Constantia -> 1237 
* Friesland / Borssum / Hilmarsum -> 1248 
* Hafen -> 1238 
* Jarssum / Widdelswehr -> 1251 
* Kleinfaldern / Herrentor / Neuer Delft -> 1286 
* Kulturviertel - nördlich Früchteburger Weg -> 1244 
* Kulturviertel - südlich Früchteburger Weg / Gewerbegebiet 2. Polderweg -> 1240 
* Larrelt -> 1236 
* Petkum Uphusen / Tholenswehr / Marienwehr -> 1252 
* Port Arthur / Transvaal -> 1239 
* Twixlum / Wybelsum / Logumer Vorwerk / Knock -> 1243 
* Wolthusen -> 1245 
 
### Emmendingen App - Müllkalender
* HPID: 424
#### Available Waste Types
* Bio- und Restmüllabfuhr (60 l/120 l/240 l/1,1 m³) 
* Gelbe Säcke 
* Papiertonne 
 
#### Districts (Name -> ID) 
* EM Bürkle-Bleiche/über der Elz -> 1293 
* EM Kollmarsreute/Windenreute -> 1295 
* EM Maleck/Mundingen -> 1294 
* EM Oberstadt -> 1290 
* EM Unterstadt -> 1292 
* EM Wasser -> 1296 
 
### DORFnet - Müllkalender
* HPID: 426
#### Available Waste Types
* Blaue Altpapiertonne 
* Gelbe Tonne 
* Graue Restmülltonne 
* Grüne Biotonne 
* Saisonbiotonne 
* Schadstoffsammlung 
* Windelsack 
 
#### Districts (Name -> ID) 
* Kalletal -> 1263 
 
### Messstetten App - Müllkalender
* HPID: 441
#### Available Waste Types
* Altpapiersammlung 
* Altpapiertonne 
* Biotonne 
* Christbaumsammlung 
* Gelber Sack 
* Grünabfall-Abfuhr 
* Kühlgeräte, Bildschirme und Fernsehgeräte 
* Restmülltonne 
* Restmülltonne 1100 l 
* Schadstoffsammlung Gewerbe in der Kreismülldeponie 
* Schadstoffsammlung im Wertstoffzentrum 
* Schrottsammlung 
 
#### Districts (Name -> ID) 
* Hartheim -> 1306 
* Heinstetten -> 1307 
* Hossingen -> 1308 
* Meßstetten 1 -> 1304 
* Meßstetten 2 -> 1305 
* Oberdigisheim -> 1309 
* Tieringen -> 1310 
* Unterdigisheim -> 1311 
 
### Oberstadion App - Müllkalender
* HPID: 447
#### Available Waste Types
* Altkleider 
* Altmetall 
* Bioabfalltonne 
* Blaue Tonne 
* Christbaumabfuhr 
* Gartenabraum 
* Gelber Sack 
* Hausmüll 
* Holzabfuhr 
* Problemstoffannahme im Entsorgungszentrum 
* Schadstoffmobil 
* Sperrmüll 
* Straßensammlung Papier 
 
#### Districts (Name -> ID) 
* Oberstadion -> 1349 
 
<!-- /cmcitymedia_de -->

### Hardcore Variant: Extract arguments from App

1. Decompile the App, extract the source code and search in the source code for hpid or get the hpid from somewhere else
2. Use the Wizard to get the other arguments or use something like postman to get the other arguments from the [API](https://sslslim.cmcitymedia.de/v1/)
