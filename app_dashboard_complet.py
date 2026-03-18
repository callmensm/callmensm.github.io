#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import os
import glob
from datetime import datetime
import pycountry
from collections import Counter

# Configuration de la page
st.set_page_config(page_title="Troublemakers - Toutes les données", page_icon="🎵", layout="wide")
st.title("🎵 Troublemakers – Rapport exhaustif (tous les fichiers)")
st.markdown(f"*Dernière mise à jour : {datetime.now().strftime('%d/%m/%Y %H:%M')}*")

# --- Fonctions de chargement ---
def load_json_files(pattern):
    """Charge tous les fichiers JSON correspondant à un pattern et retourne une liste de (nom, contenu)."""
    files = glob.glob(pattern)
    data_list = []
    for f in files:
        try:
            with open(f, 'r', encoding='utf-8') as fp:
                data = json.load(fp)
                data_list.append((os.path.basename(f), data))
        except Exception as e:
            st.warning(f"Erreur de lecture de {f}: {e}")
    return data_list

def safe_load(filepath):
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return None
    return None

# --- Chargement de tous les fichiers ---
st.sidebar.header("Fichiers chargés")

# Dossiers
raw_files = glob.glob("data/raw/*.json") + glob.glob("data/raw/*.csv")
proc_files = glob.glob("data/processed/*.json") + glob.glob("data/processed/*.csv")

st.sidebar.write(f"**Fichiers bruts :** {len(raw_files)}")
st.sidebar.write(f"**Fichiers traités :** {len(proc_files)}")

# --- Données Spotify manuelles (on les garde car elles ne sont pas dans un fichier) ---
spotify_manual = {
    "followers": 2459,
    "monthly_listeners": 15529,
    "top_cities": [
        {"city": "Paris", "country": "FR", "listeners": 765},
        {"city": "Istanbul", "country": "TR", "listeners": 650},
        {"city": "Athens", "country": "GR", "listeners": 408},
        {"city": "Berlin", "country": "DE", "listeners": 257},
        {"city": "Izmir", "country": "TR", "listeners": 188}
    ]
}

# --- Chargement des fichiers Last.fm ---
lastfm_artist = safe_load("data/raw/lastfm_artist_info.json")
lastfm_similar = safe_load("data/raw/lastfm_similar.json")
lastfm_tags = safe_load("data/raw/lastfm_tags.json")
lastfm_top_albums = safe_load("data/raw/lastfm_top_albums.json")
lastfm_top_tracks = safe_load("data/raw/lastfm_top_tracks.json")
lastfm_geo_tags = safe_load("data/raw/lastfm_geo_tags.json")
lastfm_geo_ranks = safe_load("data/raw/lastfm_geo_ranks.json")
lastfm_geo_targeted = safe_load("data/raw/lastfm_geo_targeted.json")
lastfm_geo = safe_load("data/raw/lastfm_geo.json")

# --- Chargement des fichiers Discogs ---
# On va chercher le plus complet possible
discogs_complete = safe_load("data/raw/discogs_complete.json")
discogs_all_detailed = safe_load("data/raw/discogs_all_detailed.json")
discogs_releases_detailed = safe_load("data/raw/discogs_releases_detailed.json")
discogs_masters = safe_load("data/raw/discogs_masters.json")
discogs_labels = safe_load("data/raw/discogs_labels.json")
discogs_artist = safe_load("data/raw/discogs_artist.json")
discogs_community_stats = safe_load("data/raw/discogs_community_stats.json")

# On prend le fichier de releases le plus complet
if discogs_complete and 'releases' in discogs_complete:
    releases = discogs_complete['releases']
elif discogs_all_detailed and 'releases' in discogs_all_detailed:
    releases = discogs_all_detailed['releases']
elif discogs_releases_detailed:
    releases = discogs_releases_detailed
else:
    releases = None

# --- Chargement des fichiers processed ---
continental_analysis = safe_load("data/processed/continental_analysis.json")
discogs_pays = safe_load("data/processed/discogs_pays.json")
spotify_complete = safe_load("data/processed/spotify_complete.json")
timeline_by_album = None
if os.path.exists("data/processed/timeline_by_album.csv"):
    timeline_by_album = pd.read_csv("data/processed/timeline_by_album.csv")
cumulative_by_year = None
if os.path.exists("data/processed/cumulative_by_year.csv"):
    cumulative_by_year = pd.read_csv("data/processed/cumulative_by_year.csv")

# --- Extraction des données Discogs ---
if releases:
    # Pays
    pays_list = [r.get('country') for r in releases if r.get('country')]
    pays_counts = Counter(pays_list)
    discogs_pays_dict = dict(pays_counts.most_common())
    # Années
    annees_list = [r.get('year') for r in releases if r.get('year')]
    annees_counts = Counter(annees_list)
    # Labels
    labels_list = []
    for r in releases:
        for label in r.get('labels', []):
            if isinstance(label, dict) and 'name' in label:
                labels_list.append(label['name'])
    labels_counts = Counter(labels_list).most_common(20)
    # Genres / styles
    genres_list = []
    for r in releases:
        genres_list.extend(r.get('genres', []))
    genres_counts = Counter(genres_list).most_common(10)
else:
    discogs_pays_dict = discogs_pays if discogs_pays else {}
    annees_counts = {}
    labels_counts = []
    genres_counts = []

# --- Préparation des DataFrames ---
# Pays Discogs
if discogs_pays_dict:
    df_discogs_pays = pd.DataFrame(list(discogs_pays_dict.items()), columns=['pays', 'releases'])
else:
    df_discogs_pays = pd.DataFrame()

# Carte avec codes ISO
def get_iso3(country_name):
    mapping = {
        'UK': 'GBR', 'US': 'USA', 'Russia': 'RUS', 'Greece': 'GRC',
        'Netherlands': 'NLD', 'Switzerland': 'CHE', 'Mexico': 'MEX',
        'India': 'IND', 'Australia': 'AUS', 'Japan': 'JPN',
        'New Zealand': 'NZL', 'Poland': 'POL', 'South Korea': 'KOR',
        'Worldwide': None, 'Europe': None,
    }
    if country_name in mapping:
        return mapping[country_name]
    try:
        c = pycountry.countries.get(name=country_name)
        return c.alpha_3 if c else None
    except:
        return None

if not df_discogs_pays.empty:
    df_discogs_pays['iso3'] = df_discogs_pays['pays'].apply(get_iso3)
    df_discogs_map = df_discogs_pays[df_discogs_pays['iso3'].notna()]
else:
    df_discogs_map = pd.DataFrame()

# Continents
continent_map = {
    'France': 'Europe', 'Germany': 'Europe', 'UK': 'Europe', 'Greece': 'Europe',
    'Belgium': 'Europe', 'Netherlands': 'Europe', 'Italy': 'Europe',
    'Switzerland': 'Europe', 'Russia': 'Europe', 'Poland': 'Europe',
    'US': 'North America', 'Canada': 'North America', 'Mexico': 'North America',
    'Japan': 'Asia', 'India': 'Asia', 'South Korea': 'Asia',
    'Australia': 'Oceania', 'New Zealand': 'Oceania',
}
continents = {}
if not df_discogs_pays.empty:
    for _, row in df_discogs_pays.iterrows():
        cont = continent_map.get(row['pays'], 'Autre')
        continents[cont] = continents.get(cont, 0) + row['releases']
df_cont = pd.DataFrame(list(continents.items()), columns=['continent', 'nb']) if continents else pd.DataFrame()

# Top albums Last.fm
if lastfm_top_albums:
    df_albums = pd.DataFrame(lastfm_top_albums[:20])
    if 'playcount' in df_albums.columns:
        df_albums['playcount'] = pd.to_numeric(df_albums['playcount'], errors='coerce')
else:
    df_albums = pd.DataFrame()

# Top tracks
if lastfm_top_tracks:
    df_tracks = pd.DataFrame(lastfm_top_tracks[:20])
    if 'playcount' in df_tracks.columns:
        df_tracks['playcount'] = pd.to_numeric(df_tracks['playcount'], errors='coerce')
else:
    df_tracks = pd.DataFrame()

# Tags
if lastfm_tags:
    df_tags = pd.DataFrame(lastfm_tags[:20])
else:
    df_tags = pd.DataFrame()

# Artistes similaires
if lastfm_similar:
    df_similar = pd.DataFrame(lastfm_similar[:15])
else:
    df_similar = pd.DataFrame()

# Tags géographiques
if lastfm_geo_tags:
    df_geo_tags = pd.DataFrame(lastfm_geo_tags)
else:
    df_geo_tags = pd.DataFrame()

# Villes Spotify
cities_df = pd.DataFrame(spotify_manual['top_cities'])
city_coords = {
    'Paris': (48.8566, 2.3522),
    'Istanbul': (41.0082, 28.9784),
    'Athens': (37.9838, 23.7275),
    'Berlin': (52.5200, 13.4050),
    'Izmir': (38.4192, 27.1287)
}
cities_df['lat'] = cities_df['city'].map(lambda x: city_coords.get(x, (0,0))[0])
cities_df['lon'] = cities_df['city'].map(lambda x: city_coords.get(x, (0,0))[1])

# --- Navigation ---
page = st.sidebar.radio("Navigation", [
    "Vue d'ensemble",
    "Last.fm (détail)",
    "Discogs (détail)",
    "Spotify (manuel)",
    "Analyses temporelles",
    "Analyses géographiques",
    "Tous les fichiers"
])

# --- Vue d'ensemble ---
if page == "Vue d'ensemble":
    st.header("📊 Vue d'ensemble")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Followers Spotify", f"{spotify_manual['followers']:,}")
    with col2:
        st.metric("Auditeurs mensuels Spotify", f"{spotify_manual['monthly_listeners']:,}")
    with col3:
        if lastfm_artist and 'artist' in lastfm_artist:
            listeners = lastfm_artist['artist'].get('stats', {}).get('listeners', 0)
            st.metric("Auditeurs Last.fm", f"{int(listeners):,}")
        else:
            st.metric("Auditeurs Last.fm", "N/A")
    with col4:
        if lastfm_artist and 'artist' in lastfm_artist:
            playcount = lastfm_artist['artist'].get('stats', {}).get('playcount', 0)
            st.metric("Écoutes Last.fm", f"{int(playcount):,}")
        else:
            st.metric("Écoutes Last.fm", "N/A")

    st.subheader("Répartition continentale (Discogs)")
    if not df_cont.empty:
        fig = px.pie(df_cont, values='nb', names='continent', title="")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Pas de données continentales.")

    st.subheader("Top tags Last.fm")
    if not df_tags.empty:
        st.dataframe(df_tags.head(10))
    else:
        st.info("Pas de tags.")

# --- Last.fm détail ---
elif page == "Last.fm (détail)":
    st.header("🎧 Last.fm – Tous les fichiers")

    if lastfm_artist:
        st.subheader("Informations générales")
        a = lastfm_artist.get('artist', {})
        st.write(f"**Nom:** {a.get('name', 'N/A')}")
        st.write(f"**Écoutes:** {a.get('stats', {}).get('playcount', 'N/A')}")
        st.write(f"**Auditeurs:** {a.get('stats', {}).get('listeners', 'N/A')}")
        bio = a.get('bio', {}).get('summary', '')
        if bio:
            st.markdown(bio[:500] + "...")
        st.markdown(f"[Voir sur Last.fm]({a.get('url', '#')})")

    if not df_albums.empty:
        st.subheader("Top albums")
        fig_alb = px.bar(df_albums.head(10), x='name', y='playcount',
                         labels={'playcount': 'Écoutes', 'name': ''},
                         color='playcount', color_continuous_scale='Greens')
        fig_alb.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_alb, use_container_width=True)

    if not df_tracks.empty:
        st.subheader("Top titres")
        fig_tr = px.bar(df_tracks.head(10), x='name', y='playcount',
                        labels={'playcount': 'Écoutes', 'name': ''},
                        color='playcount', color_continuous_scale='Oranges')
        fig_tr.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_tr, use_container_width=True)

    if not df_tags.empty:
        st.subheader("Tags")
        fig_tags = px.bar(df_tags.head(10), x='count', y='name', orientation='h',
                          labels={'count': 'Fréquence', 'name': ''},
                          color='count', color_continuous_scale='Reds')
        st.plotly_chart(fig_tags, use_container_width=True)

    if not df_similar.empty:
        st.subheader("Artistes similaires")
        fig_sim = px.bar(df_similar.head(10), x='match', y='name', orientation='h',
                         labels={'match': 'Score', 'name': ''},
                         color='match', color_continuous_scale='Viridis')
        st.plotly_chart(fig_sim, use_container_width=True)

    if not df_geo_tags.empty:
        st.subheader("Tags géographiques")
        st.dataframe(df_geo_tags)

    if lastfm_geo_ranks:
        st.subheader("Classements par pays (geo.getTopArtists)")
        found = {k: v for k, v in lastfm_geo_ranks.items() if v.get('found')}
        if found:
            st.write(found)
        else:
            st.info("Aucun pays où le groupe est dans le top 200.")

    if lastfm_geo_targeted:
        st.subheader("Classements ciblés")
        st.write(lastfm_geo_targeted)

# --- Discogs détail ---
elif page == "Discogs (détail)":
    st.header("💿 Discogs – Tous les fichiers")

    st.subheader(f"Nombre total de releases : {len(releases) if releases else 0}")

    if not df_discogs_map.empty:
        st.subheader("Carte des pays")
        fig_map = px.scatter_geo(df_discogs_map, locations='iso3', size='releases',
                                 hover_name='pays', projection='natural earth',
                                 size_max=50, color_discrete_sequence=['#1DB954'])
        fig_map.update_layout(geo=dict(showframe=False, showcoastlines=True))
        st.plotly_chart(fig_map, use_container_width=True)

    if not df_discogs_pays.empty:
        st.subheader("Top 10 pays")
        top10 = df_discogs_pays.nlargest(10, 'releases')[['pays', 'releases']]
        fig_bar = px.bar(top10, x='pays', y='releases', text='releases', color='releases',
                         color_continuous_scale='Blues')
        fig_bar.update_traces(textposition='outside')
        st.plotly_chart(fig_bar, use_container_width=True)

    if not df_cont.empty:
        st.subheader("Répartition continentale")
        fig_pie = px.pie(df_cont, values='nb', names='continent',
                         color_discrete_sequence=px.colors.sequential.Viridis_r)
        st.plotly_chart(fig_pie, use_container_width=True)

    if annees_counts:
        st.subheader("Sorties par année")
        df_annees = pd.DataFrame(list(annees_counts.items()), columns=['année', 'nb']).sort_values('année')
        fig_line = px.line(df_annees, x='année', y='nb', markers=True, title="")
        st.plotly_chart(fig_line, use_container_width=True)

    if labels_counts:
        st.subheader("Top labels")
        df_labels = pd.DataFrame(labels_counts, columns=['label', 'nb'])
        fig_labels = px.bar(df_labels.head(10), x='nb', y='label', orientation='h', color='nb',
                            color_continuous_scale='Viridis')
        st.plotly_chart(fig_labels, use_container_width=True)

    if genres_counts:
        st.subheader("Genres")
        df_genres = pd.DataFrame(genres_counts, columns=['genre', 'count'])
        st.dataframe(df_genres)

    # Affichage des fichiers checkpoint (liste)
    checkpoints = glob.glob("data/raw/discogs_checkpoint_*.json")
    if checkpoints:
        st.subheader("Fichiers checkpoint")
        st.write(", ".join([os.path.basename(f) for f in checkpoints]))

# --- Spotify manuel ---
elif page == "Spotify (manuel)":
    st.header("📱 Spotify – Données relevées manuellement")

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Followers", f"{spotify_manual['followers']:,}")
    with col2:
        st.metric("Auditeurs mensuels", f"{spotify_manual['monthly_listeners']:,}")

    if not cities_df.empty:
        st.subheader("Carte des villes d'écoute")
        fig_cities = px.scatter_geo(cities_df, lat='lat', lon='lon', size='listeners',
                                    hover_name='city', projection='natural earth',
                                    size_max=30, color='country',
                                    color_discrete_sequence=px.colors.qualitative.Set1)
        fig_cities.update_layout(geo=dict(showframe=False, showcoastlines=True))
        st.plotly_chart(fig_cities, use_container_width=True)

    st.subheader("Détail des villes")
    st.dataframe(cities_df[['city', 'country', 'listeners']])

    if spotify_complete:
        st.subheader("Données Spotify API (si disponibles)")
        st.json(spotify_complete)

# --- Analyses temporelles ---
elif page == "Analyses temporelles":
    st.header("📈 Analyses temporelles")

    if timeline_by_album is not None:
        st.subheader("Timeline par album")
        st.dataframe(timeline_by_album)
        if 'year' in timeline_by_album.columns and 'youtube_views' in timeline_by_album.columns:
            fig = px.line(timeline_by_album, x='year', y='youtube_views', title="Vues YouTube par année")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Fichier timeline_by_album.csv non trouvé.")

    if cumulative_by_year is not None:
        st.subheader("Cumul par année")
        st.dataframe(cumulative_by_year)
        if 'year' in cumulative_by_year.columns and 'cumulative_views' in cumulative_by_year.columns:
            fig = px.line(cumulative_by_year, x='year', y='cumulative_views', title="Cumul des vues YouTube")
            st.plotly_chart(fig, use_container_width=True)

    if annees_counts:
        st.subheader("Sorties Discogs par année")
        df_annees = pd.DataFrame(list(annees_counts.items()), columns=['année', 'nb']).sort_values('année')
        fig = px.bar(df_annees, x='année', y='nb', title="Nombre de releases par année")
        st.plotly_chart(fig, use_container_width=True)

# --- Analyses géographiques ---
elif page == "Analyses géographiques":
    st.header("🌍 Analyses géographiques")

    if not df_discogs_map.empty:
        st.subheader("Releases Discogs par pays")
        st.plotly_chart(px.scatter_geo(df_discogs_map, locations='iso3', size='releases',
                                       hover_name='pays', projection='natural earth',
                                       size_max=50).update_layout(geo=dict(showframe=False)), use_container_width=True)

    if not df_cont.empty:
        st.subheader("Continent (Discogs)")
        st.plotly_chart(px.pie(df_cont, values='nb', names='continent'), use_container_width=True)

    if not cities_df.empty:
        st.subheader("Villes Spotify")
        st.plotly_chart(px.scatter_geo(cities_df, lat='lat', lon='lon', size='listeners',
                                       hover_name='city', projection='natural earth',
                                       size_max=30, color='country').update_layout(geo=dict(showframe=False)), use_container_width=True)

    if not df_geo_tags.empty:
        st.subheader("Tags géographiques Last.fm")
        st.dataframe(df_geo_tags)

    if lastfm_geo_ranks:
        found = {k: v for k, v in lastfm_geo_ranks.items() if v.get('found')}
        if found:
            st.subheader("Classements par pays (Last.fm)")
            st.write(found)

    if continental_analysis:
        st.subheader("Analyse continentale (fichier processed)")
        st.json(continental_analysis)

# --- Tous les fichiers ---
elif page == "Tous les fichiers":
    st.header("📁 Liste de tous les fichiers chargés")

    st.subheader("Fichiers bruts (raw)")
    for f in sorted(raw_files):
        st.write(f"- {os.path.basename(f)}")

    st.subheader("Fichiers traités (processed)")
    for f in sorted(proc_files):
        st.write(f"- {os.path.basename(f)}")

# --- Footer ---
st.sidebar.markdown("---")
st.sidebar.info("Rapport généré à partir de l'ensemble des fichiers JSON collectés.")