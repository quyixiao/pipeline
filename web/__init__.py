from flask import Flask, make_response, request, render_template, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/<int:id>')
def showdag(id):
    return render_template('chart{}.html'.format(id))


def simplechart():
    xs = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    data = [820, 932, 901, 934, 1290, 1330, 1320]
    return jsonify({'xs':xs, 'data':data})


