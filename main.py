import pandas as pd
import os
import dash_table
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly
import base64
import requests
import hashlib
import hmac
import datetime
from urllib import parse
import urllib.parse
from dash.dependencies import Input, Output, State
from huobi.client.market import MarketClient
from huobi.constant import CandlestickInterval

p_api_key = os.environ['p_api_key']
p_secret_key = os.environ['p_secret_key']

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.layout = html.Div(
    html.Div([
        html.H4('Huobi Futures Live Update'),
        dcc.Graph(id='live-update-graph'),
        dcc.Graph(id='update-graph'),
        html.Div([
            html.Div([
                html.Button('Buy', id='submit-buy', n_clicks=0),
                    dcc.Input(id="buy-price", type="number", placeholder="Price"),
                    dcc.Input(id="buy-quant", type="number", placeholder="Quantity")
        ]),
            html.Div([
                html.Button('Sell', id='submit-sell', n_clicks=0),
                    dcc.Input(id="sell-price", type="number", placeholder="Price"),
                    dcc.Input(id="sell-quant", type="number", placeholder="Quantity")
                    ])
        ]),
        html.Plaintext("No buy or sell order", id="result"),
        html.Div(id='table'),
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


def post_huobi(url, data, api_key, secret_key):
    timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
    param = {"AccessKeyId": api_key,
             "SignatureVersion": "2",
             "SignatureMethod": "HmacSHA256",
             "Timestamp": timestamp
             }

    host = urllib.parse.urlparse(url).hostname
    path = urllib.parse.urlparse(url).path

    method = "POST"

    keys = sorted(param.keys())
    qs0 = '&'.join(['%s=%s' % (key, parse.quote(param[key], safe='')) for key in keys])
    payload0 = '%s\n%s\n%s\n%s' % (method, host, path, qs0)
    dig = hmac.new(secret_key.encode('utf-8'), msg=payload0.encode('utf-8'), digestmod=hashlib.sha256).digest()
    s = base64.b64encode(dig).decode()
    param["Signature"] = s
    response = requests.post(url + "?" + urllib.parse.urlencode(param), headers={'Content-Type': 'application/json'},
                             json=data)
    return response.json()

@app.callback(Output('result', 'children'),
              [Input('submit-buy', 'n_clicks'), Input('submit-sell', 'n_clicks')],
              state=[State('buy-price', 'value'),
                     State('buy-quant', 'value'),
                     State('sell-price', 'value'),
                     State('sell-quant', 'value')
                     ]
              )
def execute_order(n_clicks_buy, n_clicks_sell, input1, input2, input3, input4):
    ctx = dash.callback_context

    if not ctx.triggered:
        button_id = 'No clicks yet'
    else:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if button_id == 'submit-buy' and input1 > 0 and input2 > 0:
        data = {'volume': int(input2),
                'direction': 'buy',
                'offset': 'open',
                'lever_rate': 3,
                'symbol': 'ETH',
                'order_price_type': 'opponent',
                'contract_type': 'next_week',
                'price': float(input1)
                }
        message = post_huobi('https://api.hbdm.com/api/v1/contract_order', data, p_api_key, p_secret_key)
        return 'Output from API {0}'.format(message['err_msg'])
    elif button_id == 'submit-sell' and input3 > 0 and input4 > 0:
        data = {'volume': int(input2),
                'direction': 'sell',
                'offset': 'open',
                'lever_rate': 3,
                'symbol': 'ETH',
                'order_price_type': 'opponent',
                'contract_type': 'next_week',
                'price': float(input3)
                }
        message = post_huobi('https://api.hbdm.com/api/v1/contract_order', data, p_api_key, p_secret_key)
        return 'Output from API {0}'.format(message['err_msg'])
    return 'No order.'

@app.callback(Output('table', 'children'),
              Input('interval-component', 'n_intervals'))
def order_history(n):
    data = {'type': 1,
            'trade_type': 0,
            'create_date': 30,
            'status': 0,
            'symbol': 'ETH'
            }
    response = post_huobi('https://api.hbdm.com/api/v1/contract_hisorders', data, p_api_key, p_secret_key)
    df = pd.DataFrame(response['data']['orders'])
    table = dash_table.DataTable(
        id='table_orders',
        columns=[{"name": i, "id": i} for i in df.columns],
        data=df.to_dict('records'))
    return table

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
