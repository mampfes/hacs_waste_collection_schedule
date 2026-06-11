# Basingstoke and Deane Borough Council

Support for schedules provided by [Basingstoke and Deane Borough Council](https://www.basingstoke.gov.uk/bincollections), Hampshire, UK.

## Local Government Reorganisation note
During the ongoing local government reorganisation (LGR) in Hampshire, please continue to use the source for your current area as long as it's still working. New sources for the new North Hampshire Council are not expected to be live until at least April 2028, when the council itself officially comes into being.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: basingstoke_gov_uk
      args:
        uprn: UPRN_CODE
```

### Configuration Variables

**uprn**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: basingstoke_gov_uk
      args:
        uprn: "100060218986"
```

## How to get the source argument

An easy way to discover your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering in your address details.