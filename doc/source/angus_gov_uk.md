# Angus Council

**Title**: Angus Council
**Description**: Supports all councils using the `myangus.angus.gov.uk` (Granicus/Firmstep) portal.

## Configuration

| Parameter | Type | Required | Description |
|---|---|---|---|
| `uprn` | string | Yes | Unique Property Reference Number |
| `postcode` | string | Yes | Postcode (e.g. DD11 2RH) |

### How to get your UPRN
1. An easy way to discover your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering in your address details.

OR

1. Go to [https://myangus.angus.gov.uk/service/Bin_collection_dates_V3](https://myangus.angus.gov.uk/service/Bin_collection_dates_V3)
2. Search for your address.
3. Open your browser Developer Tools (F12) and go to the **Network** tab.
4. Select your address from the dropdown list on the website.
5. In the Network tab, look for a request named `runLookup...`.
6. Click on it and view the **Payload** or **Request Data**.
7. Look for `select_NewAddress` or `serviceUPRN`. The value (usually starting with `1...`) is your UPRN.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: angus_gov_uk
      args:
        uprn: "117097214"
        postcode: "DD11 2RH"