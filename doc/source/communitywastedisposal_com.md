# Community Waste Disposal (CWD)

Support for schedules provided by [Community Waste Disposal (CWD)](https://www.communitywastedisposal.com).

Source for Community Waste Disposal (CWD) in North Texas

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: communitywastedisposal_com
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
    - name: communitywastedisposal_com
      args:
        address: 100 Princeton Cir, Forney, TX 75126
```

## How to get the source arguments

Enter your street address including city and ZIP (e.g. '123 Main St, Allen, TX 75002').
