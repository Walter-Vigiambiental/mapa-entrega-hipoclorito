import folium

# Criando o mapa centralizado (use coordenadas médias da região)
mapa_estoque = folium.Map(location=[-16.73, -43.87], zoom_start=12)

# Dados fictícios de locais com hipoclorito em estoque
dados_estoque = [
    {"nome": "UBS Centro", "lat": -16.728, "lon": -43.861, "quantidade": 30},
    {"nome": "UBS Sul", "lat": -16.738, "lon": -43.870, "quantidade": 45},
    {"nome": "UBS Norte", "lat": -16.722, "lon": -43.875, "quantidade": 20},
]

# Adicionando ícones de frasco de remédio para cada local
for dado in dados_estoque:
    texto_popup = f"{dado['nome']}<br>Hipoclorito disponível: {dado['quantidade']} frascos"
    folium.Marker(
        location=[dado['lat'], dado['lon']],
        popup=texto_popup,
        icon=folium.Icon(color='orange', icon='medkit', prefix='fa')
    ).add_to(mapa_estoque)

# Legenda explicativa (usando o plugin FloatImage como alternativa para ícones visuais)
legend_html = '''
<div style="position: fixed; bottom: 30px; left: 30px; width: 200px; height: 100px;
     background-color: white; border:2px solid grey; z-index:9999; font-size:14px;
     padding: 10px;">
     <b>Legenda:</b><br>
     <i class="fa fa-medkit" style="color: orange"></i> Locais com hipoclorito em estoque
</div>
'''
mapa_estoque.get_root().html.add_child(folium.Element(legend_html))

# Salvando como HTML (opcional)
mapa_estoque.save("mapa_estoque_hipoclorito.html")
