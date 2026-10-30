# Dataset search boundary

`es_search_api.py` serves 17 literal dataset routes. Requests flow through the
immutable `SEARCHES` registry, `build_query`, the shared Elasticsearch transport
and a hit/geometry projection. `SearchSpec` holds only dataset configuration;
query construction does not open connections. The existing shared client and
container startup remain unchanged.

The registry replaces repeated handlers while preserving HTTP paths, Flask
endpoint names, required query/field validation, untrimmed query values, search
fields, `match` versus `multi_match`, optional match-all queries, `_source`, result
limits and geometry-only responses. The LGA/DZN `type` filter keeps precedence
over text queries and retains each dataset's original term/match behavior.
Unknown paths remain 404. Backend exceptions remain generic HTTP 500 responses;
the interactive debugger remains disabled. This refactor does not add a new API,
authentication or production deployment.

## Verification and extension

`tests/fixtures/search_contract.json` captures 102 request cases from reviewed
baseline `9f7848be262c89b1538997a56409db3ac50482d9`, using a labelled synthetic
backend response. Tests compare response status/body, exact Elasticsearch keyword
arguments and endpoint identity. Existing failure tests cover all routes and
ensure backend details stay private. The fixture is a compatibility baseline,
not real city data or a performance result.

To add a dataset, explicitly add its immutable specification and independent
expected contract tests; do not regenerate the old fixture to hide a behavior
change. There is no automatic dataset discovery. Real Elasticsearch/map and
address-service integration CI still verifies the surrounding application.
