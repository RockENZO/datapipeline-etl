"""Dataset search HTTP contracts backed by an immutable query registry."""
from dataclasses import dataclass
from functools import partial
import os

from flask import Flask, request, jsonify
from elasticsearch import Elasticsearch

app = Flask(__name__)
es = Elasticsearch(hosts=[f"http://{os.getenv('ELASTICSEARCH_HOST', 'localhost')}:9200"])


@dataclass(frozen=True)
class SearchSpec:
    index: str
    fields: tuple[str, ...] = ()
    mode: str = 'multi_match'
    optional_query: bool = False
    size: int | None = None
    source: tuple[str, ...] = ()
    geometry_filter: tuple[str, str] | None = None
    geometry_only: bool = False
    suffix: str = ''


SEARCHES = (
    SearchSpec('building_complex_points', ('properties.generalname', 'properties.street_name')),
    SearchSpec('pedestrian_counts', ('location_name', 'location_code')),
    SearchSpec('height_of_building', ('properties.EPI_NAME', 'properties.LGA_NAME', 'properties.MAP_NAME')),
    SearchSpec('stairs', ('properties.Name', 'properties.Address', 'properties.Suburb')),
    SearchSpec('recreation_centres', ('properties.Name', 'properties.Address', 'properties.Suburb')),
    SearchSpec('information_kiosks', ('properties.CentreName', 'properties.StreetAddress', 'properties.Suburb')),
    SearchSpec('ambulance_stations', ('properties.generalname', 'properties.urbanity')),
    SearchSpec('bicycle_network', ('properties.name', 'properties.region', 'properties.lga', 'properties.facility')),
    SearchSpec('free_15_minute_parking', ('properties.Street', 'properties.Section', 'properties.Suburb')),
    SearchSpec('residential_waste_recovery', ('properties.All_',), mode='match'),
    SearchSpec('business_rate_category', ('properties.BUS_VALUE',)),
    SearchSpec('ucl', ('properties.ucl_name_2021', 'properties.state_name_2021'),
               optional_query=True, size=10000, source=('geometry',)),
    SearchSpec('ticket_parking_rates', ('properties.PlanYear', 'properties.Tariff1', 'properties.Tariff2'),
               optional_query=True, size=10000),
    SearchSpec('parking_permits_areas', ('properties.Label', 'properties.Label_2', 'properties.Precinct',
               'properties.BusinessEligible', 'properties.VisitorEligible', 'properties.ResidentialEligible')),
    SearchSpec('lga_ndd_total', ('properties.fid',), mode='match', optional_query=True, size=1000,
               geometry_filter=('term', 'geometry.type.keyword'), geometry_only=True),
    SearchSpec('dzn', ('properties.dzn_code', 'properties.sa2_name_2021'), optional_query=True, size=1000,
               geometry_filter=('match', 'geometry.type'), geometry_only=True),
    SearchSpec('library_details', mode='exists', suffix='/has_feature'),
)


class InvalidSearch(ValueError):
    """Controlled client validation errors; never wrap backend exception text."""


def build_query(spec, args):
    query = args.get('query')
    geom_type = args.get('type')
    if spec.mode == 'exists':
        field = args.get('field')
        if not field:
            raise InvalidSearch('Field parameter is required')
        clause = {'exists': {'field': f'properties.{field}'}}
    elif spec.geometry_filter and geom_type:
        kind, field = spec.geometry_filter
        clause = {kind: {field: geom_type}}
    elif not query:
        if not spec.optional_query:
            raise InvalidSearch('Query parameter is required')
        clause = {'match_all': {}}
    elif spec.mode == 'match':
        clause = {'match': {spec.fields[0]: query}}
    else:
        clause = {'multi_match': {'query': query, 'fields': list(spec.fields)}}
    body = {'query': clause}
    if spec.source:
        body['_source'] = list(spec.source)
    return body


def search_dataset(spec):
    try:
        body = build_query(spec, request.args)
    except InvalidSearch as error:
        return jsonify({'error': str(error)}), 400
    options = {'size': spec.size} if spec.size is not None else {}
    try:
        response = es.search(index=spec.index, body=body, **options)
        hits = response['hits']['hits']
        if spec.geometry_only:
            hits = [{'type': hit['_source']['geometry'].get('type'),
                     'coordinates': hit['_source']['geometry'].get('coordinates')} for hit in hits]
        return jsonify(hits), 200
    except Exception:
        return jsonify({'error': 'Search service unavailable'}), 500


# Keep the literal URL set and Flask endpoint names; unknown datasets remain 404.
for spec in SEARCHES:
    path = spec.index + spec.suffix
    app.add_url_rule('/es_search/' + path, endpoint='search_' + path.replace('/', '_'),
                     view_func=partial(search_dataset, spec), methods=['GET'])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=False)
