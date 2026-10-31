# Newry, Mourne and Down District Council

Support for schedules provided by [Newry, Mourne and Down District Council](https://www.newrymournedown.org).

Source for Newry, Mourne and Down District Council bin calendars.

## Configuration via configuration.yaml

### Using postcode and house_number

```yaml
waste_collection_schedule:
  sources:
    - name: newrymournedown_org
      args:
        postcode: POSTCODE
        house_number: HOUSE_NUMBER
```

### Using url

```yaml
waste_collection_schedule:
  sources:
    - name: newrymournedown_org
      args:
        url: URL
```

### Configuration Variables

**postcode**  
*(string) (alternative)*

**house_number**  
*(string) (alternative)*

**url**  
*(string) (alternative)*

Provide one of: `postcode` + `house_number` or `url`.

## Example

### Using postcode and house_number

```yaml
waste_collection_schedule:
  sources:
    - name: newrymournedown_org
      args:
        postcode: BT35 7DN
        house_number: '9'
```

### Using url

```yaml
waste_collection_schedule:
  sources:
    - name: newrymournedown_org
      args:
        url: https://www.newrymournedown.org/bin-collections/WED-Z1.pdf?v=5
```

## How to get the source arguments

Either enter the postcode and house number shown by the council's lookup at https://www.newrymournedown.org/weekly-bin-collection-and-calendar. Or paste your council bin-collections PDF link into url instead. The direct PDF option works independently of the address portal, which can be temporarily unavailable. Dates, including holiday changes, come from the printed calendar. Black bins are general waste, blue bins recycling, and brown bins combined food/garden waste (Organic). Unnumbered properties and ambiguous house numbers are not supported by this address lookup.
