# Min Renovasjon

Support for schedules provided by [Min Renovasjon](https://www.norkart.no).

Source for Norkart Komtek MinRenovasjon (Norway).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: minrenovasjon_no
      args:
        street_name: STREET_NAME
        house_number: HOUSE_NUMBER
        street_code: STREET_CODE
        county_id: COUNTY_ID
```

### Configuration Variables

**street_name**  
*(string) (required)*

**house_number**  
*(string) (required)*

**street_code**  
*(string) (required)*

**county_id**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: minrenovasjon_no
      args:
        street_name: "R\xE5dhustorget"
        house_number: 2
        street_code: 2469
        county_id: 3024
```

## How to get the source arguments

Look up your address with the Kartverket address API, for example https://ws.geonorge.no/adresser/v1/sok?sok=Min%20Gate%2012. `street_code` is the result's `adressekode` and `county_id` its `kommunenummer`.
