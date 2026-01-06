# AbfallNavi.de

Support for schedules provided by [Abfallnavi.de](https://www.abfallnavi.de). The service is hosted under [regioit.de](https://regioit.de).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: abfallnavi_de
      args:
        service: SERVICE
        ort: SERVICE
        strasse: STRASSE
        hausnummer: hausnummer
```

### Configuration Variables

**service**  
*(string) (required)*

**ort**  
*(string) (required)*

**strasse**  
*(string) (optional)*  
*required if the service provider website requests it*

**hausnummer**  
*(string | Integer) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: abfallnavi_de
      args:
        service: coe
        ort: Coesfeld
        strasse: Ahornweg
```

## How to get the source arguments

Your serviceID can be found in the list below. `ort`, `strasse` and `hausnummer` (only supply if needed) should match the values of the serviceproviders search form.

<!--Begin of service section-->
|Region|service|
|-|-|
| Stadt Aachen | aachen |
| Abfallwirtschaft Stadt Nürnberg | nuernberg |
| Abfallwirtschaftsbetrieb Bergisch Gladbach | aw-bgl2 |
| AWA Entsorgungs GmbH | zew2 |
| AWG Kreis Warendorf | krwaf |
| Bergischer Abfallwirtschaftverbund | bav |
| Kreis Coesfeld | coe |
| Stadt Cottbus | cottbus |
| Dinslaken | din |
| Stadt Dorsten | dorsten |
| EGW Westmünsterland | wml2 |
| Gütersloh (Stadt) | gt2 |
| Kreis Gütersloh GEG | krwaf |
| Halver | hlv |
| Kreis Heinsberg | krhs |
| Kronberg im Taunus | kronberg |
| MHEG Mülheim an der Ruhr | muelheim |
| Stadt Norderstedt | nds |
| Kreis Pinneberg | pi |
| Gemeinde Roetgen | roe |
| Stadt Solingen | solingen |
| STL Lüdenscheid | stl |
| GWA - Kreis Unna mbH | unna |
| Kreis Viersen | viersen |
| WBO Wirtschaftsbetriebe Oberhausen | oberhausen |
| ZEW Zweckverband Entsorgungsregion West | zew2 |
| Stadt Cuxhaven | cux |
| Stadt Frankenthal | frankenthal |
| Abfallwirtschaftsverband Lippe | awvlippe |
| Gemeinde Kranenburg | kranenburg |
<!--End of service section-->



### Using the wizard

There is a script with an interactive command line interface which generates the required source configuration:

[https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/custom_components/waste_collection_schedule/waste_collection_schedule/wizard/abfallnavi_de.py](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/custom_components/waste_collection_schedule/waste_collection_schedule/wizard/abfallnavi_de.py).

First, install the Python module `inquirer`. Then run this script from a shell and answer the questions.
