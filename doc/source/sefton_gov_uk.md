# Sefton Council

Support for schedules provided by [Sefton Council](https://www.sefton.gov.uk/).

Source for Sefton Council, UK

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: sefton_gov_uk
      args:
        postcode: POSTCODE
        streetname: STREETNAME
        house_number_or_name: HOUSE_NUMBER_OR_NAME
```

### Configuration Variables

**postcode**  
*(string) (required)*

**streetname**  
*(string) (required)*

**house_number_or_name**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: sefton_gov_uk
      args:
        house_number_or_name: '1'
        streetname: Ken Mews
        postcode: L20 6GF
```

## How to get the source arguments

Using a browser, go to [sefton.gov.uk](https://www.sefton.gov.uk/bins-and-recycling/bins-and-recycling/when-is-my-bin-collection-day/). For _Postcode_ and _Street name_ use the values you'd enter on Sefton's first page. Search, and then for _House Name or Number_ you need the value that comes before the street name you entered on the first screen. e.g. if your streetname is 'Liverpool Road' and the select box has an option of '1A Liverpool Road' enter '1A' as your _House Name or Number_.
