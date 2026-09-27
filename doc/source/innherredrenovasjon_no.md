# Innherred Renovasjon

Support for schedules provided by [Innherred Renovasjon](https://innherredrenovasjon.no/).

Source for innherredrenovasjon.no services for Innherred Renovasjon, Norway.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: innherredrenovasjon_no
      args:
        address: ADDRESS
```

### Configuration Variables

**address**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: innherredrenovasjon_no
      args:
        address: "Geving\xE5sen 206"
```
