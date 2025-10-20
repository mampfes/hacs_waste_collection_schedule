# Greyhound Recycling

Support for schedules provided by [Greyhound Recycling](https://greyhound.ie/), serving the Greater Dublin area, Ireland.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: greyhound_ie
      args:
        account_number: ACCOUNT_NUMBER
        pin: PIN

```

### Configuration Variables

**account_number**
*(String | Integer) (required)*

**pin**
*(String | Integer) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: greyhound_ie
      args:
        account_number: 1234567
        pin: 1234

```

## How to get the account_number and pin

These details are provided by Greyhound Recycling when signing up to the service. (they are the same details used for the app login in.)