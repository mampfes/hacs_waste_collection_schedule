# Babergh and Mid Suffolk District Councils

Support for schedules provided by [Mid Suffolk District Council](https://www.midsuffolk.gov.uk/) and [Babergh District Council](https://babergh.gov.uk/), serving Mid Suffolk and Babergh, UK.

## Local Government Reorganisation note
This source **only** serves the areas covered by the **existing** Barbergh District Council and Mid Suffolk District Council. It does not cover other areas that will be in the upcoming Central and Eastern Suffolk Council area.

During the ongoing local government reorganisation (LGR) in Suffolk, please continue to use the source for your current area as long as it's still working. New sources for the new Western Suffolk, Central & Eastern Suffolk, and Ipswich & South Suffolk councils are not expected to be live until at least April 2028, when the councils themselves officially come into being.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: babergh_midsuffolk_gov_uk
      args:
        uprn: "UPRN"
        council: "COUNCIL"
```

### Configuration Variables

**uprn**
*(String | Integer) (required)*

Your Unique Property Reference Number (UPRN).

**council**
*(String) (required)*

Which council area you are in. Must be one of:
- `midsuffolk` — Mid Suffolk District Council
- `babergh` — Babergh District Council

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: babergh_midsuffolk_gov_uk
      args:
        uprn: "100091488908"
        council: "midsuffolk"
```

## How to find your UPRN

### Easy method using findmyaddress.co.uk

The easiest way to find your Unique Property Reference Number (UPRN) is to go to <https://www.findmyaddress.co.uk/> and enter your address details.

### Method using the council website

1. Go to <https://www.midsuffolk.gov.uk/check-your-collection-day> (Mid Suffolk) or <https://babergh.gov.uk/check-your-collection-day> (Babergh).
2. Open your browser's developer tools (F12) and go to the **Network** tab.
3. Enter your postcode and click **Find address**.
4. Look for a request to `/api/jsonws/invoke`. The response will contain a list of addresses, each with a `UPRN` field.
5. Select your address and note the UPRN value.
