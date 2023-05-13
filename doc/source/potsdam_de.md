# Potsdam

Support for schedules provided by [Potsdam](https://www.potsdam.de), serving Potsdam, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: potsdam_de
      args:
        ortsteil: ORTSTEIL
        strasse: STRAßE
        rest_rhythm: RHYTMUS Restabfall
        papier_rhythm: RHYTMUS Altpapier
        bio_rhythm: RHYTMUS Bioabfall
        gelb_rhythm: RHYTMUS Leichtverpackungen
        
```

### Configuration Variables

**ortsteil**  
*(String) (required)*

**strasse**  
*(String) (required)*

**rest_rhythm**  
(Integer) (optional)*
Rhythm for `Restabfall`

**papier_rhythm**  
(Integer) (optional)*
Rhythm for `Altpapier`

**bio_rhythm**  
(Integer) (optional)*  
Rhythm for `Bioabfall`

**gelb_rhythm**  
(Integer) (optional)*  
Rhythm for `Leichtverpackungen`. Defaults to 3 probably does not need to change

rhythm parameters must be selected like on the Potsdam website as follows:
|Rhythm|Value|
|-|-|
|kein ...|0|
|2x pro Woche|1|
|Wöchentlich|2|
|14-taglich|3|
|4-wöchentlich|4|
|Kombileerung|5|

## Examples

```yaml
waste_collection_schedule:
    sources:
    - name: potsdam_de
      args:
        ortsteil: Teltower Vorstadt
        strasse: Albert-Einstein-Str.
        rest_rhythm: 1
        papier_rhythm: 3
        bio_rhythm: 5
```

```yaml
waste_collection_schedule:
    sources:
    - name: potsdam_de
      args:
        ortsteil: Uetz
        strasse: Kanalweg
        rest_rhythm: 4
        papier_rhythm: 4
        bio_rhythm: 2
```

## How to get the source argument

Find the parameter of your address using [https://www.potsdam.de/abfallkalender-fuer-potsdam](https://www.potsdam.de/abfallkalender-fuer-potsdam) and write them exactly like on the web page.

Set the rhythm parameters like you would on the webpage (see list above for rhythm - value mapping).
