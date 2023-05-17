# Welwyn Hatfield Borough Council

Support for schedules provided by [Welwyn Hatfield Borough Council](https://www.welhat.gov.uk/xfp/form/214), serving the
Welwyn and Hatfield council area.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: welhat_gov_uk
      args:
        uprn: UPRN
        postcode: POSTCODE
      customize:
        - type: recycling
        - type: refuse
        - type: food
        - type: garden
```

### Configuration Variables

**uprn**  
*(string) (required)*

**postcode**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: welhat_gov_uk
      args:
        uprn: "100080965745"
        postcode: "AL9 5EA"
      customize:
        - type: recycling
        - type: refuse
        - type: food
        - type: garden
```

## How to get the uprn argument above

The UPRN code can be found by entering your postcode or address on
[Find My Address
](https://www.findmyaddress.co.uk/search) and selecting your address from the available list. The UPRN is then shown in yellow text on the address marker.

## Important Note
Due to limitations with the WelHat website, only the next collection for each bin can be retrieved. I have lodged a request for full API access with the council, so if there is a way to retrieve additional information in future I will update this.