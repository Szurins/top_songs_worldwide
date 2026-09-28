with unified_tracks as (
    select * from {{ ref('int_tracks_unified') }}
),

artist_metrics as (
    select
        artist_name,
        ingested_date,
        count(distinct platform) as platforms_count,
        collect_set(platform) as platforms,
        count(*) as total_charting_tracks,
        min(rank) as best_rank_achieved,
        round(avg(rank), 2) as avg_chart_rank
    from unified_tracks
    where artist_name is not null
    group by artist_name, ingested_date
)

select * from artist_metrics
