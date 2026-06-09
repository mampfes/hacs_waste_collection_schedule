# Boston Borough Council

Support for schedules provided by [Boston Borough Council](https://www.boston.gov.uk/article/27449/Your-Waste-Collections), UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: boston_gov_uk
      args:
        postcode: PE20 3LW
        property: "43"
```

### Configuration Variables

**postcode**
*(string) (required)*

Your property postcode, e.g. `PE20 3LW`.

**property**
*(string) (required)*

Your property name or number, e.g. `43`.

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: boston_gov_uk
      args:
        postcode: PE20 3LW
        property: "43"
```

## How to get the source arguments

Visit the [Boston Borough Council waste collections page](https://www.boston.gov.uk/article/27449/Your-Waste-Collections), enter your postcode and property name or number, and use the same values here.

Note: this source returns the next scheduled collection date per bin type. Home Assistant will refresh the data automatically to keep the dates current.
