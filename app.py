@st.cache_data
def load_data():
    data = {
        'DATA': pd.date_range(start='2023-01-01', periods=5, freq='M'),
        'LATITUDE': [-17.89, -17.91, -17.88, -17.92, -17.85],
        'LONGITUDE': [-43.42, -43.40, -43.45, -43.38, -43.50],
        'LOCAL': ['Bairro A', 'Bairro B', 'Bairro C', 'Bairro D', 'Bairro E'],
        'QUANTIDADE': [100, 200, 150, 180, 120]
    }
    df = pd.DataFrame(data)
    df['Ano'] = df['DATA'].dt.year
    df['Mês'] = df['DATA'].dt.month.astype('Int64')
    return df
