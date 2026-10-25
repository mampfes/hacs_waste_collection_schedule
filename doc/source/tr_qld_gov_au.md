# Toowoomba Regional Council

Support for schedules provided by [Toowoomba Regional Council](https://www.tr.qld.gov.au).

Source for Toowoomba Regional Council (QLD) kerbside collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: tr_qld_gov_au
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
    - name: tr_qld_gov_au
      args:
        address: 191 Herries Street
        suburb: Toowoomba City
```

## How to get the source arguments

Enter the street address with the street type written out (e.g. '191 Herries Street', units as '2/86C Hogg Street') and the suburb (e.g. 'Toowoomba City'), as the council's 'Find your bin day' map shows them. An address from the suggestion list may be pasted whole ('191 Herries Street, TOOWOOMBA CITY QLD 4350'). Green waste is an optional service: the dates are those of your area's green waste round, whether or not you have a green waste bin.
