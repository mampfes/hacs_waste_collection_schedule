# App GemInfo

Support for schedules provided by [App GemInfo](https://geminfo.app/), serving cities in Austria.

## Supported cities

<!--Begin of service section-->
|City|Website|
|-|-|
| Thannhausen | [thannhausen.at](https://www.thannhausen.at/)
<!--End of service section-->

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: geminfo_app
      args:
        city: CITY
        calendar: CALENDAR
        
        
```

### Configuration Variables

**city**  
*(String) (required)*

**calendar**  
*(String) (required)*


## Example

```yaml
waste_collection_schedule:
    sources:
    - name: geminfo_app
      args:
        city: Thannhausen
        calendar: Veranstaltungen & Termine    
```

## How to get the source argument

### Using the GemInfo app

The easiest way to find the parameter of the city is using [GemInfo app](https://geminfo.app/) directly. There is no destinction to streets in this city.

- Select your city.
- Open `Termine`.
- Select the types of waste to be collected under the link 
- Select the calendar view
- You should be able to see now the under [Kalender](https://geminfo.app/3-weiz-thannhausen/termine/kalender)
