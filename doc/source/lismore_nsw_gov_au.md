# Lismore City Council (NSW)

Support for schedules provided by [Lismore City Council](https://www.lismore.nsw.gov.au/Households/Waste-and-recycling/Whats-My-Bin-Day1).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: lismore_nsw_gov_au
      args:
        address: YOUR_FULL_ADDRESS
```

### Configuration Variables

**address**
*(string) (required)*

Your full street address including suburb, state and postcode.
Street-type abbreviations such as `Rd`, `St`, `Ave`, `Dr` are accepted — the address is resolved automatically via an address-matching service. Case is not significant.

This source covers addresses serviced by Lismore City Council, including localities such as Lismore, Nimbin, Goonellabah, Lismore Heights, South Lismore, Clunes, Dunoon, and other areas within the Lismore LGA.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: lismore_nsw_gov_au
      args:
        address: "71 Tuntable Falls Rd, NIMBIN NSW 2480"
```

## How to get the source arguments

1. Visit the [What's My Bin Day page](https://www.lismore.nsw.gov.au/Households/Waste-and-recycling/Whats-My-Bin-Day1) on the Lismore City Council website.
2. Type your address into the search box and confirm the result matches your property.
3. Copy the address exactly as shown in the suggestion list (abbreviations like `Rd` or `St` are fine).
4. Paste it as the `address` argument in your configuration.

If no results are returned, check that your address is within the Lismore LGA and is listed in the council's collection database.
