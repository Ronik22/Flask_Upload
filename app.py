import os
from flask import Flask, render_template, request, redirect, url_for, abort, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__)
# app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024
app.config['UPLOAD_EXTENSIONS'] = ['.*']
app.config['UPLOAD_PATH'] = 'uploads'


# @app.errorhandler(413)
# def too_large(e):
#     return "File is too large", 413

@app.route('/')
def index():
    files = os.listdir(app.config['UPLOAD_PATH'])
    return render_template('index.html', files=files)

@app.route('/', methods=['POST'])
def upload_files():
    uploaded_file = request.files['file']
    filename = secure_filename(uploaded_file.filename)
    uploaded_file.save(os.path.join(app.config['UPLOAD_PATH'], filename))
    return '', 204

@app.route('/uploads/<filename>')
def upload(filename):
    return send_from_directory(app.config['UPLOAD_PATH'], filename)

@app.route('/viewuploads', methods=['GET'])
def dirtree():
    path = 'uploads'
    return render_template('dirtree.html', tree=make_tree(path))


def make_tree(path):
    tree = dict(name=os.path.basename(path), children=[])
    try: lst = os.listdir(path)
    except OSError:
        pass
    else:
        for name in lst:
            tree['children'].append(dict(name=name))
    return tree   

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=8000)