# AWB Birkenfeld

Support for schedules provided by [AWB Birkenfeld](https://www.awb-bir.de).

Source for AWB Birkenfeld (Abfallwirtschaftsbetrieb Landkreis Birkenfeld), Germany

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: awb_bir_de
      args:
        street: STREET
        city: CITY
```

### Configuration Variables

**street**  
*(string) (required)*

**city**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: awb_bir_de
      args:
        street: "Auf dem Scho\xDF"
        city: Reichenbach
```

## How to get the source arguments

Visit the AWB Birkenfeld waste calendar page <https://www.awb-bir.de/Service/(0)Abfuhrkalender/> and search for your street. Use the exact street name (and, if it occurs in more than one village, the Ortsgemeinde) as shown in the search results.
