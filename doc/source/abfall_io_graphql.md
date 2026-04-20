# Abfall.IO / AbfallPlus (GraphQL)

Support for schedules provided by [Abfall.IO](https://abfall.io) using the v3 GraphQL API. The official homepage is [AbfallPlus.de](https://www.abfallplus.de/).

Use this source if your provider uses the new v3 API. If you are unsure which API version your provider uses, try the [Abfall.IO (legacy)](abfall_io.md) source first; if it returns an error saying the key is not valid, switch to this source.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: abfall_io_graphql
      args:
        key: KEY
        idHouseNumber: HOUSE_NUMBER_ID
        wasteTypes:
          - "1"
          - "2"
```

### Configuration Variables

**key**
*(string) (required)*

32-character service key for your provider. See [How to get the source arguments](#how-to-get-the-source-arguments) below.

**idHouseNumber**
*(integer) (required)*

Numeric ID identifying your address in the abfall.io system. Use the wizard script to find this value.

**wasteTypes**
*(list of string) (optional)*

List of waste type IDs to include. If omitted, all default waste types for your address are fetched. Use the wizard script to find available IDs.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: abfall_io_graphql
      args:
        key: "efb75cbd1f08fae1d4e47ae72a85c655"
        idHouseNumber: 4136
```

## How to get the source arguments

### Simple variant: use the wizard script

There is an interactive wizard script that guides you through finding your `key`, `idHouseNumber`, and `wasteTypes`:

[https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/custom_components/waste_collection_schedule/waste_collection_schedule/wizard/abfall_io_graphql.py](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/custom_components/waste_collection_schedule/waste_collection_schedule/wizard/abfall_io_graphql.py)

Install the `inquirer` Python module, then run the script and answer the prompts.

### Manual variant: extract arguments from browser developer tools

#### Finding your `key`

1. Open your provider's waste collection schedule page in a desktop browser.
2. Accept the cookie consent for the abfallplus widget (usually labelled "Abfuhrtermine" or similar).
3. Open Developer Tools (`Ctrl+Shift+I`) and go to the **Network** tab.
4. Reload the page or interact with the widget.
5. Look for a request to `api.abfall.io` with a query parameter `key=`. The 32-character hex value is your service key.

#### Finding your `idHouseNumber`

1. With Developer Tools still open on the Network tab, select your city, street, and house number in the widget.
2. Look for a request to `widgets.abfall.io/graphql`.
3. In the request payload, find the `idHouseNumber` variable — that is the value you need.
