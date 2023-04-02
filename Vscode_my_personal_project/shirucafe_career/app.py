from flask import Flask, render_template, request, redirect

app = Flask(__name__)

@app.route('/', methods=["GET"])
def index():
    return render_template("home.html")

@app.route('/post', methods=["GET", "POST"])
def post():
    if request.method == "GET":
        return render_template("post.html")
    else:
        return redirect("/answer")
    
@app.route('/answer', methods=["GET"])
def answer():
    return render_template("answer.html")

if __name__ == '__main__':
    app.run(debug=True)
