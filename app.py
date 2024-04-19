# app.py
 
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
from bson import ObjectId
import os
import timeit
 
from mongodb_connection import collection
from text_processing import process_text_documents, run_ingest
from utils import allowed_file
 
app = Flask(__name__)
CORS(app)
UPLOAD_FOLDER = '/home/genaidevassetv1/GenAI/Genesis/data'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
 
@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and store in folder and MongoDB."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request!'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected for uploading!'}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        try:
            with open(file_path, 'rb') as f:
                file_data = f.read()
            metadata = {
                'document': filename,
                'version': '1.0',
                'date': timeit.default_timer(),
                'status': 'uploaded'
            }
            result = collection.insert_one(metadata)
            return jsonify({'message': 'File uploaded and stored successfully!', 'file_id': str(result.inserted_id)}), 200
        except Exception as e:
            os.remove(file_path)
            return jsonify({'error': f'Error storing file: {str(e)}'}), 500
    else:
        return jsonify({'error': 'File type not allowed!'}), 400
 
@app.route('/files', methods=['GET'])
def get_files():
    """Retrieve files metadata from MongoDB and return as JSON."""
    try:
        metadata = list(collection.find({}, {'document': 1, 'version': 1, 'date': 1, 'status': 1}))
        for data in metadata:
            data['_id'] = str(data['_id'])
        return jsonify(metadata), 200
    except Exception as e:
        return jsonify({'error': f'Internal Server Error: {str(e)}'}), 500
 
@app.route('/ingest/<fileName>', methods=['POST'])
def ingest_file(fileName):
    """Handle ingestion and chunking of the uploaded file."""
    try:
        run_ingest(fileName)
        return jsonify({'message': 'File ingestion and chunking started successfully!'}), 200
    except Exception as e:
        return jsonify({'error': f'Error ingesting file: {str(e)}'}), 500
 
@app.route('/ask/<genask>', methods=['POST'])
def asktype(genask):
    mainPrompt = ""
    question = request.json['question']
    if genask == "testcases":
        mainPrompt = "Act as a QA engineer, for the given the text " + "'" + question + "'" + ", generate all possible functional and non-functional test cases."
    elif genask == "testscript":
        language = request.json['language']
        mainPrompt = "Act as QA engineer, for the given test case with test steps " + "'" + question + "', generate test script in language '" + language + "'."
    semantic_search = request.json.get('semantic_search', False)
    start = timeit.default_timer()
    if semantic_search:
        semantic_search_results = query_embeddings(mainPrompt)
        answer = {'semantic_search_results' : semantic_search_results}
    else:
        qa_chain = setup_qa_chain()
        response = qa_chain({'query' : mainPrompt})
        answer = {'answer' : response['result']}
    return jsonify(answer)
 
@app.route('/ask', methods=['POST'])
def ask():
    """ Ask a question about the invoice data and return the answer """
    question = request.json['question']
    semantic_search = request.json.get('semantic_search', False)
    start = timeit.default_timer()
    if semantic_search:
        semantic_search_results = query_embeddings(question)
        answer = {'semantic_search_results' : semantic_search_results}
    else:
        qa_chain = setup_qa_chain()
        response = qa_chain({'query' : question})
        answer = {'answer' : response['result']}
    end = timeit.default_timer()
    answer['time_taken'] = end - start
    return jsonify(answer)
 
@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    """Handle file download."""
    try:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(file_path):
            response = send_file(file_path, as_attachment=True)
            response.headers['Content-Type'] = 'application/octet-stream'
            return response
        else:
            return jsonify({'error': 'File not found!'}), 404
    except Exception as e:
        return jsonify({'error': f'Error downloading file: {str(e)}'}), 500
 
if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)