# Torbay Council

Support for schedules provided by [Torbay Council](https://www.torbay.gov.uk).

Source for waste collection services for Torbay Council, Devon, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: torbay_council_gov_uk
      args:
        uprn: UPRN
```

### Configuration Variables

**uprn**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: torbay_council_gov_uk
      args:
        uprn: '100040542066'
```

## How to get the source arguments

Your Unique Property Reference Number (UPRN). Find yours at https://www.findmyaddress.co.uk/.
