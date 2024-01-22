# Wellington City Council

Support for schedules provided by [Hutt City Council](https://toogoodtowaste.co.nz/).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: toogoodtowaste_co_nz
      args:
        address: 30 Laings Road HUTT CENTRAL # see 'How to get the source argument below'
```

### Configuration Variables

**address**  
*(string)*

## How to get the source argument

The source argument is the address as is appears when searched on https://toogoodtowaste.co.nz:

- Search for you address on https://toogoodtowaste.co.nz
- Select your address from the dropdown
- Copy your address from the text box

The casing must match exactly.
