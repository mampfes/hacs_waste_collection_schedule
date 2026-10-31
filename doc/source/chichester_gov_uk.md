# Chichester District Council

Support for schedules provided by [Chichester District Council](https://www.chichester.gov.uk).

Source for chichester.gov.uk services for Chichester

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: chichester_gov_uk
      args:
        uprn: UPRN
```

### Configuration Variables

**uprn**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: chichester_gov_uk
      args:
        uprn: 010002476348
```

## How to get the source arguments

Open https://www.chichester.gov.uk/checkyourbinday, search your address, and copy the UPRN.
