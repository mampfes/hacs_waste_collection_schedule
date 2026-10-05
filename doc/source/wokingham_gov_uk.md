# Wokingham Borough Council

Support for schedules provided by [Wokingham Borough Council](https://wokingham.gov.uk).

Source for wokingham.gov.uk services for Wokingham, UK.

## Configuration via configuration.yaml

### Using property

```yaml
waste_collection_schedule:
  sources:
    - name: wokingham_gov_uk
      args:
        postcode: POSTCODE
        property: PROPERTY
```

### Using address

```yaml
waste_collection_schedule:
  sources:
    - name: wokingham_gov_uk
      args:
        postcode: POSTCODE
        address: ADDRESS
```

### Configuration Variables

**postcode**  
*(string) (required)*

**property**  
*(string) (alternative)*

**address**  
*(string) (alternative)*

Provide one of: `property` or `address`.

## Example

### Using property

```yaml
waste_collection_schedule:
  sources:
    - name: wokingham_gov_uk
      args:
        postcode: RG40 1GE
        property: '10032935729'
```

### Using address

```yaml
waste_collection_schedule:
  sources:
    - name: wokingham_gov_uk
      args:
        postcode: RG40 2LW
        address: 16 Davy Close
```

## How to get the source arguments

Enter your postcode together with either the first line of your address (e.g. '16 Davy Close'; the first address on the council's list that contains it is used) or the property number, which is the UPRN. To find it, open https://www.wokingham.gov.uk/rubbish-and-recycling/waste-collection/find-your-bin-collection-day, look up your postcode and read the value of your address's <option> in the page source, e.g. 10032935729 for '32, SAMBORNE DRIVE, WOKINGHAM'.
