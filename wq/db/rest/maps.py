from django.db.models import Func, Value
from django.http import HttpResponse
from django.db import connection
from django.conf import settings


def supports_vector_tiles():
    backend = settings.DATABASES.get("default", {}).get("ENGINE")

    if backend == "django.contrib.gis.db.backends.postgis":
        return True
    else:
        return False


def tiles(router, request, z, x, y):
    if not supports_vector_tiles():
        return HttpResponse(
            "Tile server not supported with this database engine.",
            content_type="text/plain",
            status=404,
        )
    tiledata = []
    envelope = TileEnvelope(z, x, y)
    cursor = connection.cursor()
    for name, conf in router.config["pages"].items():
        if not conf.get("list") or not conf.get("geometry_fields"):
            continue

        fields = ["id"]
        if lookup := conf.get("lookup"):
            fields.append(lookup)
        fields += list(conf.get("vector_tile_fields") or [])

        queryset = router.get_queryset_for_model(name, request)
        for field in conf["geometry_fields"]:
            model_info = (name, queryset, field["name"], fields)
            tiledata.append(get_tile_data(model_info, envelope, cursor))

    return HttpResponse(
        b"".join(tiledata),
        content_type="application/vnd.mapbox-vector-tile",
    )


def get_tile_data(model_info, envelope, cursor):
    name, queryset, geometry_field, fields = model_info
    geometry_mvt = f"{geometry_field}_mvt"
    fields = fields + [geometry_mvt]
    tile = (
        queryset.filter(geometry__bboverlaps=envelope)
        .annotate(**{geometry_mvt: TileGeom(geometry_field, envelope)})
        .values(*fields)
    )
    sql, params = tile.query.sql_with_params()
    sql = sql.replace(f'::bytea AS "{geometry_mvt}"', f' AS "{geometry_mvt}"')
    cursor.execute(
        f"SELECT ST_AsMVT(tile.*, '{name}', 4096, '{geometry_mvt}', 'id') FROM ({sql}) AS tile",
        params,
    )
    row = cursor.fetchone()
    return row[0]


class TileEnvelope(Func):
    arity = 3
    function = "ST_TileEnvelope"

    def __init__(self, z, x, y):
        from django.contrib.gis.db.models import GeometryField

        self.output_field = GeometryField(srid=3857)

        super().__init__(Value(z), Value(x), Value(y))


class TileGeom(Func):
    arity = 2
    function = "ST_AsMVTGeom"

    def __init__(self, geometry, envelope):
        from django.contrib.gis.db.models.functions import Transform

        geometry = Transform(geometry, srid=3857)
        super().__init__(geometry, envelope)


def update_tiles_url(plugin_conf, base_url):
    if not plugin_conf:
        return
    if "tiles" in plugin_conf:
        return
    if not supports_vector_tiles():
        return
    plugin_conf["tiles"] = base_url + "/tiles/{z}/{x}/{y}.pbf"


def update_geometry_fields(conf):
    if conf.get("form") and "geometry_fields" not in conf:
        geometry_fields = get_geometry_fields(conf["form"])
        if geometry_fields:
            conf["geometry_fields"] = geometry_fields


def update_map_config(conf, pages):
    if not conf.get("map"):
        return

    if conf.get("map") is True:
        if conf.get("list"):
            conf["map"] = [
                {
                    "mode": "list",
                    "auto_layers": True,
                },
                {"mode": "detail", "auto_layers": True},
                {"mode": "edit", "auto_layers": True},
            ]
        else:
            conf["map"] = {
                "mapId": "map",
                "auto_layers": True,
            }

    maps = conf.get("map")
    if isinstance(maps, dict):
        maps = [maps]
    for map_conf in maps:
        if map_conf.get("auto_layers") or map_conf.get("autoLayers"):
            mode = map_conf.get("mode")
            map_conf.pop("auto_layers", None)
            map_conf.pop("autoLayers", None)
            layers = map_conf.get("layers") or []
            reference_layers = pages.copy()
            if mode in ("list", "detail") and not layers:
                if conf.get("defer_geometry"):
                    if mode == "list" and supports_vector_tiles():
                        layers += get_tile_layers({conf["name"]: conf}, None)
                        reference_layers.pop(conf["name"])
                    else:
                        layers += get_geojson_url_layers(conf, mode)
                else:
                    layers += get_context_layers(conf, mode)
            if supports_vector_tiles():
                layers += get_tile_layers(reference_layers, mode)
            map_conf["layers"] = layers

    return conf


def get_geometry_fields(form, prefix=""):
    geometry_fields = []
    for field in form or []:
        if field["type"].startswith("geo"):
            geometry_fields.append(
                {
                    "name": prefix + field["name"],
                    "label": field["label"] or field["name"],
                    "type": field["type"],
                }
            )
        elif field["type"] == "group":
            geometry_fields += get_geometry_fields(
                field["children"],
                prefix=field["name"] + "." if field["name"] else "",
            )
        elif field["type"] == "repeat":
            geometry_fields += get_geometry_fields(
                field["children"], prefix=field["name"] + "[]."
            )

    return geometry_fields


def get_page_label(conf, mode):
    if mode == "list":
        page_label = conf.get("verbose_name_plural") or conf["name"]
    else:
        page_label = conf.get("verbose_name") or conf.get["name"]
    if page_label == page_label.lower():
        page_label = page_label.title()
    return page_label


def get_geometry_label(conf, field, mode):
    page_label = get_page_label(conf, mode)
    if len(conf.get("geometry_fields") or []) > 1:
        field_label = field["label"] or field["name"]
    else:
        field_label = None

    if field_label:
        return f"{page_label} - {field_label}"
    else:
        return page_label


def get_context_layers(conf, mode):
    if mode == "list":
        lookup_fn = "context_feature_collection"
    else:
        lookup_fn = "context_feature"

    layers = []
    for field in conf.get("geometry_fields") or []:
        layer_conf = {
            "name": get_geometry_label(conf, field, mode),
            "type": "geojson",
            "data": [lookup_fn, field["name"]],
            "popup": conf["name"],
        }
        if mode == "list":
            layer_conf["cluster"] = True  # TODO: implement in @wq/map-gl
        if conf.get("map_color"):
            layer_conf["color"] = conf["map_color"]
            # TODO: layer_conf["legend"] = ...
        layers.append(layer_conf)
    return layers


def get_geojson_url_layers(conf, mode):
    if mode == "list":
        url = "{{{rt}}}/" + conf["url"] + ".geojson"
    else:
        url = "{{{rt}}}/" + conf["url"] + "/{{{id}}}.geojson"

    layers = []
    for field in conf.get("geometry_fields") or []:
        layer_conf = {
            "name": get_geometry_label(conf, field, mode),
            "type": "geojson",
            "url": url,
            "popup": conf["name"],
        }
        if mode == "list":
            layer_conf["cluster"] = True  # TODO: implement in @wq/map-gl
        if conf.get("map_color"):
            layer_conf["color"] = conf["map_color"]
            # TODO: layer_conf["legend"] = ...
        layers.append(layer_conf)

    # Only last geometry supported in GeoJSONRenderer
    layers = layers[-1:]

    return layers


def get_tile_layers(pages, mode):
    layers = []
    for conf in sorted(pages.values(), key=layer_sort_key):
        page_name = conf["name"]
        fields = conf.get("geometry_fields")
        if not fields:
            continue
        for index, field in enumerate(fields):
            field_name = field["name"]
            layer_name = (
                page_name if index == 0 else f"{page_name}_{field_name}"
            )
            geometry_label = get_geometry_label(conf, field, "list")
            if mode:
                geometry_label = f"All {geometry_label}"
            layer_conf = {
                "name": geometry_label,
                "type": "vector-tile",
                "layer": layer_name,
                "popup": page_name,
            }
            if conf.get("map_icon"):
                layer_conf["icon"] = conf["map_icon"]
                if mode != "edit":
                    layer_conf["identifyLayers"] = [layer_name]
            else:
                if conf.get("map_color"):
                    layer_conf["color"] = conf["map_color"]
                    # TODO: layer_conf["legend"] = ...
                if mode != "edit":
                    if field.get("type") == "geopoint":
                        layer_conf["identifyLayers"] = [f"{layer_name}-circle"]
                    elif field.get("type") == "geotrace":
                        layer_conf["identifyLayers"] = [f"{layer_name}-line"]
                    elif field.get("type") == "geoshape":
                        layer_conf["identifyLayers"] = [f"{layer_name}-fill"]

            if "map_active" in conf:
                layer_conf["active"] = conf["map_active"]
            elif mode:
                layer_conf["active"] = False

            layers.append(layer_conf)
    return layers


def layer_sort_key(conf):
    order = conf.get("order") or 0
    label = get_page_label(conf, "list")
    return order, label
