# Cardinia Shire Council

Waste collection schedules provided by [Cardinia Shire Council](https://www.cardinia.vic.gov.au/).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: cardinia_vic_gov_au
      args:
        address: ADDRESS # FORMATTING MUST BE EXACT, PLEASE SEE BELOW
```

### Configuration Variables

**address**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: cardinia_vic_gov_au
      args:
        address: 6-8 Main St, Nar Nar Goon Vic
```

## How to get the correct address

Search your address on [Cardinia Shire Council's Website](https://www.cardinia.vic.gov.au/info/20002/rubbish_and_recycling/385/bin_collection_days_and_putting_your_bins_out/2#check) to ensure you use the correct address format. Start typing the full address and the use autocomplete to search. After results have been found, copy the address exactly as it appears in the search box.