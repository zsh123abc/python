
from app import app
#from flask import jsonify, request,render_template
from views import database, keypoint,file, video,ai_review



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080,debug=True)
    