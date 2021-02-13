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
        dcc.Interval(
            id='interval-component',
            interval=2000, # in milliseconds
            n_intervals=0
        )
    ])
)


# Multiple components can update everytime interval gets fired.
@app.callback(Output('live-update-graph', 'figure'),
              Input('interval-component', 'n_intervals'))
def update_graph_live(n):
    data = {
        'time': [],
        'price': []
    }
    market_client = MarketClient(url="https://api.hbdm.com")
    list_obj = market_client.get_candlestick("ETH_CQ", CandlestickInterval.MIN5, 15)
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
