# Stadt Kerpen

Support for schedules provided by [Stadt Kerpen](https://www.stadt-kerpen.de).

Source for waste collection services in Kerpen.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: stadt_kerpen_de
      args:
        f_id_strasse: F_ID_STRASSE
        f_id_strasse_hnr: F_ID_STRASSE_HNR
        f_abfallarten: F_ABFALLARTEN
```

### Configuration Variables

**f_id_strasse**  
*(string) (optional)*

**f_id_strasse_hnr**  
*(string) (optional)*

**f_abfallarten**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: stadt_kerpen_de
      args:
        f_id_strasse: 3703amselweg
        f_id_strasse_hnr: '19409'
```

## How to get the source arguments

Open the MüllALARM web app at https://www.schoenmackers.de/kommunen/muellalarm-app/, choose Kerpen, then enter your street and house number with the browser's network tab open. The form data of the requests to api.abfall.io carries the f_id_strasse and f_id_strasse_hnr values. The kommune id is already set to Kerpen.
