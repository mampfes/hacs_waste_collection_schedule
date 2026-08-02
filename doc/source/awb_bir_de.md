# AWB Birkenfeld

Support for schedules provided by [awb-bir.de](https://www.awb-bir.de), the waste management authority (AWB) of Landkreis Birkenfeld, Rhineland-Palatinate, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: awb_bir_de
      args:
        street: Auf dem Schoß
        city: Reichenbach
```

### Configuration Variables

**street**  
*(string) (required)*

**city**  
*(string) (optional)*

Only required if the street name occurs in more than one Ortsgemeinde (village/town) within the Landkreis.

## How to get the source arguments

Visit the [Abfuhrkalender](https://www.awb-bir.de/Service/(0)Abfuhrkalender/) page and search for your street. Use the street name (and, if it occurs in more than one village, the Ortsgemeinde) exactly as shown in the search results.
