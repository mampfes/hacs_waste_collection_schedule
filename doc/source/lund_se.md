# Lund Waste Collection

Support for schedules provided by [Lund Waste Collection](https://eservice431601.lund.se).

Source for Lund waste collection services, Sweden.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: lund_se
      args:
        street_address: STREET_ADDRESS
```

### Configuration Variables

**street_address**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: lund_se
      args:
        street_address: "Lokf\xF6raregatan 7, LUND (19120)"
```

## How to get the source arguments

Enter your street address as the provider's own address search lists it; the building id in brackets, e.g. 'Lokföraregatan 7, LUND (19120)', skips the search.
