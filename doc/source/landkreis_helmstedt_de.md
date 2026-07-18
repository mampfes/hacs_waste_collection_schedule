# Landkreis Helmstedt

Support for schedules provided by [Landkreis Helmstedt](landkreis-helmstedt.de).

Source for Landkreis Helmstedt.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: landkreis_helmstedt_de
      args:
        municipal: MUNICIPAL
        restabfall: RESTABFALL
        altpapier: ALTPAPIER
        gelber_sack: GELBER_SACK
        bioabfall: BIOABFALL
```

### Configuration Variables

**municipal**  
*(string) (required)*

**restabfall**  
*(string) (required)*

**altpapier**  
*(string) (required)*

**gelber_sack**  
*(string) (required)*

**bioabfall**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: landkreis_helmstedt_de
      args:
        municipal: Grasleben und Velpke
        restabfall: 1
        bioabfall: 1
        gelber_sack: 3
        altpapier: 5
```

## How to get the source arguments

Visit https://www.landkreis-helmstedt.de/portal/seiten/abfuhrkalender-900000002-34150.html and first get the name of the ICS calendar on the website for your municipal, then open the related PDF calendar and find the collection areas.
