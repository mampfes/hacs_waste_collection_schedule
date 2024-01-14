# West Suffolk Council

Support for schedules provided by [West Suffolk Council](https://westsuffolk.gov.uk/), serving West Suffolk Council, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: westsuffolk_gov_uk
      args:
        uprn: "UPRN"
        
```

### Configuration Variables

**uprn**  
*(String | Integer) (required)*


## Example

```yaml
waste_collection_schedule:
    sources:
    - name: westsuffolk_gov_uk
      args:
        uprn: "10090739388"
        
```

## How to get the source argument

### Easy method using findmyaddress.co.uk

An easy way to discover your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering in your address details.

### Harder method using browser developer tools

1. Go to <https://maps.westsuffolk.gov.uk/MyWestSuffolk.aspx>
2. Open your browser's developer tools (usually F12)
3. Click on the "Network" tab
4. Enter your address details and click on the address you want
5. You should see a request like <https://maps.westsuffolk.gov.uk/MyWestSuffolk.aspx?action=SetAddress&UniqueId=10090739388>
6. The number at the end of the URL is your UPRN
