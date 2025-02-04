# PreZero Bad Oeynhausen

Add support for schedules provided by [PreZero Bad Oeynhausen](https://abfallkalender.prezero.network/bad-oeynhausen).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: prezero_bad_oeynhausen
      args:
        street: "Eidingsen"
        houseNo: "2"
```

### Configuration Variables

**street**
*(string) (required)*

**houseNo**
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: prezero_bad_oeynhausen
      args:
        street: "Eidingsen"
```

## How to get the source arguments

Just add your Street Name and House Number and add your iCal.
