# Stockholm Vatten och Avfall

Support for schedules provided by [Stockholm Vatten och Avfall](https://www.stockholmvattenochavfall.se).

Source for Stockholm Vatten och Avfall (SVOA), house and townhouse waste collection in Stockholm.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: stockholmvattenochavfall_se
      args:
        street: STREET
        address: ADDRESS
```

### Configuration Variables

**street**  
*(string) (optional)*

**address**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: stockholmvattenochavfall_se
      args:
        address: "Hjortronv\xE4gen 3, Bromma"
```

## How to get the source arguments

In the UI, type the street name and then pick your address from the list. Enter the address of a house or townhouse (villa och radhus) as on https://www.stockholmvattenochavfall.se/villa-och-radhus/avfallstjanster/nar-kommer-sopbilen/, e.g. `Hjortronvägen 3, Bromma`. The postcode is optional. The website only shows the next collection of each bin, so the schedule is refreshed once a day (the default fetch interval).
