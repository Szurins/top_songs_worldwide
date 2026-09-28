with source as (
    select * from {{ source('bronze', 'apple_music_songs') }}
),

exploded as (
    select
        cast(ingested_at as timestamp) as ingested_at,
        cast(ingested_date as date) as ingested_date,
        platform,
        t.platform_track_id,
        t.track_name,
        t.artist_name,
        t.album_name,
        cast(t.rank as int) as rank,
        try_cast(t.popularity_or_streams as bigint) as streams_or_popularity,
        try_cast(t.duration_ms as bigint) as duration_ms,
        try_cast(t.release_date as date) as release_date
    from source
    lateral view explode(tracks) exploded_table as t
)

select * from exploded
