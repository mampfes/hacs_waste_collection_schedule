# SRV Återvinning

Support for schedules provided by [SRV återvinning AB](https://www.srvatervinning.se/), Sweden.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: srvatervinning_se
      args:
        address: ADDRESS
        city: CITY
```

### Configuration Variables

**address**  
*(string) (required)*

**city**  
*(string)*

## Examples

```yaml
waste_collection_schedule:
  sources:
    - name: srvatervinning_se
      args:
        address: "Skansvägen"

```

```yaml
waste_collection_schedule:
  sources:
    - name: srvatervinning_se
      args:
        address: "Skolvägen"
        city: "TUNGELSTA"

```

## How to get the source arguments

1. Go to your calendar at [SRV återvinning AB](https://www.srvatervinning.se/avfallshamtning/nar-hamtar-vi-ditt-avfall)
2. Enter your street address. Do not include postal code or city.
3. Include city as an argument if there are multiple search results.

### Configuration values
#### source -> customization -> type
##### Vanlig
- "Matavfall"
- "Restavfall"
##### Sortera hemma
- "Kärl 370 liter fyrfack kärl 1"
- "Kärl 370 liter fyrfack kärl 2"
