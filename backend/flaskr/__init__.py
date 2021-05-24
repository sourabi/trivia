import random

from flask import Flask, request, abort, jsonify
from flask_cors import CORS
from models import setup_db, Question, Category
from werkzeug.exceptions import HTTPException

QUESTIONS_PER_PAGE = 10

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)
    cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,true')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response

    '''Handles the received exception which is If a HTTPException occurs will throw the same if 
    some other exception is received 500 will be thrown. '''
    def handle_exception(e):
        if isinstance(e, HTTPException):
            abort(e.code)
        else:
            abort(500)

    '''Formats the categories - a list of categories objects are converted into a dictionary of categories with 
    category id as key and category type as value. '''
    def format_categories(categories):
        return {category.id: category.type for category in categories}

    '''Paginate questions - receives a list of question objects and returns a subset of the given list which should 
    be in a page. '''
    def paginate_questions(question_request, questions):
        page = question_request.args.get('page', 1, type=int)
        start = (page - 1) * QUESTIONS_PER_PAGE
        end = start + QUESTIONS_PER_PAGE

        questions = [question.format() for question in questions]
        current_questions = questions[start:end]

        return current_questions

    '''A GET endpoint which returns all categories as an object in a specific format and success value. '''
    @app.route('/categories')
    def retrieve_categories():
        try:
            categories = Category.query.order_by(Category.id).all()

            if len(categories) == 0:
                abort(404)

            return jsonify({
                "success": True,
                'categories': format_categories(categories)
            })
        except Exception as e:
            handle_exception(e)

    '''A GET endpoint which returns a list of questions, success value, total number of questions, all categories and 
    current category. Also results are paginated in groups of 10. Include a request argument to choose page number, 
    starting from 1. '''
    @app.route('/questions')
    def retrieve_questions():
        try:
            questions = Question.query.order_by(Question.id).all()

            current_questions = paginate_questions(request, questions)

            if len(current_questions) == 0:
                abort(404)

            categories = Category.query.order_by(Category.id).all()

            if len(categories) == 0:
                abort(404)

            return jsonify({
                "success": True,
                'questions': current_questions,
                'total_questions': len(questions),
                'categories': format_categories(categories),
                'currentCategory': categories[random.randint(0, len(categories) - 1)].type
            })
        except Exception as e:
            handle_exception(e)

    '''A DELETE endpoint to delete the question of the given ID if it exists. '''
    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def remove_question(question_id):
        try:
            question = Question.query.filter_by(id=question_id).one_or_none()

            if question is None:
                abort(404)

            Question.delete(question)

            return retrieve_questions()
        except Exception as e:
            handle_exception(e)

    '''A POST endpoint to creates a new question using the submitted question, answer, difficulty and category. Also 
    to search the list of questions which contains the submitted search term. '''
    @app.route('/questions', methods=['POST'])
    def create_question():
        body = request.get_json()

        new_question = body.get('question', None)
        new_answer = body.get('answer', None)
        new_difficulty = body.get('difficulty', None)
        new_category = body.get('category', None)
        search_term = body.get('searchTerm', None)

        try:
            if search_term:
                questions = Question.query.filter(Question.question.ilike('%{}%'.format(search_term))).all()
                current_questions = paginate_questions(request, questions)
                return jsonify({
                    "success": True,
                    'questions': current_questions,
                    'total_questions': len(questions),
                    'currentCategory': None
                })
            elif new_question is None or new_answer is None or new_question == '' or new_answer == '':
                abort(422)
            else:
                question = Question(question=new_question, answer=new_answer, difficulty=new_difficulty,
                                    category=new_category)
                question.insert()
                return retrieve_questions()
        except Exception as e:
            handle_exception(e)

    '''A GET endpoint to returns the list of questions in the specified category, success value, total number of 
    questions in that category and specified category. '''
    @app.route('/categories/<int:category_id>/questions')
    def retrieve_specific_category_questions(category_id):
        try:
            questions = Question.query.order_by(Question.id).filter_by(category=category_id).all()
            current_category = Category.query.get(category_id)

            if questions is None or current_category is None:
                abort(404)

            current_questions = paginate_questions(request, questions)

            return jsonify({
                "success": True,
                'questions': current_questions,
                'total_questions': len(questions),
                'currentCategory': current_category.type
            })
        except Exception as e:
            handle_exception(e)

    '''A POST endpoint to play a quiz based on the specified category or all categories. Questions are chosen 
    randomly and previous questions aren't repeated in that particular quiz. '''
    @app.route('/quizzes', methods=['POST'])
    def play_quiz():
        try:
            body = request.get_json()
            category_id = int(body['quiz_category']['id'])
            category = Category.query.get(category_id)
            previous_questions = body['previous_questions']
            if category is None:
                if "previous_questions" in body and len(previous_questions) > 0:
                    questions = Question.query.filter(Question.id.notin_(previous_questions)).all()
                else:
                    questions = Question.query.all()
            else:
                if "previous_questions" in body and len(previous_questions) > 0:
                    questions = Question.query.filter(Question.id.notin_(previous_questions),
                                                      Question.category == category.id).all()
                else:
                    questions = Question.query.filter(Question.category == category.id).all()
            maxlen = len(questions) - 1
            if maxlen > 0:
                question = questions[random.randint(0, maxlen)].format()
            elif maxlen == 0:
                question = questions[0].format()
            else:
                question = False
            return jsonify({
                "success": True,
                "question": question
            })
        except Exception as e:
            handle_exception(e)

    '''Error Handler methods. '''
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": 404,
            "message": "resource not found"
        }), 404

    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({
            "success": False,
            "error": 422,
            "message": "unprocessable"
        }), 422

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            "success": False,
            "error": 400,
            "message": "bad request"
        }), 400

    @app.errorhandler(405)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": 405,
            "message": "method not allowed"
        }), 405

    @app.errorhandler(500)
    def server_error(error):
        return jsonify({
            "success": False,
            "error": 500,
            "message": "internal server error"
        }), 500

    return app
