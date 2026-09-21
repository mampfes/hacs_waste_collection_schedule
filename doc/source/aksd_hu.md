# AKSD Debrecen

Support for schedules provided by [A.K.S.D. Kft.](https://www.aksd.hu/hulladeknaptar), the waste management company of Debrecen, Hungary.

The provider only publishes the collection weekday per street (and "every odd week" for some bins), so the dates are generated from that weekly rule for the next year. Garden waste (brown bin and green bag) is only generated for March to December. Odd weeks are interpreted as odd ISO week numbers.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: aksd_hu
      args:
        street: STREET_NAME
```

### Configuration Variables

**street**
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: aksd_hu
      args:
        street: Kinizsi utca
```

## How to get the source arguments

Enter the street name exactly as it appears in the street search at <https://www.aksd.hu/hulladeknaptar> (e.g. `Kinizsi utca`). Upper/lower case and accents are ignored.
