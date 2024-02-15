# Tunbridge Wells

Support for schedules provided by [Tunbridge Wells](https://tunbridgewells.gov.uk/), serving Tunbridge Wells, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: tunbridgewells_gov_uk
      args:
        uprn: UPRN
        
```

### Configuration Variables

**uprn**  
*(String | Integer) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: tunbridgewells_gov_uk
      args:
        uprn: 10090058289
        
```

## How to get the source argument

## Using the browser developer tools

- Go to the [Tunbridge Wells - check-your-bin-collection-day](https://tunbridgewells.gov.uk/bins-and-recycling/check-your-bin-collection-day) page and enter postcode or street and click on the "Find address" button.
- Right-click -> inspect on the address dropdown menu
- Expand the select tag and look for the option tag with your address. The value attribute of the option tag is your UPRN.

## Using findmyaddress.co.uk

An easy way to discover your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering in your address details.
