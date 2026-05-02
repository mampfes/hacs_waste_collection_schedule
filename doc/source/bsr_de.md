# Berliner Stadtreinigungsbetriebe

Support for schedules provided by [bsr.de](https://www.bsr.de/).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: bsr_de
      args:
        schedule_id: "SCHEDID"
```

### Configuration Variables

**schedule_id**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: bsr_de
      args:
        schedule_id: "049011000107000039600010"
```

## How to get the source arguments

It's actually only one source argument!

### Via a program

There is a script with an interactive command line interface which generates the required source configuration:

[custom_components/waste_collection_schedule/waste_collection_schedule/wizard/bsr_de.py](../../custom_components/waste_collection_schedule/waste_collection_schedule/wizard/bsr_de.py).

First, install the Python modules `inquirer` and `requests`.
Then run this script from a shell and answer the questions.
The script will basically ask for the street and the house number.
It will then query the BSR for the `schedule_id`.

### Via the bsr.de website

1. Go to https://www.bsr.de/abfuhrkalender.
1. Enter your street (Straße) and house number (Hausnummer) in the form at the lower part of the page (you might get a list where you have to select your postal code).
1. Now you should see a calendar with pickup dates.
1. Click on the 3 dots in a circle that is directly above the calender on the right.
1. A popup opens (you can download either a PDF or a ICS document, but there's no need to do it).
1. When you hover with your mouse over one of the two links you will see the link at the very bottom of the window.
1. Part of this link is a 24 digit number - this is your `sched_id`.

Depending on your browser or operating system, you might have the chance to right-click on one of the links and select something like "Copy link address" from the context menu.
Paste that into a text editor.
Now you can easily access the 24 digit number.
