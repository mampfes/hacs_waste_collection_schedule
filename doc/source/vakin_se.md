# Vakin

Waste collection schedule for Vakin (serving Umeå, Nordmaling, and Vindeln municipalities in Sweden).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: vakin_se
      args:
        address: "Kajakvägen 3, Täfteå"
```

### Configuration Variables

**address**  
*(string) (required)*  
Street address with house number (e.g. `Kajakvägen 3` or `Kajakvägen 3, Täfteå`).

**city**  
*(string) (optional)*  
City or municipality name (e.g. `Täfteå`, `Umeå`, `Nordmaling`), helpful if there are multiple matches.

## How to get the source arguments

Go to the [Vakin schedule page](https://www.vakin.se/kundserviceochetjanster/sophamtning/narkommersopbilen.4.6252338c1a0c6bd088ed01f.html) and search for your street address. Use the matching address string as the `address` parameter.

