# Odense Renovation

Support for schedules provided by [Odense Renovation](https://odenserenovation.dk/), serving Odense, Denmark.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: odenserenovation_dk
      args:
        addressNo: Address number
```

### Configuration Variables

**addressNo**
_(int) (required)_

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: odenserenovation_dk
      args:
        addressNo: 133517
```

## How to get the addressNo

Go to the [Se tømningskalender](https://mit.odenserenovation.dk/hentkalender) page, enter your address.

In the URL (web page address) copy the number after `addressNo=`

`I.e.` [`https://mit.odenserenovation.dk/downloadkalender?addressNo=133517`](https://mit.odenserenovation.dk/downloadkalender?addressNo=133517)

Then it's the `133517` part used in the integration
