# Cheltenham Borough Council

Support for schedules provided by [Cheltenham Borough Council](https://www.cheltenham.gov.uk), serving Cheltenham, Gloucestershire, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: cheltenham_gov_uk
      args:
        property_id: PROPERTY_ID
```

### Configuration Variables

**property_id**
*(integer) (required)*

The internal numeric property identifier used by Cheltenham Borough Council's waste collection system. See below for how to find yours.

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: cheltenham_gov_uk
      args:
        property_id: 56299
```

## How to get the source argument

1. Visit <https://cheltenham-host01.oncreate.app/w/webpage/collection-lookup>
2. Enter your postcode and select your address from the dropdown.
3. Once your bin schedule loads, note the numeric **property ID** — it will be visible in the address selection form. Typical values are 5-digit numbers (e.g. `56299`).

Alternatively, open your browser's developer tools (F12 → Network tab), enter your postcode, select your address, and look for a POST request. The property ID is the numeric value submitted in the form payload.
