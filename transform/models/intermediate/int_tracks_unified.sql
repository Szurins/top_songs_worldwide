with spotify as (
    select * from {{ ref('stg_spotify_songs') }}
),
apple as (
    select * from {{ ref('stg_apple_music_songs') }}
),
youtube as (
    select * from {{ ref('stg_youtube_music_songs') }}
),
soundcloud as (
    select * from {{ ref('stg_soundcloud_songs') }}
),

unioned as (
    select * from spotify
    union all
    select * from apple
    union all
    select * from youtube
    union all
    select * from soundcloud
),

final as (
    select
        md5(concat_ws('||', platform, coalesce(platform_track_id, track_name), cast(ingested_date as string))) as record_id,
        platform,
        platform_track_id,
        trim(track_name) as track_name,
        trim(artist_name) as artist_name,
        trim(album_name) as album_name,
        rank,
        streams_or_popularity,
        duration_ms,
        release_date,
        ingested_date,
        ingested_at
    from unioned
)

select * from final
