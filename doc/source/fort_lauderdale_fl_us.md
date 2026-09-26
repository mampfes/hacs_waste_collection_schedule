# Fort Lauderdale, FL

Support for schedules provided by [Fort Lauderdale, FL](https://www.fortlauderdale.gov/government/departments-i-z/public-works/operations/sanitation-operations/collection-programs).

Source for City of Fort Lauderdale, FL trash, recycling, bulk trash and yard waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: fort_lauderdale_fl_us
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
    - name: fort_lauderdale_fl_us
      args:
        address: 413 NW 15th Ave, Fort Lauderdale, FL 33311
```

## How to get the source arguments

Enter your full street address including city, state and ZIP code (e.g. '413 NW 15th Ave, Fort Lauderdale, FL 33311'). It is matched against the city's 'My Government Services' collection zones (https://gis.fortlauderdale.gov/MyGovernmentServices/). Holiday shifts are not reflected.
