with unified as (
    select * from {{ ref('int_tracks_unified') }}
)

select
    record_id,
    platform,
    platform_track_id,
    track_name,
    artist_name,
    album_name,
    rank,
    streams_or_popularity,
    duration_ms,
    release_date,
    ingested_date,
    ingested_at
from unified
