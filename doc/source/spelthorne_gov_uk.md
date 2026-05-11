# Spelthorne Borough Council

Support for waste collection schedules from [Spelthorne Borough Council](https://www.spelthorne.gov.uk), Surrey, UK.

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
