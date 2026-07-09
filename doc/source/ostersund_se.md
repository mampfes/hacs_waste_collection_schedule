# Östersunds kommun

Support for the household waste collection schedule provided by [Östersunds kommun](https://www.ostersund.se/) for single-family homes in Östersund municipality, Sweden. Data is fetched from the address search widget on the "När kommer sopbilen?" (When does the garbage truck come?) page. Apartment buildings and businesses are not listed by this service.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: ostersund_se
      args:
        address: ADDRESS
```

### Configuration Variables

**address**
*(String) (required)* — Street address including house number, exactly as it appears on ostersund.se, e.g. `Återgången 1`.

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: ostersund_se
      args:
        address: Återgången 1
```

## How to get the source arguments

Go to the [collection search on ostersund.se](https://www.ostersund.se/bygga-bo-klimat-och-miljo/avfall-och-atervinning/nar-kommer-sopbilen.html), search for your address and copy the street name and house number exactly as shown in the results list, e.g. `Återgången 1`. Only single-family homes in Östersund kommun are covered; apartment buildings and businesses are not listed.

## Notes

The website only exposes the next collection date per address. Household waste (residual and food waste) is collected together every 14 days ("Sopbilen hämtar ditt avfall var fjortonde dag"), so this source extrapolates future collections at a fixed 14-day interval from the next confirmed pickup date. Collection times may shift around major holidays; such shifts are not reflected by this extrapolation.
