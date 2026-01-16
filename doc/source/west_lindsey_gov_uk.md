# West Lindsey District Council

Support for schedules provided by [West Lindsey District Council](https://www.west-lindsey.gov.uk), serving West Lindsey, Lincolnshire, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: west_lindsey_gov_uk
      args:
        x: EASTING
        y: NORTHING
        id: PROPERTY_ID
```

### Configuration Variables

**x**  
*(int |string) (required)*  
The 6-figure Easting grid reference assigned to your property.

**y**  
*(int | string) (required)*  
The 6-figure Northing grid reference assigned to your property.

**id**  
*(int | string) (required)*  
The unique property id assigned to your property.

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: west_lindsey_gov_uk
      args:
        x: 509762
        y: 384493
        id: 919
```

#### How to find your x, y, and id values

The simplest way to find the x, y, and id values for your property is to search for your bin collection schedule on https://www.west-lindsey.gov.uk/bins-waste-recycling/find-your-bin-collection-day
 with the browser's Developer Tools open and the Network tab visible.

As you interact with the website, you'll see the Network tab being populated with various calls being made to the backend. Once your collection schedule is being displayed, scroll down and look at the last few transactions.

If you click on the lines, a panel should appear showing further details. Focus on the Payload tab, and for one of the transactions you should see something like this:

```
script: \Cluster\Cluster.AuroraScript$
taskId: bins
format: js
updateOnly: true
query: x=482566;y=390375;id=16636
```

The `query` line contains the numbers to use for the x, y and id args. 

A picture paints a thousand words, so maybe this also helps:

![West Lindsey Screenshot](/images/west_lindsey_gov_uk.png)