import datetime
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly
from dash.dependencies import Input, Output
from huobi.client.market import MarketClient
from huobi.constant import CandlestickInterval

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.layout = html.Div(
    html.Div([
        html.H4('Huobi Futures Live Update'),
        dcc.Graph(id='live-update-graph'),
        dcc.Graph(id='update-graph'),
        dcc.Interval(
            id='interval-component-live',
            interval=1000, # in milliseconds
            n_intervals=0
        ),
        dcc.Interval(
            id='interval-component',
            interval=10000,  # in milliseconds
            n_intervals=0
        )

    ])
)

live_data = {
    'time': [],
    'price': []
}

# Multiple components can update everytime interval gets fired.
@app.callback(Output('live-update-graph', 'figure'),
              Input('interval-component-live', 'n_intervals'))
def update_graph_live(n):
    market_client = MarketClient(url="https://api.hbdm.com")
    list_obj = market_client.get_candlestick("ETH_CQ", CandlestickInterval.MIN1, 1)
    live_data['price'].append(list_obj[-1].close)
    live_data['time'].append(datetime.datetime.now().strftime('%c'))
    fig = plotly.tools.make_subplots(rows=1, cols=1, vertical_spacing=0.2)
    fig['layout']['margin'] = {
        'l': 30, 'r': 10, 'b': 30, 't': 10
    }
    fig['layout']['legend'] = {'x': 0, 'y': 1, 'xanchor': 'left'}

    fig.append_trace({
        'x': live_data['time'],
        'y': live_data['price'],
        'name': 'Price',
        'mode': 'lines+markers',
        'type': 'scatter'
    }, 1, 1)
    return fig

@app.callback(Output('update-graph', 'figure'),
              Input('interval-component', 'n_intervals'))
def update_graph(n):
    data = {
        'time': [],
        'price': []
    }
    market_client = MarketClient(url="https://api.hbdm.com")
    list_obj = market_client.get_candlestick("ETH_CQ", CandlestickInterval.MIN1, 200)
    for item in list_obj:
        data['price'].append(item.close)
        data['time'].append(datetime.datetime.fromtimestamp(item.id).strftime('%c'))
    fig = plotly.tools.make_subplots(rows=1, cols=1, vertical_spacing=0.2)
    fig['layout']['margin'] = {
        'l': 30, 'r': 10, 'b': 30, 't': 10
    }
    fig['layout']['legend'] = {'x': 0, 'y': 1, 'xanchor': 'left'}

    fig.append_trace({
        'x': data['time'],
        'y': data['price'],
        'name': 'Price',
        'mode': 'lines+markers',
        'type': 'scatter'
    }, 1, 1)
    return fig


if __name__ == '__main__':
    app.run_server(debug=True)
