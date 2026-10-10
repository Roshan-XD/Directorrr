"""Explicit, offline fixture demo: python -m director.installations.demo --help."""
import argparse
import time
from pathlib import Path

from director.installations.downloader import FixtureDownloader
from director.installations.fixtures import fixture_manifest, fixture_payloads
from director.installations.jobs import InstallationJobManager
from director.installations.schemas import ManagerError, TERMINAL, manifest_digest
from director.installations.storage import ModelStorageManager


def main() -> int:
    parser = argparse.ArgumentParser(description="Install synthetic text bytes offline, never AI weights")
    parser.add_argument("--root",type=Path,required=True,help="Dedicated Director storage directory")
    parser.add_argument("--acknowledge-fixture-license",action="store_true")
    parser.add_argument("--remove",action="store_true",help="Remove the active Director-owned fixture")
    args = parser.parse_args()
    model = fixture_manifest()
    print(model.license_documents[0].text)
    if not args.remove and not args.acknowledge_fixture_license:
        print("Read this fixture license, then pass --acknowledge-fixture-license to accept it explicitly.")
        return 2
    manager = InstallationJobManager(ModelStorageManager(args.root),fixture_downloader=FixtureDownloader(fixture_payloads()))
    try:
        if args.remove:
            job = manager.start(model,"remove")
        elif manager.storage.active(model.id):
            job = manager.start(model,"verify")
        else:
            requirements = manager.licenses.requirements(model)
            ack = manager.licenses.record(model,requirements["document_set_digest"],accepted=True)
            job = manager.start(model,"install",manifest_digest(model),ack.id)
        while job.state not in TERMINAL:
            time.sleep(0.05)
            job = manager.get(job.id)
        print(f"{job.operation}: {job.state}; verified bytes: {job.verified_bytes}; generation ready: False")
        if job.error:
            print(job.error["code"] + ": " + job.error["message"])
        return 0 if job.state in {"ready","not_installed"} else 1
    except ManagerError as error:
        print(error.code + ": " + error.message)
        return 1
    finally:
        manager.close()


if __name__ == "__main__":
    raise SystemExit(main())
