# Latrobe City Council

Support for schedules provided by [Latrobe City Council](https://www.latrobe.vic.gov.au).

Source for Latrobe City Council (VIC) kerbside collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: latrobe_vic_gov_au
      args:
        address: ADDRESS
        suburb: SUBURB
```

### Configuration Variables

**address**  
*(string) (required)*

**suburb**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: latrobe_vic_gov_au
      args:
        address: 23-25 Ann Street
        suburb: Morwell
```

## How to get the source arguments

Enter the property address as on your rates notice, with the street type written out (e.g. 23-25 Ann Street), and the suburb (e.g. Morwell). The collection day and area (A or B) come from the council's property records and the dates from the council's recycling and green waste calendar PDF. The council's website only answers from Australian internet connections, so the source does not work through a VPN or proxy outside Australia.
