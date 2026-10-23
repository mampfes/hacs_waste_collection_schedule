# Publidata (Canada) generic source

Support for schedules provided by [Publidata (Canada) generic source](https://www.publidata.ca).

Publidata is a Canadian public operator. Check if your area is concerned on their website.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: publidata_ca
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
    - name: publidata_ca
      args:
        address: "1580 Chem. du Fer-\xE0-Cheval, Sainte-Julie, QC J3E 0A2"
```

## How to get the source arguments

Enter your full address, e.g. `1580 Chem. du Fer-à-Cheval, Sainte-Julie, QC J3E 0A2`.
