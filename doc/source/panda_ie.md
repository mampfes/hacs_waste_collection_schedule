# Panda Waste

Support for schedules provided by [Panda Waste](https://www.panda.ie), serving Ireland.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: panda_ie
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
    - name: panda_ie
      args:
        account_number: 1234567
        pin: 1234

```

## How to get the account_number and pin

These details are provided by Panda when subscribing to the service.
They are the same details used in the access for the mobile app.