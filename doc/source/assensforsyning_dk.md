# Assens Forsyning

Support for schedules from Assens Forsyning

Uses affaldonline, which serves several Danish municipalities, but differs when it comes to the layout of the response, which seems to be designed for the individual municipality.

I chose to write a specific solution for Assens Forsyning, since each municipality may choose a different supplier in the future.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
        - name: assensforsyning_dk
          args:
              values: "Rådhus Allé|1||||5610|Assens|12544|607551|0"
```

### Configuration Variables

**values**  
_(String) (required)_

A string that includes the street name, house number, postal code, city name, and some numbers that seems to be internal affaldonline references. 

## How to find the "values" string to use

Go to the Affaldonline site for assens: https://www.affaldonline.dk/kalender/assens/

Open the developer console in your browser.

Enter your address and select the house number in the dropdown menu.

In the Network tab in the browser console, select the latest URL ending in **showInfo.php** and look under Payload, where you should find the **values** variable read for copy/paste.

Depending on your browser, it should also be possible to right-click the house number field, and select "Inspect" - this should give you the html for the field, and here you can select the value from your house number in the list.

### Customizing Waste Types

Customizing waste types is a feature of the Waste Collection Schedule component and is very useful here, since the waste types in affaldonline are often long and not very consistent.

```yaml
waste_collection_schedule:
    sources:
        - name: assensforsyning_dk
          args:
              values: "Rådhus Allé|1||||5610|Assens|12544|607551|0"
          customize:
              - type: "Rest/Mad"
                alias: "Rest- og madaffald"
```