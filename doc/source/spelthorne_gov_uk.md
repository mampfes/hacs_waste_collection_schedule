# Spelthorne Borough Council

Support for waste collection schedules from [Spelthorne Borough Council](https://www.spelthorne.gov.uk), Surrey, UK.

## Local Government Reorganisation note
During the ongoing local government reorganisation (LGR) in Surrey, please continue to use the source for your current area as long as it's still working. New sources for the new West Surrey Council are not expected to be live until at least April 2027, when the council itself officially comes into being.

## How to get your UPRN

Visit [https://spelthorne-self.achieveservice.com/service/Waste_Collections](https://spelthorne-self.achieveservice.com/service/Waste_Collections), enter your postcode and select your address. The UPRN is the numeric identifier associated with your property.

Alternatively, find your UPRN at [https://www.findmyaddress.co.uk/](https://www.findmyaddress.co.uk/).

## Configuration

```yaml
waste_collection_schedule:
  sources:
    - name: spelthorne_gov_uk
      args:
        uprn: "33042469"
```

### Arguments

| Argument | Description |
|----------|-------------|
| `uprn` | Unique Property Reference Number (UPRN) for your address |
