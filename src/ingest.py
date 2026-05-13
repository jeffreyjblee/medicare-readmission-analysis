import requests
import zipfile
from pathlib import Path

RAW_DIR = Path(__file__).parent.parent / "data" / "raw"

# Beneficiary Summary Files — Samples 1 through 5
# Claims files — Sample 1 only (we will use inpatient for readmission labels)
SYNPUF_FILES = [
    (
        "beneficiary_sample1.zip",
        "https://www.cms.gov/Research-Statistics-Data-and-Systems/Downloadable-Public-Use-Files/SynPUFs/Downloads/DE1_0_2008_Beneficiary_Summary_File_Sample_1.zip"
    ),
    (
        "beneficiary_sample2.zip",
        "https://www.cms.gov/Research-Statistics-Data-and-Systems/Downloadable-Public-Use-Files/SynPUFs/Downloads/DE1_0_2008_Beneficiary_Summary_File_Sample_2.zip"
    ),
    (
        "beneficiary_sample3.zip",
        "https://www.cms.gov/Research-Statistics-Data-and-Systems/Downloadable-Public-Use-Files/SynPUFs/Downloads/DE1_0_2008_Beneficiary_Summary_File_Sample_3.zip"
    ),
    (
        "beneficiary_sample4.zip",
        "https://www.cms.gov/Research-Statistics-Data-and-Systems/Downloadable-Public-Use-Files/SynPUFs/Downloads/DE1_0_2008_Beneficiary_Summary_File_Sample_4.zip"
    ),
    (
        "beneficiary_sample5.zip",
        "https://www.cms.gov/Research-Statistics-Data-and-Systems/Downloadable-Public-Use-Files/SynPUFs/Downloads/DE1_0_2008_Beneficiary_Summary_File_Sample_5.zip"
    ),
    (
        "inpatient_sample1.zip",
        "https://www.cms.gov/Research-Statistics-Data-and-Systems/Downloadable-Public-Use-Files/SynPUFs/Downloads/DE1_0_2008_to_2010_Inpatient_Claims_Sample_1.zip"
    ),
    (
        "inpatient_sample2.zip",
        "https://www.cms.gov/Research-Statistics-Data-and-Systems/Downloadable-Public-Use-Files/SynPUFs/Downloads/DE1_0_2008_to_2010_Inpatient_Claims_Sample_2.zip"
    ),
    (
        "inpatient_sample3.zip",
        "https://www.cms.gov/Research-Statistics-Data-and-Systems/Downloadable-Public-Use-Files/SynPUFs/Downloads/DE1_0_2008_to_2010_Inpatient_Claims_Sample_3.zip"
    ),
    (
        "inpatient_sample4.zip",
        "https://www.cms.gov/Research-Statistics-Data-and-Systems/Downloadable-Public-Use-Files/SynPUFs/Downloads/DE1_0_2008_to_2010_Inpatient_Claims_Sample_4.zip"
    ),
    (
        "inpatient_sample5.zip",
        "https://www.cms.gov/Research-Statistics-Data-and-Systems/Downloadable-Public-Use-Files/SynPUFs/Downloads/DE1_0_2008_to_2010_Inpatient_Claims_Sample_5.zip"
    ),
]


def download_file(filename: str, url: str) -> bool:
    """Download a single file. Returns True on success, False on failure."""
    destination = RAW_DIR / filename

    if destination.exists():
        print(f"  Already exists, skipping: {filename}")
        return True

    print(f"  Downloading {filename}...")
    response = requests.get(url, stream=True, timeout=60)

    if response.status_code == 404:
        print(f"  WARNING: File not found (404) — {url}")
        return False

    response.raise_for_status()

    with open(destination, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    print(f"  Saved: {filename}")
    return True


def unzip_files() -> None:
    """Unzip all downloaded zip files."""
    zip_files = list(RAW_DIR.glob("*.zip"))
    print(f"\nUnzipping {len(zip_files)} files...")

    for zip_path in zip_files:
        print(f"  Unzipping {zip_path.name}...")
        with zipfile.ZipFile(zip_path, "r") as z:
            z.extractall(RAW_DIR)
        print(f"  Done.")


def run():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Downloading SynPUF files to: {RAW_DIR}\n")

    failed = []
    for filename, url in SYNPUF_FILES:
        success = download_file(filename, url)
        if not success:
            failed.append(filename)

    print("\nDownloads complete.")
    if failed:
        print(f"Failed: {failed}")
    else:
        print("All files downloaded successfully.")

    unzip_files()
    print("\nAll files ready.")


if __name__ == "__main__":
    run()