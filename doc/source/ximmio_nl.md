# Ximmio

Support for schedules provided by [Ximmio.nl](https://www.ximmio.nl/).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: ximmio_nl
      args:
        company: COMPANY
        post_code: POST_CODE
        house_number: HOUSE_NUMBER
```

### Configuration Variables

**company**<br>
*(string) (required)*

Use one of the following codes as company code:

- acv
- almere
- areareiniging
- avalex
- avri
- bar
- hellendoorn
- meerlanden
- meppel
- rad
- reinis
- twentemilieu
- waardlanden
- westland
- ximmio

**post_code**<br>
*(string) (required)*

**house_number**<br>
*(integer) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: ximmio_nl
      args:
        company: acv
        post_code: 6721MH
        house_number: 1
```
