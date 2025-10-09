from flask import Flask, jsonify
from flask_cors import CORS
import json
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Разрешаем CORS для всех доменов

@app.route('/api/reviews', methods=['GET'])
def get_reviews():
    try:
        # Читаем данные из bot_data.json
        json_file_path = os.path.join(os.path.dirname(__file__), 'bot_data.json')

        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Получаем последние 7 отзывов
        reviews = data.get('reviews', [])
        latest_reviews = reviews[-7:] if len(reviews) > 7 else reviews

        # Сортируем по дате (самые новые первыми)
        sorted_reviews = sorted(latest_reviews,
                              key=lambda x: datetime.strptime(x['date'], "%d.%m.%Y"),
                              reverse=True)

        return jsonify({
            'success': True,
            'reviews': sorted_reviews,
            'total': len(sorted_reviews)
        })

    except FileNotFoundError:
        return jsonify({
            'success': False,
            'error': 'Файл bot_data.json не найден'
        }), 404
    except json.JSONDecodeError:
        return jsonify({
            'success': False,
            'error': 'Ошибка чтения JSON файла'
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/reviews/latest', methods=['GET'])
def get_latest_review():
    try:
        json_file_path = os.path.join(os.path.dirname(__file__), 'bot_data.json')

        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        reviews = data.get('reviews', [])
        if not reviews:
            return jsonify({
                'success': True,
                'review': None
            })

        # Последний отзыв (самый новый)
        latest_review = max(reviews,
                          key=lambda x: datetime.strptime(x['date'], "%d.%m.%Y"))

        return jsonify({
            'success': True,
            'review': latest_review
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)