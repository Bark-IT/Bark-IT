import json
from time import time
import cryptocode
from flask import (
    Flask,
    abort,
    redirect,
    render_template,
    request,
    send_file,
    send_from_directory,
    url_for,
)
from werkzeug.datastructures import ImmutableMultiDict
from flask import session
from random import randrange
from Levenshtein import distance

global post

post = open("templates/post.html", "r").read()
app = Flask(__name__)
app.secret_key = b"secretkey"


def loadjson():
    return open("json/posts.json", "r").read()


def filter(var):
    """Sanitizes user input"""
    return (
        var.replace("\\", "&#92;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .strip()
    )


def genposts(page):
    output = ""
    posts = loadjson()
    for a in range(3):
        pcount = len(posts) - a - int(page)
        if posts.get(f"{pcount}") == None:
            continue
        output += (
            post.replace(
                "^user^", str(posts[f"{pcount}"].get("author", "Unknown User"))
            )
            .replace("^title^", str(posts[f"{pcount}"].get("title", "Unknown Title")))
            .replace(
                "^content^", str(posts[f"{pcount}"].get("content", ""))
            )
            .replace("{PostID}", str(pcount))
        )

    return output


def genpost(id):
    postload = json.loads(open("json/posts.json", "r").read()).get(id, {})
    return (
        post.replace("^user^", postload.get("author", "Unknown User"))
        .replace("^title^", postload.get("title", "Unknown Title"))
        .replace("^content^", postload.get("content", ""))
        .replace("^right^", f"/posts/{id-1}")
        .replace("^left^", f"/posts/{id-1}")
    )


def getData(file):
    """Gets the json data from {file}"""
    return json.loads(open(file, "r").read())


def checkban(user):
    userread = json.loads(open("json/users.json", "r").read())
    if userread[user].get("banned") == "True":
        return True
    else:
        return False

def renderindex(page,title,session):
    index = open("templates/index.html","r").read()
    user = session.get("name", "Login")
    return index.replace("^posts^",page).replace("^profile^",user).replace("^title^","Bark-IT - "+title)

@app.route("/")
def main(name=None):
    global processing_time
    global posts
    start = time()
    posts = open("templates/genposts.html", "r").read()
    end = time()
    processing_time = end - start
    return renderindex(posts,"Home",session)



@app.route("/images/<path:filename>")
def images(filename):

    if filename == "bark-it.png":
        chance = randrange(1, 1000)
        print(chance)
        if chance == 69:
            return send_from_directory("images", "meow-it.png", as_attachment=True)
    if filename == "bark-it-small.png":
        chance = randrange(1, 1000)
        if chance == 69:
            return send_from_directory(
                "images", "meow-it-small.png", as_attachment=True
            )
    try:
        return send_from_directory("images", filename, as_attachment=True)
    except FileNotFoundError:
        abort(404)


@app.route("/about")
def about():
    return renderindex(open("templates/about.html").read(),"About",session)


# API
@app.route("/postget/<id>/")
def postget(id):
    return json.loads(loadjson()).get(id, "nill")


@app.route("/postcount")
def postcount():
    return str(len(json.loads(loadjson())))


# @app.route("/comments/<id>/")
# def comments(id):
#    return render_template("index.html", posts=genpost(id))


@app.route("/sendpost/", methods=["GET", "POST", "DELETE"])
def user():
    if request.method == "GET":
        sessname = session.get("name")
        if sessname:
            if checkban(sessname):
                return "you are banned"
        else:
            return renderindex("not logged in","Post",session)

        title = request.args.get("title")
        content = request.args.get("post")

        if title == None:
            form = """
<div class=posts>
    <center>
    <form action="/sendpost">
        <label for="id1">Title </label>
        <br>
        <input class=input type="text" id="id1" name="title" required>
        <br>
        <label for="id2">Content  </label>
        <br>
        <textarea class=input style="resize: vertical;" rows=10 maxlength="6000" id="id2" name="post" required></textarea>
        <br>
        <input class=styledbutton style="width: 30%; height: 50%;" type="submit" value="Submit">
    </form>
    </center>
</div>"""
            name = session["name"]
            if name == None:
                name = "Login"
                return renderindex("not logged in","Post",session)
            return renderindex(form,"Post",session)          
        if len(content) > 6000 or len(title) > 6000:
            return "post size is too big"

        #token = "0"
        posts = getData("json/posts.json")
        newPostId = max(map(int, posts.keys())) + 1
        postfile = open("json/posts.json", "w")
        posts.update(
            {
                newPostId: {
                    "title": title,
                    "author": sessname,
                    "content": content,
                    "likes": 1,
                    "locked": False,
                    "comments": {},
                }
            }
        )
        postfile.write(json.dumps(posts, indent=2))
        print(f"Name: {sessname}, Title: '{title}'\nContent: {content}")
        return '<meta http-equiv="Refresh" content="0; url=/sendpost" />'

    else:
        return f"{request.method} requests don't work on this url"


@app.route("/login/")
def login():
    form = """
    <div class=posts>
        <form action="/login">
            <label for="id1">Username </label>
            <input class=input type="text" id="id1" name="name">
            <br>
            <label for="id2">Password  </label>
            <input class=input type="password" id="id2" name="pass">
            <br>
            <input type="submit" value="Submit">
        </form>
    </div>"""
    userread = json.loads(open("json/users.json", "r").read())
    name = request.args.get("name")
    password = request.args.get("pass")
    
    if name == None or password == None:
        return renderindex(form,"Register",session)
    else:
        if checkban(name):
            return "you are banned"
        decrypt = cryptocode.decrypt(userread[name]["password"], password)
        # if decrypt == False:
        # return  open("templates/index.html","r").read().replace("^profile^",sessname).replace("^posts^","<center><p>incorrect username or password</p></center> "+form)
        if decrypt == password:
            session["name"] = name
        else:
            return renderindex("<center><p>incorrect username or password</p></center> "+ form,"Register",session)
        return '<meta http-equiv="Refresh" content="0; url=/" />'
    


@app.route("/register/")
def register():

    sessname = session.get("name", "Login")
    form = """
    <div class=posts>
        <form action="/register">
            <label for="id1">Username </label>
            <input class=input type="text" id="id1" name="name">
            <br>
            <label for="id2">Password  </label>
            <input class=input type="password" id="id2" name="pass">
            <br>
            <input type="submit" value="Submit">
        </form>
    </div>"""

    userread = json.loads(open("json/users.json", "r").read())
    name = request.args.get("name")
    password = request.args.get("pass")

    if name == None or password == None:
        return renderindex(form,"Register",session)
    for item in userread:
        if name == item:
            return renderindex("<p>Name already taken</p> ","Register",session)
    password = cryptocode.encrypt(password, password)
    userwrite = open("json/users.json", "w")
    userread.update({name: {"password": password, "banned": "False"}})
    userwrite.write(json.dumps(userread, indent=2))
    return renderindex(form,"Register",session)


@app.route("/settings/")
def settings():
    sessname = session.get("name", "Login")
    if sessname == "admin":
        return renderindex(open("templates/settingsadmin.html", "r").read(),"Admin Settings",session)
    return renderindex(open("templates/settings.html", "r").read(),"Settings",session)

    


@app.route("/chngsetting/<setting>")
def chngsettings(setting):
    sessname = session.get("name", "Please log in")
    match setting:
        case "changepass":
            password = request.args.get("oldpass")
            newpass = request.args.get("newpass")
            newpass2 = request.args.get("newpass2")
            if not newpass == newpass2:
                return '<meta http-equiv="Refresh" content="2; url=/settings"/><p>new passwords do not match</p>'
            userread = json.loads(open("json/users.json", "r").read())
            if not len(newpass) >= 1:
                return "put in a new password"

            if cryptocode.decrypt(userread[sessname]["password"], password) == password:
                userread[sessname]["password"] = cryptocode.encrypt(newpass, newpass)
                usersave = open("json/users.json", "w").write(
                    json.dumps(userread, indent=2)
                )
                return '<meta http-equiv="Refresh" content="0; url=/" />'
            else:
                return "wrong password"

        case "adminban":
            if not sessname == "admin":
                return "you are not an admin"
            user = request.args.get("user", "no user")
            userread = json.loads(open("json/users.json", "r").read())
            if userread.get(user):
                userread[user]["banned"] = "True"
            else:
                return "unknown user"
            usersave = open("json/users.json", "w").write(
                json.dumps(userread, indent=2)
            )
            return "banned"

        case "adminunban":
            if not sessname == "admin":
                return "you are not an admin"
            user = request.args.get("user", "no user")
            userread = json.loads(open("json/users.json", "r").read())
            userread[user]["banned"] = "False"
            usersave = open("json/users.json", "w").write(
                json.dumps(userread, indent=2)
            )
            return "unbanned"
@app.route("/search/")
def searchpage():
    sessname = session.get("name", "Login")
    object = request.args.get("object")
    searched = request.args.get("search")
    index = open("templates/index.html", "r").read()
    if not searched == None and not object == None:
        match object:
            case "channel":
                channellist = []
                channels = json.loads(open("json/catagories.json", "r").read())
                for i in range(len(channels)):
                    if distance(searched, channels[str(i)]["name"]) < 4:
                        channellist.append(channels[str(i)]["name"])
                return channellist
            case "posts":
                postslist = []
                postsrender = ""
                postspage = open("templates/post.html","r").read()
                posts = json.loads(open("json/posts.json", "r").read())
                for i in range(len(posts)):
                    if distance(searched, posts[str(i)]["title"]) < 4 or searched in posts[str(i)]["title"]:
                        postslist.append(posts[str(i)])
                        postsrender += postspage.replace("^user^",posts[str(i)]["author"]).replace("^title^",posts[str(i)]["title"]).replace("^content^",posts[str(i)]["content"])
                return renderindex(postsrender,searched,session)
    else:
        return renderindex(open("templates/search.html", "r").read(),"Search",session)
       
    


if __name__ == "__main__":
    app.run("0.0.0.0", 8080)
