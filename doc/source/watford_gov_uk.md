# Watford Borough Council

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: watford_gov_uk
      args:
        uprn: "100080945713"
```

### Configuration Variables

**uprn** *(string, required unless `address` is provided; recommended)*

Property UPRN / selected address token from the Watford bin collections form.

**address** *(string, optional)*

Explicit address token from the Watford form. In practice this appears to match the UPRN for working addresses.

## Notes

Watford's public postcode-to-address lookup appears unreliable when called directly, so this source currently works best when you provide the UPRN / selected address value from the Watford form.

The `uprn` argument is the recommended option and, in working cases, matches the selected address value used internally by the Watford form.

Some Watford property tokens may not currently return collection HTML from the council backend. In those cases the source should fail cleanly instead of returning misleading empty data.

## How to get the argument

1. Open the Watford bin collections page.
2. Enter your postcode.
3. Select your address.
4. In browser developer tools, inspect the `runLookup` request payload.
5. Use the value from `formValues.Address.address.value` (this is typically also the UPRN used by this source).

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: watford_gov_uk
      args:
        uprn: "100080945713"
```
