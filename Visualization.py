# !pip install folium
# !pip install reverse_geocoder
# !pip install branca

import pandas as pd
import numpy as np
import folium
from folium import plugins
from flask import Flask
import branca

df = pd.read_excel('Test TTI.xlsx')
margin = .2 # dalam skala 0-1

index_drop = []
for idx in range(len(df)):
    if df['LONG'][idx]==0.0 or df['LAT'][idx]==0.0:
        index_drop.append(idx)
        
df.drop(index_drop, inplace=True)
df.dropna(inplace=True)
df.reset_index(drop=True, inplace=True)

df['Delta TTI'] = (df['TTI_DAY-2']-df['TTI_DAY-1'])/df['TTI_DAY-1']
df.head()

status = []
def check_status(row):
    if row<margin*-1:
        return 'Hijau'
    elif row>margin:
        return 'Merah'
    elif row<margin or row>margin*-1:
        return 'Abu-Abu'
    else:
        return 'Error'

df['Status'] = df['Delta TTI'].map(lambda x: check_status(x))

tti_good = np.array((
        df['LAT'][df['Status']=='Hijau'],
        df['LONG'][df['Status']=='Hijau']
    )
).T

tti_bad = np.array((
        df['LAT'][df['Status']=='Merah'],
        df['LONG'][df['Status']=='Merah']
    )
).T

tti_stable = np.array((
        df['LAT'][df['Status']=='Abu-Abu'],
        df['LONG'][df['Status']=='Abu-Abu']
    )
).T

tti_moreThan_25_points = np.array((
        df['LAT'][df['TTI_DAY-2']>25],
        df['LONG'][df['TTI_DAY-2']>25]
    )
).T


def popup_html(row):
    i = row
    lat = df['LAT'].iloc[i]
    long = df['LONG'].iloc[i] 
    tti_day1 = round(df['TTI_DAY-1'].iloc[i], 2)
    tti_day2 = round(df['TTI_DAY-2'].iloc[i], 2)
    delta_tt1 = round(df['Delta TTI'].iloc[i], 4)*100
    site_id = df['NEW SITE ID'].iloc[i]
    site_name = df['New Site Name'].iloc[i]
    
    left_col_color = "#19a7bd"
    right_col_color = "#f2f0d3"
    
    html = """<!DOCTYPE html>
<html>
<head>
<h4 style="margin-bottom:10"; width="200px">{}</h4>""".format(site_id) + """
</head>
    <table style="height: 126px; width: 350px;">
<tbody>
<tr>
<td style="background-color: """+ left_col_color +""";"><span style="color: #ffffff;">Latitude</span></td>
<td style="width: 150px;background-color: """+ right_col_color +""";">{}</td>""".format(lat) + """
</tr>
<tr>
<td style="background-color: """+ left_col_color +""";"><span style="color: #ffffff;">Longitude</span></td>
<td style="width: 150px;background-color: """+ right_col_color +""";">{}</td>""".format(long) + """
</tr>
<tr>
<td style="background-color: """+ left_col_color +""";"><span style="color: #ffffff;">TTI Day 1</span></td>
<td style="width: 150px;background-color: """+ right_col_color +""";">{}</td>""".format(tti_day1) + """
</tr>
<tr>
<td style="background-color: """+ left_col_color +""";"><span style="color: #ffffff;">TTI Day 2</span></td>
<td style="width: 150px;background-color: """+ right_col_color +""";">{}</td>""".format(tti_day2) + """
</tr>
<tr>
<td style="background-color: """+ left_col_color +""";"><span style="color: #ffffff;">Delta TTI %</span></td>
<td style="width: 150px;background-color: """+ right_col_color +""";">{}</td>""".format(delta_tt1) + """
</tr>
<tr>
<td style="background-color: """+ left_col_color +""";"><span style="color: #ffffff;">Site Name</span></td>
<td style="width: 150px;background-color: """+ right_col_color +""";">{}</td>""".format(site_name) + """
</tr>
</tbody>
</table>
</html>
"""
    return html

app = Flask(__name__)

@app.route('/')
def index():
    m = folium.Map(tiles='Stamen Terrain',
                   zoom_start=15)

    folium.TileLayer('Stamen Terrain').add_to(m)
    folium.TileLayer('Stamen Toner').add_to(m)
    folium.TileLayer('Stamen Water Color').add_to(m)
    folium.TileLayer('cartodbpositron').add_to(m)
    folium.TileLayer('cartodbdark_matter').add_to(m)



    mcg = folium.FeatureGroup(control=False).add_to(m)    # Marker Cluster, hidden in controls
    status_hijau_m_ = folium.plugins.FeatureGroupSubGroup(mcg, 'Status Membaik').add_to(m) # First group, in mcg
    status_merah_m_ = folium.plugins.FeatureGroupSubGroup(mcg, 'Status Memburuk').add_to(m) # Second group, in mcg
    status_abuAbu_m_ = folium.plugins.FeatureGroupSubGroup(mcg, 'Status Stabil').add_to(m) # Third group, in mcg
    tti_lebihDari_25 = folium.plugins.FeatureGroupSubGroup(mcg, 'TTI Lebih Dari 25').add_to(m)

    cluster_status_hijau_m_ = plugins.MarkerCluster().add_to(status_hijau_m_)
    cluster_status_merah_m_ = plugins.MarkerCluster().add_to(status_merah_m_)
    cluster_status_abuAbu_m_ = plugins.MarkerCluster().add_to(status_abuAbu_m_)
    # cluster_tti_lebihDari_25_ = plugins.MarkerCluster().add_to(tti_lebihDari_25)

    for i in range(len(df)):
        html = popup_html(i)
        iframe = branca.element.IFrame(html=html,width=510,height=280)
        popup = folium.Popup(folium.Html(html, script=True), max_width=500)

        if df['Status'][i]=='Hijau':
            folium.Marker(
                location=[df['LAT'][i], df['LONG'][i]],
                icon=folium.Icon(icon="arrow-up", icon_color='black',
                                 color='green'),
                popup=popup
            ).add_to(cluster_status_hijau_m_)

        elif df['Status'][i]=='Merah':
            folium.Marker(
                location=[df['LAT'][i], df['LONG'][i]],
                icon=folium.Icon(icon="arrow-down", icon_color='black',
                                 color='red'),
                popup=popup
            ).add_to(cluster_status_merah_m_)

        else:
            folium.Marker(
                location=[df['LAT'][i], df['LONG'][i]],
                icon=folium.Icon(icon="sort", icon_color='black',
                                 color='gray'),
                popup=popup
            ).add_to(cluster_status_abuAbu_m_)

    # for j in range(len(df)):
    #     html = popup_html(j)
    #     iframe = branca.element.IFrame(html=html,width=510,height=280)
    #     popup = folium.Popup(folium.Html(html, script=True), max_width=500)    

    #     if df['TTI_DAY-2'][i]>25:
    #         folium.Marker(
    #             location=[df['LAT'][i], df['LONG'][i]],
    #             icon=folium.Icon(icon="exclamation-sign", color='red'),
    #             popup=popup
    #         ).add_to(cluster_tti_lebihDari_25_)

    tti_lebihDari_25.add_child(
        plugins.MarkerCluster(
            tti_moreThan_25_points,
            icons=[folium.Icon(icon='exclamation-sign',
                               color='red') for _ in range(len(tti_moreThan_25_points))]
        )
    )

    draw = plugins.Draw(export=True)
    draw.add_to(m)
    folium.LayerControl().add_to(m)
    m.fit_bounds(m.get_bounds())

    return m._repr_html_()


if __name__ == "__main__":
        app.run(debug=True)