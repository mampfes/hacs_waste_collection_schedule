# Auckland Council

Support for schedules provided by [Auckland Council](https://new.aucklandcouncil.govt.nz/).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: aucklandcouncil_govt_nz
      args:
        area_number: AREA_NUMBER_FROM_COLLECTION_PAGE # see 'How to get the source argument below'
```

### Configuration Variables

**area_number**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: aucklandcouncil_govt_nz
      args:
        area_number: 12342306525
```

## How to get the source argument

The source argument is the area number from Auckland Council site:

- Open your collection days page by  entering your address [on the Auckland Council collection day finder](https://new.aucklandcouncil.govt.nz/en/rubbish-recycling/rubbish-recycling-collections/rubbish-recycling-collection-days.html)
- Once an address is selected, you will see a line such as: `Assessment number: 12342306525`
- In this example the area number is `12342306525`.
