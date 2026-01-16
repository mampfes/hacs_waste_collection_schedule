# PreZero Bielsko-Biała

Support for waste collection schedules provided by [PreZero Bielsko-Biała](https://prezero-bielsko.pl/harmonogram-odbioru-odpadow/), serving the city of Bielsko-Biała, Poland.

## Configuration

To configure the `PreZero Bielsko-Biała` source, you need to provide the **street name** and **house number**. Please note that this source is designed **exclusively for the city of Bielsko-Biała**. The city of **Bielsko-Biała is hardcoded** and there is no option to configure a different city.

Simply provide the full street name and house number.

| Parameter        | Required | Description                                  |
| :--------------- | :------: | :------------------------------------------- |
| `street`         |   yes    | Street name. Please provide the full street name, for example: "Krakowska". |
| `house_number`   |   yes    | House number. Please provide the house number, for example: "12". |

## Configuration via configuration.yaml

Below is an example of the `PreZero Bielsko-Biała` source configuration in `configuration.yaml`:

```yaml
waste_collection_schedule:
  sources:
    - name: prezero_bielsko_pl
      args:
        street: "Krakowska"
        house_number: "12"