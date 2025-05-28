from flask import Flask
from importlib.machinery import SourceFileLoader
from dashGMSrole import create_dash1
from dashAmount import create_dash2

server = Flask(__name__)

app1 = create_dash1(server)
app2 = create_dash2(server)

@server.route('/')
def index():
    return '''
        <h1>Welcome</h1>
        <p><a href="/app1/">GMS role</a></p>
        <p><a href="/app2/">Amount</a></p>
       
       
    '''

if __name__ == '__main__':
    server.run(debug=True)
