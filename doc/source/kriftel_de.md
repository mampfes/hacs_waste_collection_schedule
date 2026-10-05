# Gemeinde Kriftel

Support for schedules provided by [Gemeinde Kriftel](https://www.kriftel.de).

Source for Gemeinde Kriftel, Hesse, Germany waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: kriftel_de
      args:
        district: DISTRICT
```

### Configuration Variables

**district**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: kriftel_de
      args:
        district: '1'
```

## How to get the source arguments

The Kriftel collection district your address belongs to: '1', '2' or '3'.
