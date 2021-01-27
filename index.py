from ViolasWebservice import app

@app.route("/")
def index():
    return "this is index"