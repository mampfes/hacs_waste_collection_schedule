# Shawinigan

Support for schedules provided by [Shawinigan](https://geoweb.shawinigan.ca/CollecteMatieresResiduelles/).

Source for Shawinigan, Canada waste collection schedule.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: shawinigan_ca
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
    - name: shawinigan_ca
      args:
        address: 1760 Avenue de la Paix, Shawinigan, QC G9N 6H7
```

## How to get the source arguments

Enter your street address including city and postal code (e.g. '1760 Avenue de la Paix, Shawinigan, QC G9N 6H7').
