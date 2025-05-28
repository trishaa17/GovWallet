from flask import Flask
from importlib.machinery import SourceFileLoader
from dashTallyAccounts import create_dash1
from prepare import create_dash2

server = Flask(__name__)

app1 = create_dash1(server)
app2 = create_dash2(server)

@server.route('/')
def index():
    return '''
        <h1>Welcome</h1>
        <p><a href="/app1/">GovWallet Dashboard</a></p>
        <p><a href="/app2/">GovWallet Dashboard 2</a></p>
       
       
    '''

if __name__ == '__main__':
    server.run(debug=True)
