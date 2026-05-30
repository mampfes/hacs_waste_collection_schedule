# Kungsbacka kommun

Support for schedules provided by [Kungsbacka kommun](https://sjalvservice.kungsbacka.se/), serving the municipality of Kungsbacka, Sweden.

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
*(string) (required)* : Street name and house number. Swedish characters (ä, å, ö) are supported.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: kungsbacka_se
      args:
        street_address: "Särö Lundaväg 14"
```

## How to get the source argument

Enter the street name and house number as you would on the [Kungsbacka self-service portal](https://sjalvservice.kungsbacka.se/oversikt/flow/4587). You can include the neighbourhood name for more precise matching, e.g. `"Särö Lundaväg 14"` instead of just `"Lundaväg 14"`.
