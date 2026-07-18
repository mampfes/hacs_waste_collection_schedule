# Gloucester City Council

Support for schedules provided by [Gloucester City Council](https://www.gloucester.gov.uk/), serving Gloucester, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: gloucester_gov_uk
      args:
        uprn: UNIQUE_PROPERTY_REFERENCE_NUMBER
```

### Configuration Variables

**uprn**<br>
*(string) (required)*

#### How to find your `UPRN`

Visit the [Gloucester bin collection checker](https://gloucester-self.achieveservice.com/en/service/Bins___Check_your_bin_day) and search for your address. Your UPRN will appear as part of the address lookup.

Alternatively, go to <https://www.findmyaddress.co.uk/> and enter your address details.

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: gloucester_gov_uk
      args:
        uprn: 200004478006
```

## How it works

Gloucester City Council's online bin-day checker is only able to reliably
display the next household waste (black bin) collection date on its own web
page — recycling, food and garden waste cards are affected by a known
display issue on the council's site ("Sorry, we're having technical issues
with our system."). This source queries the same underlying data feed used
by that page directly, so it is able to return the next collection date for
recycling, food and garden waste too, whenever that data is available for
your address.

Only the single next upcoming collection date is available per waste
stream (the council's system does not expose a full calendar of future
dates), so this source reports one upcoming entry per waste type each time
it is polled.
