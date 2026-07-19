# Stadt Kerpen

Support for schedules provided by [Stadt Kerpen](https://www.stadt-kerpen.de/).

The service provider for Kerpen is Schönmackers. This source leverages the [abfall.io](https://abfall.io) API internally, which natively supports Kerpen.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: stadt_kerpen_de
      args:
        f_id_strasse: STRASSE
        f_id_strasse_hnr: HAUSNUMMER
        f_abfallarten:
          - 1
          - 2
```

### Configuration Variables

**f_id_strasse**  
*(string) (required)*

The internal ID of your street. 

**f_id_strasse_hnr**  
*(string) (optional)*

The internal ID of your house number. 

**f_abfallarten**  
*(list of integers) (optional)*

List of internal IDs for specific waste types. Leave empty to retrieve all types.

## How to get the source arguments

1. Go to the [MüllALARM](https://www.schoenmackers.de/kommunen/muellalarm-app/) web app.
2. Select **Kerpen** as your city.
3. Open the Developer Tools of your browser (F12) and switch to the **Network** tab.
4. Proceed to enter your street and house number.
5. Watch the network requests for `api.abfall.io` and check the `Form Data` of the requests to find the values for `f_id_strasse` and `f_id_strasse_hnr`.

Alternatively, you can use the interactive script `abfall_io.py` provided in the `wizard` directory of this repository to fetch the internal IDs. Use the service map ID for Schönmackers.
