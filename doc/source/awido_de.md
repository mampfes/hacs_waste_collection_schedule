# AWIDO based services

Cubefour AWIDO is a platform for waste schedules, which has several German cities and districts as customers. The homepage of the company is [https://www.awido-online.de/](https://www.awido-online.de/).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: awido_de
      args:
        customer: customer
        city: city
        street: street
        housenumber: 2
```

### Configuration Variables

**customer**  
*(string) (required)*

**city**  
*(string) (required)*

**street**  
*(string) (optional, depends on customer)*

**housenumber**  
*(integer) (optional, depends on customer)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: awido_de
      args:
        customer: rmk
        city: Waiblingen
        street: Benzstr.
        housenumber: 14
```

## Additional Attributes

For special waste collection events such as the **Schadstoffmobil** (hazardous waste mobile), the following extra attributes are provided on the sensor entity when available:

| Attribute | Description |
|-----------|-------------|
| `location` | The specific address/location for this collection event |
| `description` | Additional information about the event |
| `start_time` | Start time of the event (e.g. `"09:00"`) – only for timed events |
| `end_time` | End time of the event (e.g. `"11:00"`) – only for timed events |

These attributes allow differentiating between multiple Schadstoffmobil stops on the same day at different locations and times.

## How to get the source arguments

### customer

List of customers (2021-07-09):

<!--Begin of service section-->
<!--End of service section-->

### city, street, house number

- Go to your calendar at `https://awido.cubefour.de/Customer/<customer>/v2/Calendar2.aspx` (old version) or `https://awido.cubefour.de/Customer/<customer>/v3/Calendar2.aspx` (new version). Replace `<customer>` with the one of the keys listed above.
- Enter your city name from the first page into the `city` field.
- If you have to enter a street or district, enter the name into the `street` field.
- If you have to enter a house number, enter the house number into the `housenumber` field.
