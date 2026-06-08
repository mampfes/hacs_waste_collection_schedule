# Vatten och Miljöresurs

Support for schedules provided by [Vatten och Miljöresurs](https://www.vattenmiljoresurs.se), serving the municipalities of Bräcke, Berg, and Härjedalen in Jämtland, Sweden.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: vattenmiljoresurs_se
      args:
        municipality: MUNICIPALITY
        street_address: STREET_ADDRESS
```

### Configuration Variables

**municipality**
*(string) (required)*

The municipality slug. One of: `bracke`, `berg`, `harjedalen`.

**street_address**
*(string) (required)*

The street address as listed on the provider's website (street name and house number, e.g. `Hantverksgatan 25`). The address is matched case-insensitively.

## Examples

```yaml
waste_collection_schedule:
  sources:
    - name: vattenmiljoresurs_se
      args:
        municipality: bracke
        street_address: Hantverksgatan 25
```

```yaml
waste_collection_schedule:
  sources:
    - name: vattenmiljoresurs_se
      args:
        municipality: berg
        street_address: Balviken 550
```

```yaml
waste_collection_schedule:
  sources:
    - name: vattenmiljoresurs_se
      args:
        municipality: harjedalen
        street_address: Algatan 3
```

## How to get the source arguments

1. Visit the collection schedule page for your municipality:
   - **Bräcke**: https://www.vattenmiljoresurs.se/bracke/avfall-och-atervinning/avfallshamtning/nar-kommer-sopbilen
   - **Berg**: https://www.vattenmiljoresurs.se/berg/avfall-och-atervinning/avfallshamtning/nar-kommer-sopbilen
   - **Härjedalen**: https://www.vattenmiljoresurs.se/harjedalen/avfall-och-atervinning/avfallshamtning/nar-kommer-sopbilen
2. Search for your address using the address lookup tool on the page.
3. Use the displayed address (street name and number) as the `street_address` argument.

## Notes

- The source generates a rolling schedule for up to one year based on the collection frequency encoded in the provider's address database.
- Some addresses have multi-number entries (e.g. `169 -171`); the source handles range matching automatically.
- A small number of addresses in Härjedalen use non-standard frequency codes (`h4xx`, `bud`) that indicate special collection arrangements. These will return no scheduled dates — contact the provider directly for those addresses.
