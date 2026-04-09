# SUM Avfall (Sunnfjord og Ytre Sogn Miljøverk IKS)

Support for schedules provided by [SUM Avfall](https://www.sumavfall.no/), serving municipalities in Sunnfjord and Ytre Sogn, Norway (including Førde, Naustdal, Gaular, Jølster, and surrounding areas).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: sumavfall_no
      args:
        address: ADDRESS_SLUG
```

### Configuration Variables

**address**
*(String) (required)*

The address slug as it appears in the URL on sumavfall.no, e.g. `blåbærlia-16` or `storgata-1`.

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: sumavfall_no
      args:
        address: blåbærlia-16
```

## How to get the source argument

1. Go to [https://www.sumavfall.no/tommekalender](https://www.sumavfall.no/tommekalender)
2. Type your address in the search field and select it from the suggestions
3. The page will redirect to a URL like `https://www.sumavfall.no/tommekalender?adresse=blåbærlia-16`
4. Use the value after `?adresse=` as your `address` argument

## Waste types

The following waste types are returned (merged from the website's raw categories):

| Type | Description |
|------|-------------|
| `Matavfall` | Food waste |
| `Restavfall` | Residual waste |
| `Papp og plast` | Cardboard, paper and plastic packaging |
| `Glass og metall` | Glass and metal packaging |
