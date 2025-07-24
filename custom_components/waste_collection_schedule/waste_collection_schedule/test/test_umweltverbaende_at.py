import sys
import importlib.util
import os

sys.path.insert(
    0, "/workspaces/hacs_waste_collection_schedule/custom_components/waste_collection_schedule")
sys.path.insert(
    0, "/workspaces/hacs_waste_collection_schedule/custom_components/waste_collection_schedule/waste_collection_schedule/source")

# dynamically load module
module_path = os.path.join(
    "/workspaces/hacs_waste_collection_schedule/custom_components/waste_collection_schedule/waste_collection_schedule/source",
    "umweltverbaende_at.py"
)
spec = importlib.util.spec_from_file_location(
    "umweltverbaende_at", module_path)
umweltverbaende_at = importlib.util.module_from_spec(spec)
spec.loader.exec_module(umweltverbaende_at)


def run_all_tests():
    for name, params in umweltverbaende_at.TEST_CASES.items():
        print(f"\n--- Starte Testfall: {name} ---")
        try:
            src = umweltverbaende_at.Source(**params)
            result = src.fetch()
            print(f"Results for {name} (total count: {len(result)}):")
            for entry in result[:3]:
                print(entry)
            if len(result) > 3:
                print(f"...and {len(result)-3} more results.")
        except Exception as e:
            print(f"Error for {name}: {e}")


if __name__ == "__main__":
    run_all_tests()
