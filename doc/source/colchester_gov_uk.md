# Colchester City Council

Support for schedules provided by [Colchester City Council](https://colchester.gov.uk).

Source for Colchester.gov.uk services for the borough of Colchester, UK.

## Configuration via configuration.yaml

### Using llpgid

```yaml
waste_collection_schedule:
  sources:
    - name: colchester_gov_uk
      args:
        llpgid: LLPGID
```

### Using postcode and house

```yaml
waste_collection_schedule:
  sources:
    - name: colchester_gov_uk
      args:
        postcode: POSTCODE
        house: HOUSE
```

### Configuration Variables

**llpgid**  
*(string) (alternative)*

**postcode**  
*(string) (alternative)*

**house**  
*(string) (alternative)*

Provide one of: `llpgid` or `postcode` + `house`.

## Example

### Using llpgid

```yaml
waste_collection_schedule:
  sources:
    - name: colchester_gov_uk
      args:
        llpgid: 30213e07-6027-e711-80fa-5065f38b56d1
```

### Using postcode and house

```yaml
waste_collection_schedule:
  sources:
    - name: colchester_gov_uk
      args:
        postcode: CO5 8NT
        house: '16'
```

## How to get the source arguments

Enter your UK postcode and the house number or name as it appears in the address picker of the [Colchester recycling calendar](https://www.colchester.gov.uk/your-recycling-calendar/). Advanced users may instead supply 'llpgid' (the GUID in the calendar URL after selecting an address).
