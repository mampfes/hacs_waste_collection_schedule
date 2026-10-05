# Kungsbacka kommun

Support for schedules provided by [Kungsbacka kommun](https://sjalvservice.kungsbacka.se/).

Source for Kungsbacka kommun waste collection, Sweden.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: kungsbacka_se
      args:
        street_address: STREET_ADDRESS
```

### Configuration Variables

**street_address**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: kungsbacka_se
      args:
        street_address: Storgatan 1 Kungsbacka
```

## How to get the source arguments

Enter the street name and house number as shown on the [Kungsbacka self-service portal](https://sjalvservice.kungsbacka.se/oversikt/flow/4587), e.g. `Lundaväg 14` or `Lundaväg 14 Särö`. Swedish characters (ä, å, ö) are supported.
