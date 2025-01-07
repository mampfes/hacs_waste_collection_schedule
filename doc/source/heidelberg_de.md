# City of Heidelberg
This source provides support for the waste collection schedule provided by the [Office of Waste Management and Municipal Cleansing Heidelberg](https://www.heidelberg.de/abfall). It's the successor to the ICS-based solution previously provided by [Gipsprojekt](../ics/gipsprojekt_de.md) (the contract was terminated by the city by the end of 2024).

## Configuration via configuration.yaml
```yaml
waste_collection_schedule:
  sources:
    - name: heidelberg_de
      args:
        street: "Name of Street"
        collect_residual_waste_weekly: True
        even_house_number: False
```

### Configuration Variables
**street**  
*(string) (required)* The street you want to get the waste collection schedule for. This value must match with an [entry from the API](https://garbage.datenplattform.heidelberg.de/streetnames). If you use the GUI to set up this source and your input doesn't match, we automatically suggest you entries based on the API response.

**collect_residual_waste_weekly**  
*(bool)* By default, the city collects residual waste on a weekly basis. If you decided to switch to a bi-weekly schedule to save some money, set this value to False. If you live on a rural street where the waste is only being collected biweekly, you don't need to change anything here as it's being taken into account automatically.

**even_house_number**  
*(bool)* In case you opted for a bi-weekly residual waste collection, it's important to know if your house number is even or not. This decides about the weeks of the waste being collected. Set to False for an uneven house number and True for an even house number.

### How to get the source arguments
The correct name for the street can be found under https://garbage.datenplattform.heidelberg.de/streetnames. It **must** match with the naming there. When that's not the case, we throw an exception with all entries from the API as suggestions.

In case you're not sure if your residual waste is being collected weekly or not, just check the label on your bin. The arranged collecting scheme is printed there.

### Examples
Typical street with minimal arguments set:
```yaml
waste_collection_schedule:
  sources:
    - name: heidelberg_de
      args:
        street: "Alte Bergheimer Straße"
```

No weekly collection of residual and biological waste possible as the street is only being served bi-weekly:
```yaml
waste_collection_schedule:
  sources:
    - name: heidelberg_de
      args:
        street: "Molkenkurweg"
```

Bi-weekly residual collection as option used together with an uneven street number:
```yaml
waste_collection_schedule:
  sources:
    - name: heidelberg_de
      args:
        street: "Alte Bergheimer Straße"
        collect_residual_waste_weekly: False
        even_house_number: False
```

Bi-weekly residual collection as option used together with an even street number:
```yaml
waste_collection_schedule:
  sources:
    - name: heidelberg_de
      args:
        street: "Alte Bergheimer Straße"
        collect_residual_waste_weekly: False
        even_house_number: True
```