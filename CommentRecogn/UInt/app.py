from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory, abort, send_file, current_app
import os
import json
from comment_recognition import text_analyzer  # Убедитесь, что comment_recognition.py находится в правильной директории

# Указание директории шаблонов при создании экземпляра Flask
app = Flask(__name__, template_folder='templates')
app.secret_key = os.urandom(24)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        category = request.form.get('category')
        selected_option = request.form.get('options')
        other_option = request.form.get('other_option') if selected_option == 'other' else None
        steps = request.form.getlist('steps[]')
        files = request.files.getlist('files[]')

        steps = [step for step in steps if step]
        files = [file for file in files if file.filename]
        
        # Вызов функции для анализа текста
        results = text_analyzer(category, selected_option, other_option, steps, files)

        # Сохранение имен файлов в сессии
        with app.app_context():
            session['results_filename'] = results.get('results_filename')
            session['final_filename'] = results.get('final_filename')
            #print(f"SESSION['results_filename']: {session['results_filename']}")
            #print(f"SESSION['final_filename']: {session['final_filename']}")
        return redirect(url_for('result'))

    return render_template('index.html')

@app.route('/result', methods=['GET'])
def result():
    results_filename = session.get('results_filename')
    
    if not results_filename:
        return "No results found", 404
    
    results_filepath = os.path.join(current_app.root_path, 'output', results_filename)
    if not os.path.exists(results_filepath):
        return "No results found", 404
    
    with open(results_filepath, 'r', encoding='utf-8') as f:
        results = json.load(f)
    
    final_filename = session.get('final_filename')
    
    return render_template('result.html', results=results, final_filename=final_filename)

@app.route('/download/<path:filename>', methods=['GET'])
def download_file(filename):
    directory = os.path.join(app.root_path, 'output')
    file_path = os.path.join(directory, filename)
    
    if not os.path.exists(file_path):
        return abort(404)
    
    return send_file(file_path, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)