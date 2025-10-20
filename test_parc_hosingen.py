from custom_components.waste_collection_schedule.waste_collection_schedule.source.valorlux_lu import Source
from datetime import datetime

try:
    # Instantiate the source for Parc Hosingen
    source = Source(commune="Parc Hosingen")

    # Fetch the collection dates
    collections = source.fetch()

    # Filter for upcoming dates and sort them
    today = datetime.now().date()
    upcoming_collections = sorted([c for c in collections if c.date >= today], key=lambda c: c.date)

    if upcoming_collections:
        print("Next 5 upcoming Valorlux collections for Parc Hosingen:")
        for collection in upcoming_collections[:5]:
            print(f"- {collection.date.strftime('%Y-%m-%d')}: {collection.t}")
    else:
        print("No upcoming collections found for Parc Hosingen.")
except Exception as e:
    print(f"An error occurred: {e}")
