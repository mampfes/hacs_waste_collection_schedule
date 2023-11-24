# Apps by Abfall+

Support for schedules provided by [Apps by Abfall+](https://www.abfallplus.de/), serving multiple, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: app_abfallplus_de
      args:
        app_id: APP ID
        city: STADT/KOMMUNE
        strasse: STRASSE
        hnr: HAUSNUMMER
        bundesland: BUNDESLAND
        landkreis: LANDKREIS
        
```

### Configuration Variables

**app_id**  
*(String) (required)*

**city**  
*(String) (optional)*

**strasse**  
*(String) (required)*

**hnr**  
*(String | Integer) (optional)*

**bundesland**  
*(String) (optional)*

**landkreis**  
*(String) (optional)*

## Examples

```yaml
waste_collection_schedule:
    sources:
    - name: app_abfallplus_de
      args:
        app_id: de.albagroup.app
        city: Braunschweig
        strasse: Hauptstraße
        hnr: 7A
```

```yaml
waste_collection_schedule:
    sources:
    - name: app_abfallplus_de
      args:
        app_id: de.k4systems.bonnorange
        strasse: Auf dem Hügel
        hnr: 6
```

```yaml
waste_collection_schedule:
    sources:
    - name: app_abfallplus_de
      args:
        app_id: de.k4systems.abfallappwug
        city: Bergen
        strasse: Alle Straßen
```

```yaml
waste_collection_schedule:
    sources:
    - name: app_abfallplus_de
      args:
        app_id: de.k4systems.awbgp
        city: Bad Boll
        hnr: Alle Hausnummern
        strasse: Ahornstraße
```

## How to get the source argument

Use the app of your local provider and select your address. Provide all arguments that are requested by the app. 

If you do not want to install a App you can run the script located at custom_components/waste_collection_schedule/waste_collection_schedule/wizard/app_abfallplus_de.py make sure that the python package inquirer is installed (`pip install inquirer`)

The app_id can be found from the url of the play store entry: https://play.google.com/store/apps/details?id={app_id} or from the following table:

<!--Begin of service section-->
|app_id|supported regions|
|-|-|
| de.albagroup.app | Berlin, Braunschweig, Havelland, Oberhavel, Ostprignitz-Ruppin, Tübingen |
| de.k4systems.abfallinfocw | Kreis Calw |
| de.k4systems.abfallinfoapp | Mechernich und Kommunen |
| de.k4systems.abfallappes | Landkreis Esslingen |
| de.k4systems.egst | Kreis Steinfurt |
| de.idcontor.abfallwbd | Duisburg |
| de.ucom.abfallavr | Rhein-Neckar-Kreis |
| de.k4systems.abfallapprv | Kreis Ravensburg |
| de.k4systems.avlserviceplus | Kreis Ludwigsburg |
| de.k4systems.muellalarm | Schönmackers |
| de.k4systems.abfallapploe | Kreis Lörrach |
| de.k4systems.abfallappart | Kreis Trier-Saarburg |
| de.k4systems.abfallapp | Kreis Augsburg |
| de.k4systems.abfallappvorue | Kreis Vorpommern-Rügen |
| de.k4systems.abfallappfds | Kreis Freudenstadt |
| de.k4systems.abfallscout | Kreis Bad Kissingen |
| de.k4systems.avea | Leverkusen |
| de.k4systems.neustadtaisch | Kreis Neustadt/Aisch-Bad Windsheim |
| de.k4systems.abfalllkswp | Kreis Südwestpfalz |
| de.k4systems.awbemsland | Kreis Emsland |
| de.k4systems.abfallappclp | Kreis Cloppenburg |
| de.k4systems.abfallappnf | Kreis Nordfriesland |
| de.k4systems.abfallappog | Ortenaukreis |
| de.k4systems.abfallappmol | Kreis Märkisch-Oderland |
| de.k4systems.kufiapp | Landkreis Wunsiedel im Fichtelgebirge |
| de.k4systems.abfalllkbz | Kreis Bautzen |
| de.k4systems.abfallappbb | Landkreis Böblingen |
| de.k4systems.abfallappla | Landshut |
| de.k4systems.abfallappwug | Kreis Weißenburg-Gunzenhausen |
| de.k4systems.abfallappik | Ilm-Kreis |
| de.k4systems.leipziglk | Landkreis Leipzig |
| de.k4systems.abfallappbk | Bad Kissingen |
| de.cmcitymedia.hokwaste | Hohenlohekreis |
| de.abfallwecker | Rottweil, Tuttlingen, Waldshut, Prignitz, Nordsachsen |
| de.k4systems.abfallappka | Kreis Karlsruhe |
| de.k4systems.lkgoettingen | Abfallwirtschaft Altkreis Göttingen, Abfallwirtschaft Altkreis Osterode am Harz |
| de.k4systems.abfallappcux | Kreis Cuxhaven |
| de.k4systems.abfallslk | Salzlandkreis |
| de.k4systems.abfallappzak | ZAK Kempten |
| de.zawsr | ZAW-SR Straubing |
| de.k4systems.teamorange | Kreis Würzburg |
| de.k4systems.abfallappvivo | Kreis Miesbach |
| de.k4systems.lkgr | Landkreis Görlitz |
| de.k4systems.zawdw | AWG Donau-Wald |
| de.k4systems.abfallappgib | Kreis Wesermarsch |
| de.k4systems.wuerzburg | Würzburg |
| de.k4systems.abfallappgap | Kreis Garmisch-Partenkirchen |
| de.k4systems.bonnorange | Bonn |
| de.gimik.apps.muellwecker_neuwied | Kreis Neuwied |
| abfallH.ucom.de | Kreis Heilbronn |
| de.k4systems.abfallappts | Kreis Traunstein |
| de.k4systems.awa | Augsburg |
| de.k4systems.abfallappfuerth | Kreis Fürth |
| de.k4systems.abfallwelt | Kreis Kitzingen |
| de.k4systems.lkemmendingen | Kreis Emmendingen |
| de.k4systems.abfallkreisrt | Kreis Reutlingen |
| de.k4systems.abfallappmetz | Metzingen |
| de.k4systems.abfallappmyk | Kreis Mayen-Koblenz |
| de.k4systems.abfallappoal | Kreis Ostallgäu |
| de.k4systems.regioentsorgung | RegioEntsorgung AöR |
| de.k4systems.abfalllkbt | Kreis Bayreuth |
| de.k4systems.awvapp | Kreis Vechta |
| de.k4systems.aevapp | Schwarze Elster |
| de.k4systems.awbgp | Kreis Göppingen |
| de.k4systems.abfallhr | ALF Lahn-Fulda |
| de.k4systems.abfallappbh | Kreis Breisgau-Hochschwarzwald |
| de.k4systems.awgbassum | Kreis Diepholz |
| de.data_at_work.aws | Kreis Schaumburg |
| de.k4systems.hebhagen | Hagen |
| de.k4systems.meinawblm | Kreis Limburg-Weilburg |
| de.k4systems.abfallmsp | Landkreis Main-Spessart |
| de.k4systems.asoapp | Kreis Osterholz |
| de.k4systems.awistasta | Kreis Starnberg |
| de.ucom.abfallebe | Essen |
| de.k4systems.bawnapp | Kreis Nienburg / Weser |
| de.k4systems.abfallappol | Oldenburg |
| de.k4systems.awbrastatt | Kreis Rastatt |
| de.k4systems.abfallappmil | Kreis Miltenberg |
| de.k4systems.abfallsbk | Schwarzwald-Baar-Kreis |
| de.k4systems.wabapp | Westerwaldkreis |
| abfallMA.ucom.de | Mannheim |
| de.k4systems.llabfallapp | Kreis Landsberg am Lech |
| de.k4systems.lkruelzen | Kreis Uelzen |
| de.k4systems.abfallzak | Zollernalbkreis |
| de.k4systems.abfallappno | Neckar-Odenwald-Kreis |
| de.k4systems.udb | Burgenland (Landkreis) |
| de.k4systems.abfallappsig | Kreis Sigmaringen |
| de.k4systems.asf | Freiburg im Breisgau |
| de.drekopf.abfallplaner | Drekopf |
| de.k4systems.unterallgaeu | Rottweil, Tuttlingen, Waldshut, Frankfurt (Oder), Prignitz |
| de.k4systems.landshutlk | Kreis Landshut |
| de.k4systems.zakb | Kreis Bergstraße |
| de.k4systems.awrplus | Kreis Rotenburg (Wümme) |
| de.k4systems.lkmabfallplus | München Landkreis |
| de.k4systems.athosmobil | ATHOS GmbH |
| de.k4systems.willkommen |  |
| de.idcontor.abfalllu | Ludwigshafen |
<!--End of service section-->

## Note

Not all apps are extensively tested and some apps may have not edge cases taken into account. If you encounter any Errors feel free to open a new issue here: <https://github.com/mampfes/hacs_waste_collection_schedule/issues>
