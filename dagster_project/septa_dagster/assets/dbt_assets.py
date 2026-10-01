from pathlib import Path

from dagster import AssetExecutionContext, AssetKey
from dagster_dbt import DagsterDbtTranslator, DbtCliResource, DbtProject, dbt_assets

DBT_PROJECT_DIR = Path(__file__).resolve().parents[3] / "dbt_project"

dbt_project = DbtProject(project_dir=DBT_PROJECT_DIR, profiles_dir=DBT_PROJECT_DIR)
dbt_project.prepare_if_dev()

# Maps each dbt source table back to the upstream bronze asset that actually
# writes the files it reads, so Dagster's asset graph shows the real
# lineage (e.g. raw_transitview_all_snapshot -> stg_transitview_all__...)
# instead of treating dbt sources as disconnected roots.
_SOURCE_TO_BRONZE_ASSET = {
    ("bronze", "transitview_all_raw"): AssetKey("raw_transitview_all_snapshot"),
    ("bronze", "stops_by_route_raw"): AssetKey("raw_stops_by_route"),
    ("bronze", "gtfs_routes_raw"): AssetKey("raw_gtfs_routes"),
    ("bronze", "gtfs_shapes_raw"): AssetKey("raw_gtfs_shapes"),
    ("bronze", "gtfs_trips_raw"): AssetKey("raw_gtfs_trips"),
}


class SeptaDbtTranslator(DagsterDbtTranslator):
    def get_asset_key(self, dbt_resource_props):
        if dbt_resource_props["resource_type"] == "source":
            mapped = _SOURCE_TO_BRONZE_ASSET.get(
                (dbt_resource_props["source_name"], dbt_resource_props["name"])
            )
            if mapped:
                return mapped
        return super().get_asset_key(dbt_resource_props)


@dbt_assets(manifest=dbt_project.manifest_path, dagster_dbt_translator=SeptaDbtTranslator())
def septa_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
    yield from dbt.cli(["build"], context=context).stream()
