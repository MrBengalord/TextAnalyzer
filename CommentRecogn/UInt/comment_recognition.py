from analyze import analyze
from analyze_other_option import analyze_other_option
from openai import OpenAI
import time
import os
import shutil
from datetime import datetime
from flask import session, current_app
import json


client = OpenAI(api_key='sk-proj-')
assistant_id = 'asst_'

def save_results_to_file(results, filename):
    output_dir = os.path.join(current_app.root_path, 'output')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    output_filepath = os.path.join(output_dir, filename)

    with open(output_filepath, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=4)

    print(f"Результаты сохранены в файл: {output_filepath}")
    return output_filepath

def update_thread_message(thread_id, user_input):
    thread_message = client.beta.threads.messages.create(thread_id, role="user", content=user_input)
    print("Сообщение успешно отправлено в поток:", thread_message)

def check_thread_status(thread_id, run_id_PEREMEN):
    while True:
        run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id_PEREMEN)
        thread_status = run.status
        print("Статус треда:", thread_status)

        if thread_status == 'completed':
            return run

        time.sleep(1)

def start_thread_run(thread_id, assistant_id):
    run = client.beta.threads.runs.create(thread_id=thread_id, assistant_id=assistant_id)
    run_id_PEREMEN = run.id
    thread_id = run.thread_id
    thread_status = run.status
    print("Статус обработки треда:", thread_status)
    return run_id_PEREMEN

def process_thread_messages(thread_id):
    thread_messages = client.beta.threads.messages.list(thread_id=thread_id)

    for answer in thread_messages.data:
        print("Полученный ответ:" + answer.content[0].text.value + "\n")
        answer = answer.content[0].text.value
        break
    return answer

def create_output_file(aggregated_results, final_message=None):
    output_dir = os.path.join(current_app.root_path, 'output')
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)

    output_filename = f"final_output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    output_filepath = os.path.join(output_dir, output_filename)

    with open(output_filepath, 'w', encoding='utf-8') as f:
        f.write(aggregated_results)
        if final_message:
            f.write("\n-------------------------------------------------------------- НАЧАЛО ОБЩЕГО АНАЛИЗА --------------------------------------------------------------\n")
            f.write(final_message)

    #print(f"Итоговый файл создан: {output_filepath}")

    with current_app.app_context():
        session['final_filename'] = output_filename
        #print(f"Сессия: final_filename={session.get('final_filename')}")

    return output_filename

def text_analyzer_final(aggregated_results):
    print(aggregated_results)

    empty_thread = client.beta.threads.create()
    thread_id = empty_thread.id
    print("Параметры запущенного треда:", thread_id)

    y = update_thread_message(thread_id, aggregated_results)
    run_id_PEREMEN = start_thread_run(thread_id, assistant_id)
    run = check_thread_status(thread_id, run_id_PEREMEN)

    final_message = process_thread_messages(thread_id)

    return create_output_file(aggregated_results, final_message)

def text_analyzer(category, selected_option, other_option, steps, files):
    aggregated_results = ""

    results = {
        'category': category,
        'selected_option': selected_option,
        'other_option': other_option,
        'steps': steps,
        'files': [file.filename for file in files],
        'analysis': {}
    }
    
    for step, file in zip(steps, files):
        if selected_option == 'barriers':
            user_promt = 'Выяви бренд, про который идет речь в файле. Выдели барьеры - негативные характеристики продукта/сервиса, другими словами, это факторы или условия, которые могут мешать потенциальным клиентам совершить покупку. Выполняй задачу поэтапно. Твой ответ должен содержать перечисление барьеров и их описания. После анализа, предоставь краткое саммари по бренду. Формат ответа: ""Барьер1 - Описание барьера1.\r\n Барьер2- Описание барьера2.\r\n""'
            analysis_result = analyze(category, file, step, user_promt)
            results['analysis'][file.filename] = analysis_result
            aggregated_results += "\n" + "--------------------------------------------------------------" + step + "---------------------------------------------------------------" + "\n" + analysis_result  
        elif selected_option == 'drivers':
            user_promt = ' Выяви бренд, про который идет речь в файле. Выдели позитивные характеристики продукта/сервиса. Драйверы - это особенности продукта, которые стимулируют или мотивируют потенциальных клиентов совершить покупку. После анализа, предоставь краткое саммари по бренду. Формат ответа: ""НазваниеДрайвера1 - Описание драйвера1.\r\n НазваниеДрайвера2 - Описание драйвера2. \r\n ""'
            analysis_result = analyze(category, file, step, user_promt)
            results['analysis'][file.filename] = analysis_result
            aggregated_results += "\n" + "--------------------------------------------------------------" + step + "---------------------------------------------------------------" + "\n" + analysis_result 
        elif selected_option == 'barriers_drivers':
            user_promt = 'Выяви бренд, про который идет речь в файле. Выдели барьеры - негативные характеристики продукта/сервиса, другими словами, это факторы или условия, которые могут мешать потенциальным клиентам совершить покупку. Не менее 5 штук. После этого, выдели позитивные характеристики продукта/сервиса. Позитивные характеристики, это драйверы, другими словами это продуктовые особенности, которые стимулируют или мотивируют потенциальных клиентов совершить покупку. Не менее 5 штук. После анализа, предоставь краткое саммари по бренду. Формат ответа: ""Барьер1 - Описание барьера1.\r\n Барьер2- Описание барьера2.\r\n Драйвер1 - Описание драйвера1.\r\n Драйвер2 - Описание драйвера2. \r\n ""'
            analysis_result = analyze(category, file, step, user_promt)
            results['analysis'][file.filename] = analysis_result
            aggregated_results += "\n" + "--------------------------------------------------------------" + step + "---------------------------------------------------------------" + "\n" + analysis_result 
        elif selected_option == 'segmentation':
            user_promt = ' Выяви бренд, про который идет речь в файле. Проведи сегментацию аудитории. Выяви группы потребителей/покупателей продукта/сервиса, с описанием образа жизни, ситуации использования, важных характеристик продукта, на которые обращают внимание. После анализа, предоставь краткое саммари по бренду. Формат ответа: ""Аудитория1 - Описание аудитории1.\r\n Аудитория2 - Описание аудитории2. \r\n ""'
            analysis_result = analyze(category, file, step, user_promt)
            results['analysis'][file.filename] = analysis_result
            aggregated_results += "\n" + "--------------------------------------------------------------" + step + "---------------------------------------------------------------" + "\n" + analysis_result 
        elif selected_option == 'situations':
            user_promt = ' Выяви бренд, про который идет речь в файле. Найди все возможные ситуации для чего покупают и когда применяют продукт / сервис в комментариях пользователей. После анализа, предоставь краткое саммари по бренду. Формат ответа: ""Ситуация Потребления1 - Описание ситуации1.\r\n Ситуация Потребления2 - Описание ситуации2. \r\n ""'
            analysis_result = analyze(category, file, step, user_promt)
            results['analysis'][file.filename] = analysis_result
            aggregated_results += "\n" + "--------------------------------------------------------------" + step + "---------------------------------------------------------------" + "\n" + analysis_result 
        elif selected_option == 'factors':
            user_promt = ' Выяви бренд, про который идет речь в файле. Выдели факторы, которые могут потенциально повлиять на принятие решения или выбора. Важно, что факторы не окрашены в негативный или позитивный контекст. Выяви основные точки соприкосновения пользователя и продукта: тачпоинты, реклама, советы, рекомендации, отзывы, эмоциональные факторы и другие факторы, влияющие на выбор продукта/сервиса. Выполняй задачу поэтапно. Формат ответа: ""Фактор1 - Описание фактора1.\r\n Фактор2 - Описание фактора2. \r\n "" После анализа, предоставь краткое саммари по бренду.'
            analysis_result = analyze(category, file, step, user_promt)
            results['analysis'][file.filename] = analysis_result
            aggregated_results += "\n" + "--------------------------------------------------------------" + step + "---------------------------------------------------------------" + "\n" + analysis_result 
        elif selected_option == 'topics':
            user_promt = ' Выяви бренд, про который идет речь в файле. Выдели общие тематики, которые можно Выявить из текста. Представь не меньше 10 штук, но не больше 20. Формат ответа: ""ТематикаОбсуждений1 - Описание темы1.\r\n ТематикаОбсуждений2 - Описание темы2. \r\n "" После анализа, предоставь краткое саммари по бренду.'
            analysis_result = analyze(category, file, step, user_promt)
            results['analysis'][file.filename] = analysis_result
            aggregated_results += "\n" + "--------------------------------------------------------------" + step + "---------------------------------------------------------------" + "\n" + analysis_result 
        elif selected_option == 'image_characteristics':
            user_promt = ' Выяви бренд, про который идет речь в файле. Выдели характеристики, которые описывают имидж бренда, то есть как воспринимают пользователи тот или иной бренд. Необходимо выявить именно восприятие бренда, а не продуктов,  пользователями. Нужно не меньше 10 характеристик. Формат ответа: ""ИмиджеваяХарактеристика1 - Описание характеристики1.\r\n ИмиджеваяХарактеристика2 - Описание характеристики2. \r\n "" После анализа, предоставь краткое саммари по бренду.'
            analysis_result = analyze(category, file, step, user_promt)
            results['analysis'][file.filename] = analysis_result
            aggregated_results += "\n" + "--------------------------------------------------------------" + step + "---------------------------------------------------------------" + "\n" + analysis_result 
        elif selected_option == 'product_characteristics':
            user_promt = ' Выяви бренд, про который идет речь в файле. Выдели характеристики, которые описывают продукт и его свойства. Нужно не меньше 10 характеристик. Формат ответа: ""ПродуктоваяХарактеристика1 - Описание характеристики1.\r\n ПродуктоваяХарактеристика2 - Описание характеристики2. \r\n "" После анализа, предоставь краткое саммари по бренду.'
            analysis_result = analyze(category, file, step, user_promt)
            results['analysis'][file.filename] = analysis_result
            aggregated_results += "\n" + "--------------------------------------------------------------" + step + "---------------------------------------------------------------" + "\n" + analysis_result 
        elif selected_option == 'other':
            analysis_result = analyze_other_option(category, file, step, other_option)
            results['analysis'][file.filename] = analysis_result
            aggregated_results += "\n" + "--------------------------------------------------------------" + step + "---------------------------------------------------------------" + "\n" + analysis_result 

    if len(steps) > 1:
        final_filename = text_analyzer_final(aggregated_results)
    else:
        final_filename = create_output_file(aggregated_results)

    results_filename = f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    save_results_to_file(results, results_filename)

    with current_app.app_context():
        session['results_filename'] = results_filename
        session['final_filename'] = final_filename
        #print(f"Сессия: results_filename={session.get('results_filename')}, final_filename={session.get('final_filename')}")

        
    return session