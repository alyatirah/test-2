import os
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

database_url = os.environ.get("DATABASE_URL")
if database_url:
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
else:
    print("WARNING: DATABASE_URL not set, using SQLite instead")
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///recycling_game.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

class GameScore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player_name = db.Column(db.String(100), nullable=False)
    level = db.Column(db.Integer, nullable=False)
    correct_sorts = db.Column(db.Integer, nullable=False)
    incorrect_sorts = db.Column(db.Integer, nullable=False)
    score_percentage = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<GameScore {self.player_name} Level {self.level} Score {self.score_percentage}%>"

with app.app_context():
    db.create_all()

@app.route('/')
def intro():
    return render_template('intro.html')

@app.route('/play')
def play():
    top_scores = []
    if app.config["SQLALCHEMY_DATABASE_URI"]:
        try:
            top_scores = GameScore.query.order_by(GameScore.score_percentage.desc()).limit(5).all()
        except Exception as e:
            print(f"Error querying database: {e}")
    return render_template('index.html', top_scores=top_scores)

@app.route('/save-score', methods=['POST'])
def save_score():
    data = request.json
    if not data:
        return jsonify({"success": False, "error": "No data provided"}), 400

    try:
        player_name = str(data.get('player_name', 'Pemain')).strip()[:100]
        level = int(data.get('level', 1))
        correct_sorts = int(data.get('correct_sorts', 0))
        incorrect_sorts = int(data.get('incorrect_sorts', 0))
        score_percentage = int(data.get('score_percentage', 0))
        if not (0 <= score_percentage <= 100):
            raise ValueError("score_percentage mesti antara 0 dan 100")
        score = GameScore(
            player_name=player_name,
            level=level,
            correct_sorts=correct_sorts,
            incorrect_sorts=incorrect_sorts,
            score_percentage=score_percentage
        )
        db.session.add(score)
        db.session.commit()
        return jsonify({"success": True, "score_id": score.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/scores')
def scores():
    all_scores = []
    if app.config["SQLALCHEMY_DATABASE_URI"]:
        try:
            all_scores = GameScore.query.order_by(GameScore.score_percentage.desc(), 
                                                 GameScore.created_at.desc()).all()
        except Exception as e:
            print(f"Error querying database for scores page: {e}")
    return render_template('scores.html', scores=all_scores)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)