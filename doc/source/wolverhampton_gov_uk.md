<img src="/images/icon.png" alt="Waste Collection Schedule logo" title="Waste Collection Schedule" align="right" height="60" />

# Wolverhampton City Council

**Configuration via configuration.yaml**

```yaml
waste_collection_schedule:
  sources:
    - name: wolverhampton_gov_uk
      args:
        postcode: POSTCODE
        uprn: UPRN
```

**Configuration Variables**

**postcode** _(string) (required)_ : Your postcode
**uprn** _(string) (required)_ : The unique property reference number for your address

**How to find your UPRN**
1. Visit the [Wolverhampton Find My Nearest](https://www.wolverhampton.gov.uk/waste-and-recycling/bin-collection-dates) page
2. Enter your postcode and select your address
3. The UPRN will be visible in the URL after selecting your address (e.g., https://www.wolverhampton.gov.uk/find-my-nearest/WV11RD/10094887108 where 10094887108 is the UPRN)

**Example**

```yaml
waste_collection_schedule:
  sources:
    - name: wolverhampton_gov_uk
      args:
        postcode: "WV1 1RD"
        uprn: "10094887108"