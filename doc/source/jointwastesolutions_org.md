# Joint Waste Solutions

Support for schedules provided by [Joint Waste Solutions](https://www.jointwastesolutions.org/).

Manages Waste and Recycling services for Elmbridge, Mole Valley, Surrey Heath & Woking

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: jointwastesolutions_org
      args:
        house: HOUSE
        postcode: POSTCODE
        borough: BOROUGH
```

### Configuration Variables

**house**  
*(string) (required)*

**postcode**  
*(string) (required)*

**borough**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: jointwastesolutions_org
      args:
        house: '4'
        postcode: GU21 4PQ
```

## How to get the source arguments

Provide the house name or number and the postcode as shown on the council's bin-day lookup, and choose your borough: `woking` or `surreyheath`.
