
from openai import OpenAI
from openpyxl import Workbook
import pandas as pd
import time
import os
import shutil
from docx import Document
import pypandoc

client = OpenAI(api_key='')
assistant_id = ''
###################################################### Начало основного кода #################################################################

def convert_to_txt(file_path):
    if not os.path.exists(file_path):
        return "Файл не найден. Пожалуйста, укажите корректный путь к файлу."
    
    try:
        file_extension = file_path.split('.')[-1].lower()
        if file_extension == 'xlsx':
            df = pd.read_excel(file_path)
            txt_file_path = file_path.replace(f".{file_extension}", ".txt")
            df.to_csv(txt_file_path, index=False, header=True)
            print(txt_file_path)
            return txt_file_path
        elif file_extension == 'csv':
            df = pd.read_csv(file_path, encoding='cp1251', delimiter=';', on_bad_lines='skip')
            txt_file_path = file_path.replace(f".{file_extension}", ".txt")
            df.to_csv(txt_file_path, index=False, header=True)
            print(txt_file_path)
            return txt_file_path
        elif file_extension == 'pdf':
            # Если формат PDF, просто возвращаем оригинальный путь без конверсии
            return file_path
        elif file_extension == 'docx':
            # Обработка файлов формата docx
            txt_file_path = file_path.replace(f".{file_extension}", ".txt")
            doc = Document(file_path)
            with open(txt_file_path, 'w', encoding='utf-8') as txt_file:
                for para in doc.paragraphs:
                    txt_file.write(para.text + '\n')
            return txt_file_path
            
        elif file_extension == 'doc':
            # Обработка файлов формата doc с помощью pypandoc
            txt_file_path = file_path.replace(f".{file_extension}", ".txt")
            output = pypandoc.convert_file(file_path, 'plain', outputfile=txt_file_path)
            return txt_file_path
        else:
            return file_path

    except Exception as e:
        return f"Error converting file: {e}"

def file_convert(file_path):
    try:
        # Конвертация файла в формат .txt
        txt_file_path = convert_to_txt(file_path)

        # Проверка размера файла (в килобайтах)
        file_size_txt= os.path.getsize(txt_file_path) / 1024  # Перевод размера в килобайты
        print(file_size_txt)
        file_size_kb = os.path.getsize(file_path) / 1024  # Перевод размера в килобайты
        print(file_size_kb)
        max_size_kb = 5000 # Максимальный допустимый размер файла в килобайтах (3 мегабайта)

        if file_size_kb > max_size_kb:
            print("Размер файла превышает максимально допустимый размер.")
            return None
            
        else:
            print(f"Файл успешно сконвертирован в формат .txt: {txt_file_path}")
            return txt_file_path
    except FileNotFoundError:
        print("Файл не найден. Пожалуйста, укажите корректный путь к файлу.")
        return None
        
# Функция для загрузки файла
def file_upload(txt_file_path):
    try:
        # Открываем файл в бинарном режиме и загружаем его в ассистента
        with open(txt_file_path, "rb") as file:
            response = client.files.create(
                file=file,
                purpose="assistants"  # Указываем цель
            )
        file_id = response.id
        print(f"Файл успешно загружен с ID: {file_id}")
        print(response)
        return file_id
    except FileNotFoundError:
        print("Файл не найден. Пожалуйста, укажите корректный путь к файлу.")

def create_vectore_store(file_id):
    vector_store = client.beta.vector_stores.create(
    name="TextInsightsStore"
    )
    vector_id = vector_store.id
    print(vector_id)
    vector_store_file = client.beta.vector_stores.files.create(
    vector_store_id=vector_id,
    file_id=file_id
    )
    print(vector_store_file)
    return vector_id


def delete_file(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)
        print("Файл успешно удален")
    else:
        print("Файл не существует")


def update_assistant_vector(assistant_id, vector_id):
    assistant = client.beta.assistants.update(
    assistant_id=assistant_id,
    tool_resources={"file_search": {"vector_store_ids": [vector_id]}},
    )        

def vector_store_deletion(vector_id):
    deleted_vector_store = client.beta.vector_stores.delete(
    vector_store_id=vector_id
    )
    print(deleted_vector_store)

#############################################################################################################################################
#############################################################################################################################################

# Вызов функции для создания сообщения в треде
def update_thread_message(thread_id, user_input):
    # Например:
    thread_message = client.beta.threads.messages.create(
                                thread_id,
                                role="user",
                                content=user_input,
                                                                                )
    print("Сообщение успешно отправлено в поток:", thread_message)


def check_thread_status(thread_id, run_id_PEREMEN):
    while True:
        # Получение информации о текущем запуске треда
        run = client.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run_id_PEREMEN
                                                )
        thread_status = run.status
        print("Статус треда:", thread_status)
        
        if thread_status == 'completed':
            return run  # Возвращаем объект run, когда статус станет "completed"
        time.sleep(0.1)  # Ждем 0.33 секунд перед следующей проверкой 
        if thread_status == 'failed':
            break

                 
# Вызов функции обновления tred с message
def start_thread_run(thread_id, assistant_id):
    # Например:
    run = client.beta.threads.runs.create(
                                thread_id=thread_id,
                                assistant_id=assistant_id)
    #print("Тред успешно запущен:", run)
    run_id_PEREMEN = run.id
    thread_id = run.thread_id
    thread_status = run.status
    print("Статус обработки треда:", thread_status)
    return run_id_PEREMEN

# Вызов функции для того, чтобы доставать последний message
def process_thread_messages(thread_id):
    # Достаем ответы из треда
    thread_messages = client.beta.threads.messages.list(thread_id=thread_id)

    # После записи в эксель, можно удалить тред
    for answer in thread_messages.data:
        print("Полученный ответ:" + answer.content[0].text.value + "\n")
        answer = answer.content[0].text.value
        # delete = client.beta.threads.delete(thread_id)            # Возможно удалять будем в другом месте и вообще по-другому
        break
    return answer

def two_thread_message_deletion(thread_id):
    try:
        # Retrieve a list of all messages in the thread
        thread_messages_response = client.beta.threads.messages.list(thread_id)

        # Check if there are at least two messages in the thread
        if len(thread_messages_response.data) >= 2:
            # Extract the IDs of the last two messages
            thread_messages = list(thread_messages_response)
            last_message_id = thread_messages[-2].id
            second_last_message_id = thread_messages[-3].id
            
            last_message_content = thread_messages[-2].content
            second_last_message_content = thread_messages[-3].content
           # third_last_message_content = thread_messages[-3].content
           # forth_last_message_content = thread_messages[-4].content
            # Delete the last message
            deleted_last_message = client.beta.threads.messages.delete(
                message_id=last_message_id,
                thread_id=thread_id,
            )
            print(f"Deleted last message with ID {last_message_id}")
            print("Last message content:", last_message_content)

            # Delete the second-to-last message
            deleted_second_last_message = client.beta.threads.messages.delete(
                message_id=second_last_message_id,
                thread_id=thread_id,
            )
            print(f"Deleted second-to-last message with ID {second_last_message_id}")
            print("Second last message content:", second_last_message_content)
            #print("Third last message content:", third_last_message_content)
            #print("Fourth last message content:", forth_last_message_content)
        else:
            print("Not enough messages in the thread to delete.")
    except Exception as e:
        print(f"Error deleting messages: {e}")

#############################################################################################################################################




def analyze(category, file, step, user_promt):

    start_promt = 'Представь, что ты аналитик в рекламном агентстве. Я передаю тебе файл в формате .txt, который ты должен проанализировать. В файле содержатся комментарии пользователей социальных сетей по отношениюк брендам, относящимся к категории: '
    start_promt = start_promt + category + ". В своем ответе ни в коем случае не используй ссылки на цитаты и не указывай источники, а добавляй цитаты полностью."
    print(file)

    # Проверяем и создаем каталог uploads, если его нет
    upload_dir = "uploads"

    file_path = None
    if os.path.exists(upload_dir):
        shutil.rmtree(upload_dir)
    os.makedirs(upload_dir)
    if file:
        save_path = os.path.join(upload_dir, file.filename)
        file.save(save_path)
        file_path = save_path
    if not file_path:
        print("Файл не был загружен")
        return None
    txt_file_path = file_convert(file_path)
    print(txt_file_path)
    file_content = file_upload(txt_file_path)
    print(file_content)
    
    #vector_id = create_vectore_store(file_content)
    #time.sleep(15)
    #print(vector_id)

    #delete_file(txt_file_path)  
    #print("Удаленный файл:", txt_file_path)

    #update_assistant_vector(assistant_id, file_content)
    #time.sleep(15)
    print(step)
    
    step_promt = 'Бренд твоего заказчика:' + step + ', проанализируй файл в контексте того, что ты знаешь кто заказчик.'
    end_promt = step_promt + user_promt

    empty_thread = client.beta.threads.create()
    thread_id = empty_thread.id
    print("Параметры запущенного треда:", thread_id)

    thread_message = client.beta.threads.messages.create(
        thread_id,
        role="user",
        content=start_promt,
        attachments=[{"file_id": file_content, "tools": [{"type": "file_search"}]}]
    )
    update_thread_message(thread_id, end_promt)
    print(thread_message)

    run_id_PEREMEN = start_thread_run(thread_id, assistant_id)
    print(f"ID запуска возвращенный из функции: {run_id_PEREMEN}")

    run = check_thread_status(thread_id, run_id_PEREMEN)
    print(f"Финальный статус обработки треда: {run.status}")

    assistant_message = process_thread_messages(thread_id)

    #vector_store_deletion(vector_id)
    
    return assistant_message

